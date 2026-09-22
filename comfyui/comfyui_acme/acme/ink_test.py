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
from .ink import (balance, chroma_angle_deg, ink_mask, measure_signature,
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

@pytest.mark.xfail(strict=True, reason="acme.ink is a skeleton")
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


@pytest.mark.xfail(strict=True, reason="acme.ink is a skeleton")
def test_the_shadow_is_not_a_candidate():
    """The confuser the luminance path cannot reject."""
    img = scene()
    for blob in candidates(img, _blue_for(img)):
        assert blob.y > 130, f"a candidate at y={blob.y:.0f} is the shadow"


# --- 2. a dim peg is still a peg -------------------------------------

@pytest.mark.xfail(strict=True, reason="acme.ink is a skeleton")
def test_a_peg_at_half_brightness_is_still_found():
    """The claim the right peg falsifies under an absolute threshold.

    Lab's cube root makes the (a*, b*) angle nearly invariant to how
    brightly a peg renders, which is why the angle carries the colour
    and the magnitude only rejects grey.
    """
    img = scene(dim_peg=2)
    found = candidates(img, _blue_for(scene()))
    assert len(found) == 3, "the dim peg dropped out"


@pytest.mark.xfail(strict=True, reason="acme.ink is a skeleton")
def test_the_chroma_angle_survives_a_brightness_change():
    bright = srgb_to_lab(BLUE_INK)
    dim = srgb_to_lab(BLUE_INK * 0.5)
    assert abs(chroma_angle_deg(bright) - chroma_angle_deg(dim)) < 8.0
    assert relative_chroma(dim) > 0.5 * relative_chroma(bright)


# --- 3. paper-relative, so white balance does not matter -------------

@pytest.mark.xfail(strict=True, reason="acme.ink is a skeleton")
def test_a_white_balance_shift_does_not_move_the_mask():
    img = scene()
    sig = _blue_for(img)
    plain = ink_mask(img, sig, sheet_mask())
    warm = ink_mask(scene(gain=(1.15, 1.0, 0.82)), sig, sheet_mask())
    cool = ink_mask(scene(gain=(0.85, 1.0, 1.2)), sig, sheet_mask())
    assert plain.sum() > 0
    assert np.array_equal(plain, warm)
    assert np.array_equal(plain, cool)


@pytest.mark.xfail(strict=True, reason="acme.ink is a skeleton")
def test_balance_makes_the_reference_neutral():
    img = scene()
    balanced = balance(img, white_point(img, sheet_mask()))
    lab = srgb_to_lab(balanced)
    paper = lab[..., 0] > np.percentile(lab[..., 0], 90)
    assert abs(float(lab[..., 1][paper].mean())) < 2.0
    assert abs(float(lab[..., 2][paper].mean())) < 2.0


# --- 4. the swap: colour is data, not code ---------------------------

@pytest.mark.xfail(strict=True, reason="acme.ink is a skeleton")
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


@pytest.mark.xfail(strict=True, reason="acme.ink is a skeleton")
def test_the_two_signatures_differ_only_in_their_numbers():
    blue = measure_signature(scene(ink_rgb=BLUE_INK), PEGS, radius_px=40)
    red = measure_signature(scene(ink_rgb=RED_INK), PEGS, radius_px=40)
    delta = abs((blue.direction_deg - red.direction_deg + 180) % 360 - 180)
    assert delta > 60.0


# --- 5. an empty channel refuses, and says so ------------------------

@pytest.mark.xfail(strict=True, reason="acme.ink is a skeleton")
def test_a_frame_with_no_ink_refuses_rather_than_falling_back():
    img = scene(ink_rgb=None)
    calibration = Calibration(ink=BLUE)
    pose = fit_pose(luminance(img), calibration, rgb=img)
    assert not pose.ok
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

@pytest.mark.xfail(strict=True, reason="acme.ink is a skeleton")
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
