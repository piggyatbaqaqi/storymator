"""Tests for :mod:`acme.ink` and the colour gate in :mod:`acme.detect`.

Scenes are built here rather than in :mod:`acme.synth`, which renders
luminance only. They are deliberately crude -- flat paper, flat ink,
flat shadow -- because what is being tested is which *colours* survive
a threshold, and a realistic render would only make the failures
harder to read.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

import numpy as np
import pytest

from .detect import find_peg_candidates, find_sheet
from .fit import fit_pose
from .ink import (balance, chroma_angle_deg, ink_mask, ink_pixel_count,
                  measure_signature,
                  relative_chroma, srgb_to_lab, white_point)
from .model import Calibration, InkSignature

# Canson cream under the rig's lighting, as the corpus measures it.
PAPER = np.array([231, 194, 165], dtype=float)
# A shadow is the paper darker, not the paper a different colour.  This
# is the confuser the luminance detector cannot reject.
SHADOW = PAPER * 0.45
BLUE_INK = np.array([26, 30, 58], dtype=float)
RED_INK = np.array([70, 24, 26], dtype=float)

PEGS = ((90, 150), (200, 150), (310, 150))
SIZE = (300, 400)          # rows, cols


def scene(ink_rgb: Optional[np.ndarray] = BLUE_INK,
          dim_peg: Optional[int] = None,
          gain: Tuple[float, float, float] = (1.0, 1.0, 1.0),
          ink_corner_only: bool = False) -> np.ndarray:
    """Paper, three chrome pegs with shadows, optionally inked.

    ``gain`` multiplies the channels, which is what a white-balance
    change does.  ``dim_peg`` darkens one peg the way a crown reflecting
    something duller does.  ``ink_corner_only`` puts the ink on a
    corner of the crown instead of over it, which is what the pen
    actually does.
    """
    img = np.zeros(SIZE + (3,), dtype=float)
    img[:, :] = PAPER
    for n, (cx, cy) in enumerate(PEGS):
        # the shadow, cast up and to the left of every peg alike
        img[cy - 34:cy - 8, cx - 30:cx + 30] = SHADOW
        # the crown: dark chrome, the thing fit_rect has to measure
        crown = (slice(cy - 10, cy + 10), slice(cx - 26, cx + 26))
        img[crown] = PAPER * 0.22
        if ink_rgb is not None:
            if ink_corner_only:
                img[cy - 10:cy - 2, cx - 26:cx - 12] = ink_rgb
            else:
                img[crown] = ink_rgb
        if dim_peg == n:
            img[cy - 34:cy + 10, cx - 30:cx + 30] *= 0.5
    return np.clip(img * np.asarray(gain), 0, 255)


def luminance(rgb: np.ndarray) -> np.ndarray:
    return (rgb @ np.array([0.2126, 0.7152, 0.0722])) / 255.0


def sheet_mask() -> np.ndarray:
    mask = np.zeros(SIZE, dtype=bool)
    mask[10:-10, 10:-10] = True
    return mask


def candidates(img: np.ndarray, ink: Optional[InkSignature]):
    return find_peg_candidates(
        luminance(img), sheet_mask(), min_area_px=60.0, max_area_px=4000.0,
        ink=ink, rgb=img)


BLUE = InkSignature(name="test blue")


def _blue_for(img: np.ndarray) -> InkSignature:
    """The signature this scene's ink actually has."""
    return measure_signature(img, PEGS, name="test blue", radius_px=40)


# --- 1. the gate is doing the work -----------------------------------

def test_the_gate_finds_the_pegs_and_the_ink_is_why():
    img = scene()
    found = candidates(img, _blue_for(img))
    assert len(found) == 3
    xs = sorted(b.x for b in found)
    for got, (want, _) in zip(xs, PEGS):
        assert abs(got - want) < 6

    bare = scene(ink_rgb=None)
    with pytest.raises(ValueError, match="ink_not_found"):
        candidates(bare, _blue_for(img))


def test_the_shadow_is_not_a_candidate():
    """The confuser the luminance path cannot reject."""
    img = scene()
    for blob in candidates(img, _blue_for(img)):
        assert blob.y > 130, f"a candidate at y={blob.y:.0f} is the shadow"


# --- 2. a dim peg is still a peg -------------------------------------

def test_a_peg_at_half_brightness_is_still_found():
    """The claim the right peg falsifies under an absolute threshold.

    Lab's cube root makes the (a*, b*) angle nearly invariant to how
    brightly a peg renders, which is why the angle carries the colour
    and the magnitude only rejects grey.
    """
    img = scene(dim_peg=2)
    found = candidates(img, _blue_for(scene()))
    assert len(found) == 3, "the dim peg dropped out"


