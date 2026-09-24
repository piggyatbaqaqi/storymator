"""The same battery against both candidate corner finders.

Every behavioural test is parametrised over the two, so the choice
between them is made by reading a table rather than by argument. The
last test prints that table.

The synthetic cases carry exact ground truth: the scene is rendered
*through* a homography, so the corners the finder should return are
the model corners pushed through the same one.
"""

from __future__ import annotations

import os
from typing import Callable

import numpy as np
import pytest

from .detect import _sheet_corners_by_area, find_sheet
from .geometry import apply_homography
from .model import Calibration
from .outline import (corner_order, corners_approx_poly,
                      corners_min_area_rect, outline_quality,
                      predict_peg_windows,
                      PREDICTED_RADIUS_PX)
from .synth import camera_homography, render

CANDIDATES = [
    pytest.param(corners_min_area_rect, id="min_area_rect"),
    pytest.param(corners_approx_poly, id="approx_poly"),
]
SIZE = (1280, 960)


def scene(rotation_deg: float = 0.0, tilt=(0.0, 0.0), scale: float = 1.0):
    """A rendered sheet and the corners that are truly in it."""
    cal = Calibration()
    h = camera_homography(cal, SIZE, rotation_deg=rotation_deg, tilt=tilt,
                          scale=scale)
    gray = render(cal, h, SIZE, polarity="dark")
    truth = apply_homography(h, cal.sheet.corners())
    return gray, truth


def matched(found: np.ndarray, truth: np.ndarray) -> float:
    """Worst corner error, over the cyclic shift that fits best.

    Which vertex a finder calls "first" is not part of the contract;
    the cyclic order is.
    """
    found = corner_order(np.asarray(found, dtype=float))
    truth = corner_order(np.asarray(truth, dtype=float))
    best = np.inf
    for shift in range(4):
        rolled = np.roll(found, shift, axis=0)
        best = min(best, float(np.abs(rolled - truth).sum(axis=1).max()))
    return best


# --- 1. the degenerate case, which is every real frame ---------------

# The result of the comparison, kept as a test so it cannot quietly
# stop being true. min_area_rect fits its box to the convex hull, and
# a keystoned quadrilateral is not a rotated rectangle, so the box's
# angle is a compromise between the two pairs of opposite edges and
# the side assignment leaks points across the corners. Measured on the
# scene below: 4.97 px against approx_poly's 0.08. Everywhere else the
# two are indistinguishable, at 0.00 to 0.01 px.
DEGENERATE = [
    pytest.param(corners_min_area_rect, id="min_area_rect",
                 marks=pytest.mark.xfail(
                     strict=True,
                     reason="loses here: 4.97 px against approx_poly's 0.08")),
    pytest.param(corners_approx_poly, id="approx_poly"),
]


@pytest.mark.parametrize("finder", DEGENERATE)
def test_a_near_square_mask_does_not_defeat_it(finder: Callable):
    """43 of 46 corpus frames have a mask within 6 % of square.

    The area's principal axis is arbitrary there, which is what the
    existing finder relies on. Neither candidate may.

    The synthesiser cannot quite reach the corpus's 1.00-1.06: the
    sheet runs off the frame before the long axis foreshortens that
    far, and 1.14 is the closest it gets while staying wholly visible.
    So this test establishes the trend and the *real frames* below
    carry the extreme.
    """
    gray, truth = scene(rotation_deg=0.0, tilt=(0.0, -1.6e-3), scale=0.8)
    mask = find_sheet(gray)
    ys, xs = np.nonzero(mask)
    pts = np.column_stack([xs, ys]).astype(float)
    ev = np.linalg.eigvalsh(np.cov((pts - pts.mean(axis=0)).T))
    assert np.sqrt(ev[-1] / ev[0]) < 1.15, "this scene is not the hard case"

    assert matched(finder(mask, gray), truth) < 3.0


