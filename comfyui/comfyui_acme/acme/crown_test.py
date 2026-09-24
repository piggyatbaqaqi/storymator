"""The painted crown as the landmark, and what geometry it supports.

The operator's position, which the measurements bear out: the fit
needs peg *centres*, the crowns stand a known height above the paper,
so locating the painted crown is enough and locating the whole peg is
not required.

This supersedes `chroma gates, greyscale measures`. That design grew a
**dark** region from the ink seed, which worked while the marking was
a thin tint over a dark mirror and stopped working when the marking
became opaque paint: the unpainted chrome shoulders are *bright*, so
the sweep halts at the paint's edge anyway. Worse, growing on
luminance merges the shadow -- on `dykem_brite_mark_blue_006` the
right peg's grown region takes in its own shadow and reads 9.57 x 5.74
mm against a 12.72 x 3.14 peg.

So the patch *is* the landmark. `acme/ink_test.py::
test_ink_on_a_corner_still_yields_the_whole_crown` asserts the
opposite and is removed by this change.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from .detect import find_peg_candidates, find_sheet
from .model import Calibration

_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", ".."))

# frame, calibration, and the peg centres located by hand
MEDIA = {
    "brite mark": ("dykem_brite_mark_blue/dykem_brite_mark_blue_006",
                   "v4k_01_blue_84001.json"),
    "steel blue": ("dykem_steel_blue/dykem_steel_blue_002",
                   "v4k_01_steel_blue.json"),
    "dry erase": ("fresh_ink/fresh_ink_007", "v4k_01.json"),
    "dry erase art": ("fresh_ink/fresh_ink_008", "v4k_01.json"),
}


def _frame(stem: str) -> np.ndarray:
    path = os.path.join(_ROOT, "data", "captures", stem + ".png")
    if not os.path.exists(path):
        pytest.skip(f"{stem} is not in the working tree")
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB"), dtype=float)


def _calibration(name: str) -> Calibration:
    path = os.path.join(_ROOT, "data", "calibration", "distortion",
                        "v4k_01", name)
    if not os.path.exists(path):
        pytest.skip(f"{name} is not in the working tree")
    with open(path) as handle:
        return Calibration.from_dict(json.load(handle))


def _crowns(medium: str):
    """The three crown patches, ordered along the bar."""
    stem, cname = MEDIA[medium]
    rgb = _frame(stem)
    cal = _calibration(cname)
    gray = (rgb @ np.array([0.2126, 0.7152, 0.0722])) / 255.0
    found = find_peg_candidates(gray, find_sheet(gray), min_area_px=200.0,
                                max_area_px=20000.0, ink=cal.ink, rgb=rgb)
    return sorted(found, key=lambda b: b.x), cal, gray, rgb


# --- 1. the patch is the landmark, not a grown region ----------------

@pytest.mark.parametrize("medium", sorted(MEDIA))
def test_the_patch_is_what_is_measured(medium: str):
    """Paint cannot be larger than the crown it is on.

    A region grown on luminance can be, and was: 9.57 mm on a 12.72 mm
    peg once its shadow joined in.
    """
    crowns, cal, _, _ = _crowns(medium)
    assert len(crowns) == 3
    from .outline import sheet_scale_px_per_mm
    _, _, gray, _ = _crowns(medium)
    scale = sheet_scale_px_per_mm(find_sheet(gray), gray, cal)
    limits = [(cal.peg.rect_long_mm, cal.peg.rect_short_mm),
              (cal.peg.round_diameter_mm, cal.peg.round_diameter_mm),
              (cal.peg.rect_long_mm, cal.peg.rect_short_mm)]
    for blob, (long_mm, short_mm) in zip(crowns, limits):
        assert blob.long_px / scale <= long_mm + 0.5
        assert blob.short_px / scale <= short_mm + 0.5


def test_the_shadow_is_not_part_of_the_crown():
    """The right peg on the Brite-Mark frame is the case in point.

    Grown on luminance its region reaches 5.74 mm across a 3.14 mm
    peg, because the shadow it touches is also darker than paper.
    Chroma does not have that problem: a shadow is paper-hued.
    """
    crowns, cal, gray, _ = _crowns("brite mark")
    from .outline import sheet_scale_px_per_mm
    scale = sheet_scale_px_per_mm(find_sheet(gray), gray, cal)
    right = crowns[2]
    assert right.short_px / scale < cal.peg.rect_short_mm + 0.5


@pytest.mark.parametrize("medium", sorted(MEDIA))
def test_the_box_is_the_ink_component_itself(medium: str):
    """Not a region grown outward from it.

    `_crown_from_seed` sweeps a luminance threshold up from the ink and
    keeps the dark component the ink sits in, which was right while the
    marking was a thin tint over a dark mirror. With opaque paint the
    two disagree -- on the Brite-Mark frame the grown box is 11.28 mm
    long where the paint is 10.16 -- and the grown part is chrome and
    shadow, which is to say error.
    """
    from scipy import ndimage
    from .ink import ink_mask
    from .rect import fit_rect
    crowns, cal, gray, rgb = _crowns(medium)
    sheet = find_sheet(gray)
    mask = ndimage.binary_closing(
        ink_mask(rgb, cal.ink, ndimage.binary_erosion(sheet, iterations=2)),
        np.ones((9, 9)))
    labels, n = ndimage.label(mask)
    sizes = ndimage.sum(mask, labels, range(1, n + 1))
    boxes = ndimage.find_objects(labels)
    patches = []
    for i in np.argsort(sizes)[::-1][:3]:
        box = boxes[i]
        patches.append(fit_rect(labels[box] == i + 1,
                                origin=(box[1].start, box[0].start)))
    patches.sort(key=lambda r: r.centre[0])
    # The claim is that nothing is grown *beyond* the ink, so the
    # tolerances only have to exclude growth. They are not tighter
    # than that on purpose: this reference closes the mask 9x9 while
    # the detector sizes its span from the smallest peg worth
    # finding, and that difference alone moves the weakest patch's
    # centroid by 2.9 px. Growth, when it happened, was 30 px and
    # more.
    for blob, patch in zip(crowns, patches):
        assert abs(blob.long_px - patch.long_px) < 5.0
        assert abs(blob.short_px - patch.short_px) < 5.0
        assert np.hypot(blob.x - patch.centre[0],
                        blob.y - patch.centre[1]) < 4.0


# --- 2. the centre is what the fit uses, so it must be stable --------

def test_the_centres_repeat_when_the_bar_has_not_moved():
    """`fresh_ink_007` and `_008` differ only by the sheet on the bar.

    Measured at 0.39, 1.78 and 0.67 px, so 3 px is loose enough to be
    about the detector and tight enough to mean something: 3 px is
    0.3 mm, and punch tolerance alone is 0.27 mm.
    """
    blank, _, _, _ = _crowns("dry erase")
    art, _, _, _ = _crowns("dry erase art")
    for a, b in zip(blank, art):
        assert np.hypot(a.x - b.x, a.y - b.y) < 3.0


# --- 3. what the patch's shape may and may not be asked ---------------

@pytest.mark.parametrize("medium", sorted(MEDIA))
def test_the_two_rect_patches_agree_on_the_bar_direction(medium: str):
    """They are on one rigid bar, so their long axes are parallel.

    This is the shape measurement the patch *can* support.
    """
    crowns, _, _, _ = _crowns(medium)
    left, right = crowns[0], crowns[2]
    delta = abs((np.degrees(left.angle_rad - right.angle_rad) + 90) % 180 - 90)
    assert delta < 8.0


@pytest.mark.parametrize("medium", sorted(MEDIA))
def test_the_round_patch_is_round_enough_to_have_no_angle(medium: str):
    """And the one it cannot.

    A near-circular blob has no meaningful long axis: across the
    corpus the round peg's fitted angle reads -90, -25, -90 and +67
    degrees on frames of the same unmoved bar. Nothing downstream may
    use it, and this records why.
    """
    crowns, _, _, _ = _crowns(medium)
    assert crowns[1].elongation < 1.8


# --- 4. the geometry the centres actually support --------------------

@pytest.mark.parametrize("medium", sorted(MEDIA))
def test_the_centres_are_collinear_once_corrected_to_the_paper(medium: str):
    """Not before. The crowns are at different heights.

    The operator's point, and the measurements bear it out: the round
    peg's painted disc stands at the dome's apex, 8.674 mm, while the
    rect crowns are flat tops at 6.404 mm. Different heights mean
    different parallax, so the three *observed* centres are not
    collinear -- only their projections onto the paper are.

    Tested in undistorted image pixels rather than in millimetres. A
    homography maps lines to lines, so collinearity needs no
    homography, and the sheet's is demonstrably imperfect: it reports
    peg spacings of 102.6 and 105.4 mm for a bar whose two halves are
    equal. Asserting collinearity through it would be measuring the
    wrong thing.

    Raw and corrected, over the corpus: 6.94-8.94 px becomes 2.32-4.85
    once the apex height is used. With the hemisphere-centre height of
    5.567 that was in the calibration first, it got *worse* -- 8.48 to
    10.24 -- which is what identified the error.
    """
    from .lens import undistort_points
    from .parallax import correct_parallax
    crowns, cal, gray, _ = _crowns(medium)
    from .detect import sheet_corners
    corners = undistort_points(sheet_corners(find_sheet(gray), gray),
                               cal.camera_matrix, cal.dist_coeffs)
    model = cal.sheet.corners()
    scale = float(np.linalg.norm(corners[2] - corners[0])
                  / np.linalg.norm(model[2] - model[0]))
    raw = undistort_points(np.array([b.centre for b in crowns]),
                           cal.camera_matrix, cal.dist_coeffs)
    corrected = correct_parallax(
        raw, [cal.peg.rect_landmark_height_mm,
              cal.peg.round_landmark_height_mm,
              cal.peg.rect_landmark_height_mm],
        cal.camera_matrix, scale)

    def off_line(points):
        axis = points[2] - points[0]
        axis = axis / np.linalg.norm(axis)
        delta = points[1] - points[0]
        return abs(axis[0] * delta[1] - axis[1] * delta[0])

    assert off_line(corrected) < 6.0
    assert off_line(corrected) < off_line(raw), (
        "correcting to the paper made the trio less collinear, which "
        "means a landmark height is wrong")


@pytest.mark.parametrize("medium", sorted(MEDIA))
def test_the_fit_reports_where_each_peg_missed(medium: str):
    """Per peg, not just an aggregate.

    The corpus shows a systematic error that an rms hides completely:
    the round-to-right spacing reads 104.05 to 105.71 mm against a
    101.62 mm bar on every frame and every medium, while
    left-to-round reads 100.08 to 102.82. One peg is consistently
    out and the operator cannot see which from a single number.
    """
    from .fit import fit_pose
    _, cal, gray, rgb = _crowns(medium)
    pose = fit_pose(gray, cal, rgb=rgb, max_residual_px=1e9)
    assert pose.peg_residuals_mm is not None
    assert len(pose.peg_residuals_mm) == 3
    assert np.isclose(float(np.sqrt(np.mean(
        np.asarray(pose.peg_residuals_mm) ** 2))),
        pose.peg_residual_px / cal.raster.px_per_mm, rtol=0.05)