def test_the_chroma_angle_survives_a_brightness_change():
    bright = srgb_to_lab(BLUE_INK)
    dim = srgb_to_lab(BLUE_INK * 0.5)
    assert abs(chroma_angle_deg(bright) - chroma_angle_deg(dim)) < 8.0
    assert relative_chroma(dim) > 0.5 * relative_chroma(bright)


# --- 3. paper-relative, so white balance does not matter -------------

def test_a_white_balance_shift_does_not_move_the_mask():
    img = scene()
    sig = _blue_for(img)
    plain = ink_mask(img, sig, sheet_mask())
    warm = ink_mask(scene(gain=(1.15, 1.0, 0.82)), sig, sheet_mask())
    cool = ink_mask(scene(gain=(0.85, 1.0, 1.2)), sig, sheet_mask())
    assert plain.sum() > 0
    assert np.array_equal(plain, warm)
    assert np.array_equal(plain, cool)


def test_balance_makes_the_reference_neutral():
    img = scene()
    balanced = balance(img, white_point(img, sheet_mask()))
    lab = srgb_to_lab(balanced)
    paper = lab[..., 0] >= np.percentile(lab[..., 0], 90)
    assert abs(float(lab[..., 1][paper].mean())) < 2.0
    assert abs(float(lab[..., 2][paper].mean())) < 2.0


# --- 4. the swap: colour is data, not code ---------------------------

def test_a_signature_selects_its_own_colour():
    blue_scene = scene(ink_rgb=BLUE_INK)
    red_scene = scene(ink_rgb=RED_INK)
    blue = measure_signature(blue_scene, PEGS, radius_px=40)
    red = measure_signature(red_scene, PEGS, radius_px=40)

    assert len(candidates(blue_scene, blue)) == 3
    assert len(candidates(red_scene, red)) == 3
    with pytest.raises(ValueError, match="ink_not_found"):
        candidates(red_scene, blue)
    with pytest.raises(ValueError, match="ink_not_found"):
        candidates(blue_scene, red)


def test_the_two_signatures_differ_only_in_their_numbers():
    blue = measure_signature(scene(ink_rgb=BLUE_INK), PEGS, radius_px=40)
    red = measure_signature(scene(ink_rgb=RED_INK), PEGS, radius_px=40)
    delta = abs((blue.direction_deg - red.direction_deg + 180) % 360 - 180)
    assert delta > 60.0


# --- 5. an empty channel refuses, and says so ------------------------

def test_a_frame_with_no_ink_refuses_rather_than_falling_back():
    img = scene(ink_rgb=None)
    calibration = Calibration(ink=BLUE)
    pose = fit_pose(luminance(img), calibration, rgb=img)
    assert not pose.accepted
    assert "ink_not_found" in pose.reason


# --- 6. no signature, no change --------------------------------------

_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", ".."))
_FRAME = os.path.join(_ROOT, "data", "captures", "fresh_ink",
                      "fresh_ink_007.png")


@pytest.mark.skipif(not os.path.exists(_FRAME), reason="corpus frame absent")
def test_a_calibration_without_ink_detects_exactly_as_before():
    """The whole existing corpus is this case."""
    from PIL import Image
    rgb = np.asarray(Image.open(_FRAME).convert("RGB"), dtype=float)
    gray = luminance(rgb)
    mask = find_sheet(gray)
    common = dict(min_area_px=200.0, max_area_px=20000.0)
    before = find_peg_candidates(gray, mask, **common)
    after = find_peg_candidates(gray, mask, ink=None, rgb=rgb, **common)
    assert len(before) == len(after)
    for a, b in zip(before, after):
        assert a == b


def test_ink_without_the_colour_frame_is_an_error():
    img = scene()
    with pytest.raises(ValueError, match="colour frame"):
        find_peg_candidates(luminance(img), sheet_mask(), min_area_px=60.0,
                            max_area_px=4000.0, ink=BLUE, rgb=None)


# --- 7. the gate proposes, the greyscale fit measures ----------------

def test_ink_on_a_corner_still_yields_the_whole_crown():
    """The reason not to fit a rectangle to the ink.

    The crown is 52 x 20; the ink patch is 14 x 8 in one corner. A fit
    to the ink would report the patch, and its angle would be noise.
    """
    img = scene(ink_corner_only=True)
    found = candidates(img, _blue_for(scene()))
    assert len(found) == 3
    for blob in found:
        assert blob.long_px > 40, (
            f"long axis {blob.long_px:.1f} px is the ink patch, "
            f"not the 52 px crown")
        assert 14 < blob.short_px < 28