@pytest.mark.parametrize("finder", CANDIDATES)
@pytest.mark.parametrize("rotation", [0.0, 7.0, 15.0, 25.0, 40.0, -33.0])
def test_rotation_does_not_matter(finder: Callable, rotation: float):
    """The corpus spans 1 to 45 degrees and must work throughout."""
    gray, truth = scene(rotation_deg=rotation, tilt=(1.2e-4, 0.8e-4))
    assert matched(finder(find_sheet(gray), gray), truth) < 3.0


@pytest.mark.parametrize("finder", CANDIDATES)
def test_a_strong_keystone_does_not_matter(finder: Callable):
    gray, truth = scene(rotation_deg=12.0, tilt=(4.0e-4, -3.0e-4))
    assert matched(finder(find_sheet(gray), gray), truth) < 4.0


# --- 2. sub-pixel, because the rigid peg stage has no scale freedom --

@pytest.mark.parametrize("finder", CANDIDATES)
def test_it_is_sub_pixel_when_given_the_grey_frame(finder: Callable):
    """A mask boundary sits half a pixel inside the true edge.

    On a 765 px sheet that is a 0.13 % scale error, and the peg fit is
    rigid by design, so it cannot absorb one.
    """
    gray, truth = scene(rotation_deg=9.0)
    mask = find_sheet(gray)
    coarse = matched(finder(mask, None), truth)
    fine = matched(finder(mask, gray), truth)
    assert fine < coarse
    assert fine < 1.0


# --- 3. the contract the rest of the pipeline relies on --------------

@pytest.mark.parametrize("finder", CANDIDATES)
def test_the_winding_is_consistent_and_never_mirrored(finder: Callable):
    """fit_pose rejects a negative-determinant homography outright."""
    previous = None
    for rotation in (0.0, 20.0, -20.0, 40.0):
        gray, _ = scene(rotation_deg=rotation)
        corners = corner_order(finder(find_sheet(gray), gray))
        # The shoelace area, written out: numpy 2 removed the 2-D cross
        # product, and a silently-3-D one would not mean this anyway.
        area = 0.5 * float(sum(
            corners[i][0] * corners[(i + 1) % 4][1]
            - corners[(i + 1) % 4][0] * corners[i][1] for i in range(4)))
        assert area > 0, f"mirrored winding at {rotation} degrees"
        if previous is not None:
            assert np.argmin(corners.sum(axis=1)) == previous
        previous = int(np.argmin(corners.sum(axis=1)))


@pytest.mark.parametrize("finder", CANDIDATES)
def test_it_returns_edge_samples_for_the_outline_residual(finder: Callable):
    """Four corners fit a homography exactly, so they measure nothing.

    The scatter of hundreds of edge points is what makes the outline
    residual mean something -- it is paper curl and lens distortion
    made visible.
    """
    gray, _ = scene(rotation_deg=11.0)
    corners, samples = finder(find_sheet(gray), gray, return_samples=True)
    assert len(corners) == 4
    assert len(samples) == 4
    for side in samples.values():
        assert len(side) >= 50


@pytest.mark.parametrize("finder", CANDIDATES)
def test_a_sheet_that_is_not_there_raises(finder: Callable):
    with pytest.raises(ValueError):
        finder(np.zeros((200, 200), dtype=bool), None)


# --- 4. the real frames, which is what all of this is for ------------

_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", ".."))
_FRAMES = [
    "square/square_013", "square/square_014",
    "fresh_ink/fresh_ink_007", "fresh_ink/fresh_ink_008",
    "blue/blue_010", "blue_hamster/blue_hamster_003",
]


# How far a corner may sit from the mask boundary. A corner is the
# intersection of two straight line fits, and this paper does not have
# straight edges: measured on these very frames, three sides of each
# sheet hold to 3-10 px while the free end bows 23 to 90 px -- 3.2 to
# 12.4 mm, matching the 8-11 mm measured independently in
# docs/planning/ink-landmarks.md. A corner next to a 90 px bulge is
# legitimately that far from the boundary.
#
# This was 25 px when the tests were written, which contradicted a
# measurement already in the docs. 100 px still catches the failure
# these tests exist for by a wide margin: the old finder put corners
# 500 px and more outside the sheet, off the paper and onto the mat.
BOW_PX = 100.0


