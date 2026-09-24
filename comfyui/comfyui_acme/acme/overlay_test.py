"""What the diagnostic overlay is drawn from must be in frame pixels.

`Pose.corners_image`, `pegs_image` and `peg_rects` are what
`nodes/_convert.draw_overlay` marks on the captured frame. They are
currently in **undistorted** coordinates, because `fit_pose`
straightens the landmarks before fitting and keeps the straightened
copies. Drawn on the original, still-distorted frame they land 13 to
25 px off the pegs and 24 to 32 px off the sheet corners.

The registered product is unaffected -- the transform is fitted in
undistorted space throughout and consistently -- so this is a drawing
error only. It still matters: the overlay is the operator's only
window onto the detector, and boxes that sit beside the pegs read as a
detector that has missed.

The fix does not need an inverse distortion. The detected points
before straightening are already to hand.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest
from scipy import ndimage

from .detect import find_peg_candidates, find_sheet, sheet_corners
from .fit import fit_pose
from .ink import ink_mask
from .model import Calibration

_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", ".."))

FRAMES = {
    "repaint": ("repaint/repaint_001", "v4k_01_blue_84001.json"),
    "brite mark": ("dykem_brite_mark_blue/dykem_brite_mark_blue_006",
                   "v4k_01_blue_84001.json"),
    "dry erase": ("fresh_ink/fresh_ink_007", "v4k_01.json"),
}


def _load(medium: str):
    stem, cname = FRAMES[medium]
    path = os.path.join(_ROOT, "data", "captures", stem + ".png")
    cal_path = os.path.join(_ROOT, "data", "calibration", "distortion",
                            "v4k_01", cname)
    if not (os.path.exists(path) and os.path.exists(cal_path)):
        pytest.skip("corpus frame or rig calibration absent")
    from PIL import Image
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=float)
    with open(cal_path) as handle:
        cal = Calibration.from_dict(json.load(handle))
    gray = (rgb @ np.array([0.2126, 0.7152, 0.0722])) / 255.0
    return rgb, gray, cal


@pytest.mark.parametrize("medium", sorted(FRAMES))
@pytest.mark.xfail(strict=True, reason="Pose carries undistorted points")
def test_the_drawn_pegs_land_on_the_ink(medium: str):
    """The strongest statement available: on it, not merely near it.

    A peg marker is drawn to tell the operator the detector found
    *that* peg. Anything outside the paint is saying something false.
    """
    rgb, gray, cal = _load(medium)
    pose = fit_pose(gray, cal, rgb=rgb, max_residual_px=1e9)
    sheet = find_sheet(gray)
    marked = ndimage.binary_dilation(
        ink_mask(rgb, cal.ink, ndimage.binary_erosion(sheet, iterations=2)),
        np.ones((9, 9)))
    for x, y in np.asarray(pose.pegs_image):
        assert marked[int(round(y)), int(round(x))], (
            f"the marker at ({x:.0f}, {y:.0f}) is not on any ink")


@pytest.mark.parametrize("medium", sorted(FRAMES))
@pytest.mark.xfail(strict=True, reason="Pose carries undistorted points")
def test_the_drawn_corners_are_the_detected_corners(medium: str):
    """`sheet_corners` is what the operator is being shown."""
    rgb, gray, cal = _load(medium)
    pose = fit_pose(gray, cal, rgb=rgb, max_residual_px=1e9)
    detected = sheet_corners(find_sheet(gray), gray)
    for corner in np.asarray(pose.corners_image):
        nearest = min(np.hypot(corner[0] - q[0], corner[1] - q[1])
                      for q in detected)
        assert nearest < 2.0, (
            f"the drawn corner ({corner[0]:.0f}, {corner[1]:.0f}) is "
            f"{nearest:.0f} px from any detected corner")


@pytest.mark.parametrize("medium", sorted(FRAMES))
@pytest.mark.xfail(strict=True, reason="Pose carries undistorted points")
def test_the_drawn_rectangles_are_the_detected_rectangles(medium: str):
    rgb, gray, cal = _load(medium)
    pose = fit_pose(gray, cal, rgb=rgb, max_residual_px=1e9)
    blobs = find_peg_candidates(gray, find_sheet(gray), min_area_px=200.0,
                                max_area_px=20000.0, ink=cal.ink, rgb=rgb)
    assert pose.peg_rects is not None
    for rect in pose.peg_rects:
        nearest = min(np.hypot(rect.centre[0] - b.x, rect.centre[1] - b.y)
                      for b in blobs)
        assert nearest < 2.0


@pytest.mark.parametrize("medium", sorted(FRAMES))
def test_the_fitted_points_stay_undistorted(medium: str):
    """The correction must not leak into the geometry.

    Straightening the landmarks before fitting is deliberate and is
    what keeps the transform honest. Only the *drawing* copies move.
    """
    rgb, gray, cal = _load(medium)
    straight = fit_pose(gray, cal, rgb=rgb, max_residual_px=1e9)
    from dataclasses import replace
    flat = fit_pose(gray, replace(cal, camera_matrix=None, dist_coeffs=None),
                    rgb=rgb, max_residual_px=1e9)
    assert straight.peg_residual_px < flat.peg_residual_px


def test_without_a_lens_model_the_drawn_points_are_unchanged():
    """No distortion to undo, so nothing to move."""
    from dataclasses import replace
    rgb, gray, cal = _load("repaint")
    flat = replace(cal, camera_matrix=None, dist_coeffs=None)
    pose = fit_pose(gray, flat, rgb=rgb, max_residual_px=1e9)
    blobs = find_peg_candidates(gray, find_sheet(gray), min_area_px=200.0,
                                max_area_px=20000.0, ink=cal.ink, rgb=rgb)
    for x, y in np.asarray(pose.pegs_image):
        nearest = min(np.hypot(x - b.x, y - b.y) for b in blobs)
        assert nearest < 1.0