# --- the corpus, which is what the synthetic scenes stand in for -----

_CORPUS = [
    ("fresh_ink/fresh_ink_007", [(1280, 1952), (2001, 1828), (2520, 1737)]),
    ("fresh_ink/fresh_ink_008", [(1280, 1952), (2001, 1828), (2520, 1737)]),
    ("blue/blue_010", [(1252, 1920), (1988, 1848), (2512, 1740)]),
    ("blue/blue_008", [(1252, 1920), (1988, 1848), (2512, 1740)]),
    ("blue_hamster/blue_hamster_003",
     [(1343, 1916), (2033, 1815), (2530, 1730)]),
    ("blue_hamster/blue_hamster_002",
     [(1340, 2015), (2043, 1832), (2558, 1668)]),
]


def _corpus_frame(stem: str):
    path = os.path.join(_ROOT, "data", "captures", stem + ".png")
    if not os.path.exists(path):
        pytest.skip(f"{stem} is not in the working tree")
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB"), dtype=float)


@pytest.mark.parametrize("stem,pegs", _CORPUS)
def test_every_inked_frame_yields_exactly_the_three_pegs(stem, pegs):
    """What the synthetic scenes are a stand-in for.

    Two of these have artwork on them, where the luminance path returns
    34 to 36 candidates and cannot rank them, and two have pegs whose
    ink had worn for a day.
    """
    rgb = _corpus_frame(stem)
    gray = luminance(rgb)
    sheet = find_sheet(gray)
    found = find_peg_candidates(gray, sheet, min_area_px=200.0,
                                max_area_px=20000.0,
                                ink=InkSignature(), rgb=rgb)
    assert len(found) == 3
    for blob in found:
        nearest = min(np.hypot(blob.x - px, blob.y - py) for px, py in pegs)
        assert nearest < 45, (f"a candidate at ({blob.x:.0f}, {blob.y:.0f}) "
                              f"is {nearest:.0f} px from any peg")


@pytest.mark.parametrize("stem,pegs", _CORPUS[:1])
def test_a_signature_measured_from_a_frame_works_on_it(stem, pegs):
    rgb = _corpus_frame(stem)
    signature = measure_signature(rgb, pegs, name="pen+GEAR dry erase blue")
    assert abs(signature.direction_deg - InkSignature().direction_deg) < 15.0
    gray = luminance(rgb)
    found = find_peg_candidates(gray, find_sheet(gray), min_area_px=200.0,
                                max_area_px=20000.0, ink=signature, rgb=rgb)
    assert len(found) == 3


# --- 8. the sampling window: clipped to the sheet, fixed count -------
#
# A window wide enough to absorb the peg prediction's error reaches
# past the punched edge, and what lies beyond is the wooden desk.

def _sheet_frames():
    return {
        "blank": "fresh_ink/fresh_ink_007",
        "art": "fresh_ink/fresh_ink_008",
    }


def _corpus(stem: str):
    path = os.path.join(_ROOT, "data", "captures", stem + ".png")
    if not os.path.exists(path):
        pytest.skip(f"{stem} is not in the working tree")
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB"), dtype=float)


def _rig():
    import json
    path = os.path.join(_ROOT, "data", "calibration", "distortion",
                        "v4k_01", "v4k_01.json")
    if not os.path.exists(path):
        pytest.skip("the rig calibration is not in the working tree")
    with open(path) as handle:
        return Calibration.from_dict(json.load(handle))


def _clipped_windows(stem: str):
    """The frame, its predicted pegs, the sheet interior, and a count."""
    from scipy import ndimage
    from .detect import find_sheet
    from .outline import predict_peg_windows, sheet_scale_px_per_mm
    rgb = _corpus(stem)
    gray = (rgb @ np.array([0.2126, 0.7152, 0.0722])) / 255.0
    cal = _rig()
    sheet = find_sheet(gray)
    inside = ndimage.binary_erosion(sheet, iterations=6)
    pegs = [(int(round(x)), int(round(y)))
            for x, y in predict_peg_windows(gray, cal, sheet)]
    scale = sheet_scale_px_per_mm(sheet, gray, cal)
    # The helper rather than an expression written out here. The first
    # version of this used the full area of the LARGER peg, and that
    # count is biased and stays biased as the window grows -- -73.7
    # degrees at radius 70 against -63.8 for the right one. Which
    # count to use is a property of the rig, so it belongs in the code
    # under test and not in its fixture.
    count = ink_pixel_count(cal, scale)
    return rgb, pegs, inside, count