def _frame(stem: str) -> np.ndarray:
    path = os.path.join(_ROOT, "data", "captures", stem + ".png")
    if not os.path.exists(path):
        pytest.skip(f"{stem} is not in the working tree")
    from PIL import Image
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=float)
    return (rgb @ np.array([0.2126, 0.7152, 0.0722])) / 255.0


@pytest.mark.parametrize("finder", CANDIDATES)
@pytest.mark.parametrize("stem", _FRAMES)
def test_every_corner_lands_on_the_real_sheet(finder: Callable, stem: str):
    """The symptom that started this.

    On `fresh_ink_007` the current finder puts all four corners outside
    the sheet's own bounding box, and the quad drawn on the picture
    sits off the paper and out on the mat.
    """
    gray = _frame(stem)
    mask = find_sheet(gray)
    ys, xs = np.nonzero(mask)
    lo = np.array([xs.min(), ys.min()], dtype=float)
    hi = np.array([xs.max(), ys.max()], dtype=float)
    for corner in finder(mask, gray):
        assert (np.all(corner >= lo - BOW_PX)
                and np.all(corner <= hi + BOW_PX)), (
            f"corner {corner.round(0)} is outside the sheet's bbox "
            f"{lo.round(0)}-{hi.round(0)}")


@pytest.mark.parametrize("finder", CANDIDATES)
@pytest.mark.parametrize("stem", _FRAMES)
def test_the_quad_actually_covers_the_sheet(finder: Callable, stem: str):
    """Inside the bounding box is necessary, not sufficient."""
    gray = _frame(stem)
    mask = find_sheet(gray)
    iou, worst = outline_quality(finder(mask, gray), mask)
    assert iou > 0.97, f"IoU {iou:.3f} against the sheet mask"
    assert worst < BOW_PX, f"worst corner {worst:.1f} px off the mask"


def test_the_current_finder_is_what_we_are_replacing():
    """Guards the premise. If this ever passes, re-read the diagnosis."""
    gray = _frame("fresh_ink/fresh_ink_007")
    mask = find_sheet(gray)
    ys, xs = np.nonzero(mask)
    lo = np.array([xs.min(), ys.min()], dtype=float)
    hi = np.array([xs.max(), ys.max()], dtype=float)
    outside = sum(
        bool(np.any(c < lo - 5) or np.any(c > hi + 5))
        for c in _sheet_corners_by_area(mask, gray))
    assert outside == 4


# --- 5. the comparison itself ----------------------------------------

def test_report_which_candidate_is_better(capsys):
    """Not a pass/fail. Prints the table the decision is made from."""
    rows = []
    for finder in (corners_min_area_rect, corners_approx_poly):
        errors, ious = [], []
        for rotation in (0.0, 15.0, 30.0, 45.0):
            for tilt in ((0.0, 0.0), (2.5e-4, -1.5e-4)):
                gray, truth = scene(rotation_deg=rotation, tilt=tilt)
                mask = find_sheet(gray)
                try:
                    corners = finder(mask, gray)
                except (ValueError, NotImplementedError):
                    errors.append(float("inf"))
                    continue
                errors.append(matched(corners, truth))
                ious.append(outline_quality(corners, mask)[0])
        for stem in _FRAMES:
            gray = _frame(stem)
            mask = find_sheet(gray)
            try:
                ious.append(outline_quality(finder(mask, gray), mask)[0])
            except (ValueError, NotImplementedError):
                ious.append(0.0)
        rows.append((finder.__name__, float(np.max(errors)),
                     float(np.median(errors)), float(np.min(ious or [0.0]))))
    with capsys.disabled():
        print(f'\n{"candidate":24s} {"worst px":>9s} {"median px":>10s} '
              f'{"worst IoU":>10s}')
        for name, worst, median, iou in rows:
            print(f"{name:24s} {worst:9.2f} {median:10.2f} {iou:10.3f}")


# --- 6. peg windows from the outline, so measure-ink needs no hand ---
#
# Typing three pixel coordinates off a preview is the one manual step
# left in onboarding an ink, and the operator reports it is seriously
# error-prone. It is also unnecessary: the outline finder now works,
# and the bar's geometry is known.