def test_the_window_may_not_reach_the_desk():
    """Unclipped, a 300 px window measures +56 for an ink near -60.

    The desk is saturated brown and wins the chroma selection outright.
    """
    rgb, pegs, inside, count = _clipped_windows("fresh_ink/fresh_ink_007")
    loose = measure_signature(rgb, pegs, radius_px=300)
    clipped = measure_signature(rgb, pegs, radius_px=300, inside=inside,
                                count=count)
    assert abs(_wrap(loose.direction_deg + 60.0)) > 60.0, (
        "this frame no longer reproduces the unclipped failure")
    assert abs(_wrap(clipped.direction_deg + 60.0)) < 15.0


def _wrap(degrees: float) -> float:
    return (degrees + 180.0) % 360.0 - 180.0


@pytest.mark.parametrize("radius", [70, 120, 160, 300, 450])
def test_window_size_stops_mattering_on_a_blank_sheet(radius: int):
    """The point of the fixed count.

    A decile is a fraction, so a larger window is a larger population
    of paper and the selection fills with paper texture. A count sized
    to the peg's own area does not care how much paper is around it.
    """
    rgb, pegs, inside, count = _clipped_windows("fresh_ink/fresh_ink_007")
    got = measure_signature(rgb, pegs, radius_px=radius, inside=inside,
                            count=count)
    assert abs(_wrap(got.direction_deg + 61.0)) < 12.0


def test_the_chroma_floor_stops_collapsing_with_window_size():
    """It fell from 0.216 to 0.036 as the window grew."""
    rgb, pegs, inside, count = _clipped_windows("fresh_ink/fresh_ink_007")
    tight = measure_signature(rgb, pegs, radius_px=70, inside=inside,
                              count=count)
    wide = measure_signature(rgb, pegs, radius_px=450, inside=inside,
                             count=count)
    assert wide.min_chroma > 0.5 * tight.min_chroma


def test_art_is_the_remaining_limit_on_window_width():
    """Recorded so the limit is explicit rather than incidental.

    With the desk and the decile both dealt with, a drawn sheet is
    still only good to about 160 px: the nearest mark is 200 px from a
    peg, and past that the window finds the drawing. This is why an
    ink is measured on a blank sheet.
    """
    rgb, pegs, inside, count = _clipped_windows("fresh_ink/fresh_ink_008")
    near = measure_signature(rgb, pegs, radius_px=160, inside=inside,
                             count=count)
    assert abs(_wrap(near.direction_deg + 62.0)) < 15.0
    far = measure_signature(rgb, pegs, radius_px=300, inside=inside,
                            count=count)
    assert abs(_wrap(far.direction_deg + 62.0)) > 60.0, (
        "the art no longer reaches a 300 px window; re-read the limit")


def test_inside_excludes_what_is_outside_it():
    """The real arrangement: the intruder borders *every* window.

    On the rig the punched edge runs past all three pegs and the desk
    lies beyond it, so a wide window meets the same intruder three
    times over. One window's worth would not settle anything --
    `_dominant_hue` takes the mode, and a minority contaminant is
    supposed to lose to it.
    """
    img = scene()
    intruder = img.copy()
    mask = sheet_mask()
    for cx, cy in PEGS:
        band = (slice(cy - 45, cy - 22), slice(cx - 40, cx + 40))
        # Dark and saturated: the score is chroma *relative to
        # lightness*, and a bright colour loses to a dark ink.
        intruder[band] = np.array([88, 14, 11], dtype=float)
        mask[band] = False

    unmasked = measure_signature(intruder, PEGS, radius_px=40)
    clean = measure_signature(img, PEGS, radius_px=40)
    assert abs(_wrap(unmasked.direction_deg
                     - clean.direction_deg)) > 20.0, (
        "the intruder does not sway the result, so this tests nothing")

    masked = measure_signature(intruder, PEGS, radius_px=40, inside=mask)
    assert abs(_wrap(masked.direction_deg - clean.direction_deg)) < 4.0


def test_a_window_with_almost_nothing_inside_is_skipped_not_fatal():
    """A peg masked away contributes nothing and the rest still works."""
    img = scene()
    mask = sheet_mask()
    mask[:, :PEGS[0][0] + 40] = False        # the leftmost peg, gone
    got = measure_signature(img, PEGS, radius_px=40, inside=mask)
    assert isinstance(got, InkSignature)
    assert abs(_wrap(got.direction_deg
                     - _blue_for(img).direction_deg)) < 10.0