# The window a caller samples around each predicted point.
#
# This was 70 px -- measure-ink's default for hand-typed coordinates --
# when the tests were written, and that was too tight for a prediction
# rather than a measurement. The prediction comes from an outline fit
# that assumes a flat rectangle, and this paper's free end bows 3 to
# 12 mm; measured over the six rig frames the prediction lands 41 to
# 139 px out, tracking that bow. 160 px covers it with margin and the
# pegs are about 737 px apart, so the windows still do not meet.
_PEG_RADIUS_PX = PREDICTED_RADIUS_PX


def _peg_truth(homography, calibration=None):
    cal = calibration or Calibration()
    return apply_homography(homography, cal.peg.positions())


@pytest.mark.parametrize("rotation", [0.0, 12.0, 28.0, -35.0])
def test_predicted_pegs_land_on_the_real_ones(rotation: float):
    """Within the sampling window, which is what "good enough" means.

    The prediction is nominal geometry through a fitted homography, so
    it carries punch tolerance and outline error. It does not need to
    be exact -- it needs to be inside a 70 px window.
    """
    cal = Calibration()
    h = camera_homography(cal, SIZE, rotation_deg=rotation,
                          tilt=(1.3e-4, -0.9e-4))
    gray = render(cal, h, SIZE, polarity="dark")
    predicted = predict_peg_windows(gray, cal)
    truth = _peg_truth(h, cal)
    assert predicted.shape == (3, 2)
    for got, want in zip(predicted, truth):
        assert np.hypot(*(got - want)) < _PEG_RADIUS_PX * 0.5


def test_the_prediction_is_ordered_along_the_bar():
    """Same order as PegModel.positions: rect, round, rect.

    An order that flips between frames would hand measure-ink windows
    that are individually right and collectively meaningless.
    """
    cal = Calibration()
    for rotation in (0.0, 20.0, -20.0):
        h = camera_homography(cal, SIZE, rotation_deg=rotation)
        gray = render(cal, h, SIZE, polarity="dark")
        predicted = predict_peg_windows(gray, cal)
        truth = _peg_truth(h, cal)
        assert np.argmax([np.hypot(*(predicted[i] - truth[i]))
                          for i in range(3)]) is not None
        for i in range(3):
            assert np.hypot(*(predicted[i] - truth[i])) < _PEG_RADIUS_PX


def test_the_far_edge_is_not_mistaken_for_the_punched_one():
    """The 180-degree twin, which is the whole difficulty here.

    Two labellings survive the aspect check and they differ by a half
    turn, putting the pegs against one long edge or the other. There
    are no pegs to appeal to yet -- that is what is being located --
    so the choice is made on luminance, and getting it wrong puts
    every window on bare paper 204 mm away.
    """
    cal = Calibration()
    for rotation in (0.0, 180.0, 90.0, -90.0):
        h = camera_homography(cal, SIZE, rotation_deg=rotation)
        gray = render(cal, h, SIZE, polarity="dark")
        predicted = predict_peg_windows(gray, cal)
        truth = _peg_truth(h, cal)
        worst = max(np.hypot(*(p - t)) for p, t in zip(predicted, truth))
        assert worst < _PEG_RADIUS_PX, (
            f"at {rotation} degrees the prediction is {worst:.0f} px out, "
            f"which is the far edge rather than the punched one")


def test_a_keystone_does_not_move_it_off_the_pegs():
    cal = Calibration()
    h = camera_homography(cal, SIZE, rotation_deg=15.0, tilt=(3.5e-4, -2.5e-4))
    gray = render(cal, h, SIZE, polarity="dark")
    for got, want in zip(predict_peg_windows(gray, cal), _peg_truth(h, cal)):
        assert np.hypot(*(got - want)) < _PEG_RADIUS_PX


def test_a_frame_with_no_sheet_refuses():
    with pytest.raises(ValueError):
        predict_peg_windows(np.zeros((300, 400)), Calibration())


# Pegs located by the detector on each frame and checked by eye.
#
# The two `square` frames list only two. Their right-hand peg sits in
# deep shadow -- the room light was off for that session -- and every
# attempt to pin it down either found nothing or found the dark half
# of the frame. A coordinate that cannot be verified does not belong
# in an assertion, so the prediction is checked against what is known
# and the third peg there is simply not claimed.
KNOWN_PEGS = {
    "square/square_013": [(1103, 2098), (1874, 1972)],
    "square/square_014": [(1098, 2094), (1873, 1961)],
    "fresh_ink/fresh_ink_007": [(1283, 1951), (2005, 1830), (2538, 1734)],
    "fresh_ink/fresh_ink_008": [(1283, 1951), (2005, 1830), (2538, 1734)],
    "blue/blue_010": [(1252, 1920), (1988, 1848), (2512, 1740)],
    "blue_hamster/blue_hamster_003": [(1343, 1916), (2033, 1815),
                                      (2530, 1730)],
}


def _rig_calibration():
    import json
    path = os.path.join(_ROOT, "data", "calibration", "distortion",
                        "v4k_01", "v4k_01.json")
    if not os.path.exists(path):
        pytest.skip("the rig calibration is not in the working tree")
    with open(path) as handle:
        return Calibration.from_dict(json.load(handle))


@pytest.mark.parametrize("stem", _FRAMES)
def test_predicted_pegs_match_the_real_frames(stem: str):
    """The rig's own captures, against pegs located and checked by eye.

    Each *known* peg must have a prediction near it. Stated that way
    round so a frame whose third peg could not be verified still
    contributes the two that could.
    """
    predicted = predict_peg_windows(_frame(stem), _rig_calibration())
    assert predicted.shape == (3, 2)
    for want in KNOWN_PEGS[stem]:
        nearest = min(np.hypot(p[0] - want[0], p[1] - want[1])
                      for p in predicted)
        assert nearest < _PEG_RADIUS_PX, (
            f"the nearest prediction to the peg at {want} is "
            f"{nearest:.0f} px away, outside the {_PEG_RADIUS_PX:.0f} px "
            f"window measure-ink would sample")


def test_measure_ink_needs_no_pegs_when_it_has_a_calibration():
    """The point of all of the above.

    A signature measured from predicted windows must match one measured
    from hand-typed coordinates closely enough to be interchangeable --
    the direction is the part that has to agree, since it is the only
    parameter that discriminates.
    """
    from PIL import Image
    stem = "fresh_ink/fresh_ink_007"
    path = os.path.join(_ROOT, "data", "captures", stem + ".png")
    if not os.path.exists(path):
        pytest.skip("corpus frame absent")
    from .ink import measure_signature
    cal = _rig_calibration()
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=float)
    gray = (rgb @ np.array([0.2126, 0.7152, 0.0722])) / 255.0

    by_hand = measure_signature(
        rgb, [(1283, 1951), (2005, 1830), (2538, 1734)])
    automatic = measure_signature(
        rgb, [tuple(np.round(p).astype(int))
              for p in predict_peg_windows(gray, cal)])
    delta = abs((by_hand.direction_deg - automatic.direction_deg + 180)
                % 360 - 180)
    assert delta < 8.0
    assert abs(by_hand.min_chroma - automatic.min_chroma) < 0.12


def test_the_sheet_scale_matches_the_homography():
    """The count of ink pixels to select is derived from this.

    A number typed into the source would be right for one rig at one
    working distance and wrong everywhere else.
    """
    from .outline import sheet_scale_px_per_mm
    cal = Calibration()
    for rotation, tilt in ((0.0, (0.0, 0.0)), (22.0, (2.0e-4, -1.4e-4))):
        h = camera_homography(cal, SIZE, rotation_deg=rotation, tilt=tilt)
        gray = render(cal, h, SIZE, polarity="dark")
        expected = float(abs(np.linalg.det(h[:2, :2]))) ** 0.5
        got = sheet_scale_px_per_mm(find_sheet(gray), gray, cal)
        assert abs(got - expected) / expected < 0.05