def test_a_fixed_count_beats_a_percentile_on_a_wide_window():
    """What `count` is for, on a scene where the difference shows.

    A decile of a wide window is mostly paper, and on this scene that
    is not a subtle degradation -- there is so little ink in the
    decile that the measurement refuses outright. A count sized to the
    ink does not care how much paper surrounds it.
    """
    img = scene()
    mask = sheet_mask()
    tight = measure_signature(img, PEGS, radius_px=30, inside=mask)
    with pytest.raises(ValueError, match="no ink found"):
        measure_signature(img, PEGS, radius_px=110, inside=mask)
    by_count = measure_signature(img, PEGS, radius_px=110, inside=mask,
                                 count=20 * 52)
    assert abs(_wrap(by_count.direction_deg - tight.direction_deg)) < 6.0


def test_a_count_larger_than_the_window_is_harmless():
    img = scene()
    got = measure_signature(img, PEGS, radius_px=40, inside=sheet_mask(),
                            count=10 ** 7)
    assert isinstance(got, InkSignature)


def test_the_old_call_still_behaves_as_it_did():
    """Neither argument given means the percentile, unchanged.

    bin/measure-ink with hand-typed --peg coordinates is that call.
    """
    img = scene()
    before = measure_signature(img, PEGS, radius_px=40)
    assert abs(_wrap(before.direction_deg
                     - _blue_for(img).direction_deg)) < 1.0


# --- 9. the three marking media, each with its own signature ---------

_MEDIA = {
    "dry erase": ("fresh_ink/fresh_ink_007", "v4k_01.json",
                  [(1283, 1951), (2005, 1830), (2538, 1734)]),
    "steel blue": ("dykem_steel_blue/dykem_steel_blue_002",
                   "v4k_01_steel_blue.json",
                   [(1111, 1966), (1850, 1817), (2404, 1705)]),
    "brite mark": ("dykem_brite_mark_blue/dykem_brite_mark_blue_006",
                   "v4k_01_blue_84001.json",
                   [(1098, 2041), (1841, 1900), (2397, 1794)]),
}


def _calibration(name: str) -> Calibration:
    import json
    path = os.path.join(_ROOT, "data", "calibration", "distortion",
                        "v4k_01", name)
    if not os.path.exists(path):
        pytest.skip(f"{name} is not in the working tree")
    with open(path) as handle:
        return Calibration.from_dict(json.load(handle))


@pytest.mark.parametrize("medium", sorted(_MEDIA))
def test_each_medium_is_found_by_its_own_signature(medium: str):
    stem, calibration, pegs = _MEDIA[medium]
    rgb = _corpus(stem)
    gray = luminance(rgb) if rgb.max() <= 1.0 else (
        rgb @ np.array([0.2126, 0.7152, 0.0722])) / 255.0
    ink = _calibration(calibration).ink
    assert ink is not None, f"{calibration} carries no ink block"
    found = find_peg_candidates(gray, find_sheet(gray), min_area_px=200.0,
                                max_area_px=20000.0, ink=ink, rgb=rgb)
    assert len(found) == 3
    for blob in found:
        nearest = min(np.hypot(blob.x - px, blob.y - py) for px, py in pegs)
        assert nearest < 60


def test_the_tight_signature_is_specific_and_the_loose_ones_general():
    """Pins the cross-detection matrix rather than leaving it in prose.

    Brite-Mark is opaque paint and measures a 0.649 chroma floor, which
    is above what a thin layout fluid puts down -- so its signature
    finds only two pegs on the Steel Blue frame. That is the right
    trade and not a fault, but it does mean the calibration has to
    match the ink actually on the bar. The first two media were
    interchangeable and lulled us into assuming the third would be.
    """
    results = {}
    for medium, (stem, _, pegs) in _MEDIA.items():
        rgb = _corpus(stem)
        gray = (rgb @ np.array([0.2126, 0.7152, 0.0722])) / 255.0
        sheet = find_sheet(gray)
        for signature, (_, calibration, _) in _MEDIA.items():
            ink = _calibration(calibration).ink
            try:
                found = find_peg_candidates(
                    gray, sheet, min_area_px=200.0, max_area_px=20000.0,
                    ink=ink, rgb=rgb)
            except ValueError:
                results[(medium, signature)] = 0
                continue
            results[(medium, signature)] = sum(
                min(np.hypot(b.x - px, b.y - py) for px, py in pegs) < 60
                for b in found)

    assert results[("steel blue", "brite mark")] == 2, (
        "the tight signature no longer discriminates; re-read the table")
    for medium in _MEDIA:
        for signature in ("dry erase", "steel blue"):
            assert results[(medium, signature)] == 3, (
                f"the {signature} signature stopped being general: "
                f"{results[(medium, signature)]}/3 on {medium}")
    assert results[("brite mark", "brite mark")] == 3
