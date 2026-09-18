"""Synthetic captures, so the fit can be tested without a rig.

The scene is evaluated analytically in the peg frame and pulled back
through a chosen homography, which means the ground truth is exact: the
test knows the transform it asked for and can compare.  Edges are
anti-aliased, because hard 0/1 edges quantise every feature to the pixel
grid and a test built on them measures the synthesiser rather than the
measurement.
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np

from .geometry import apply_homography
from .model import Calibration


def camera_homography(calibration: Calibration, size_px: Tuple[int, int],
                      rotation_deg: float = 0.0,
                      tilt: Tuple[float, float] = (0.0, 0.0),
                      scale: float = 1.0,
                      centre_offset_px: Tuple[float, float] = (0.0, 0.0),
                      ) -> np.ndarray:
    """A plausible camera view: peg-frame mm -> image pixels.

    ``tilt`` are the projective terms, in units of 1/mm; a few times
    1e-4 gives the sort of keystone a 30-45 degree view produces.
    """
    width, height = size_px
    sheet = calibration.sheet
    theta = math.radians(rotation_deg)
    rot = np.array([
        [math.cos(theta), -math.sin(theta), 0.0],
        [math.sin(theta), math.cos(theta), 0.0],
        [0.0, 0.0, 1.0]])
    # Size the view to whatever the rotated, keystoned sheet actually
    # subtends, rather than to the sheet's own width and height.  A
    # fixed fraction fits at 0 degrees and runs off the frame by 25,
    # and a clipped sheet makes the outline fit latch onto the image
    # border -- which is a defect in the test rig, not in the fitter.
    corners = sheet.corners() - sheet.corners().mean(axis=0)
    spun = corners @ np.array([[math.cos(theta), math.sin(theta)],
                               [-math.sin(theta), math.cos(theta)]])
    reach = np.abs(spun).max(axis=0) * 2.0
    fit = min(width / reach[0], height / reach[1]) * 0.85 * scale
    scl = np.diag([fit, fit, 1.0])
    move = np.array([
        [1.0, 0.0, width / 2 + centre_offset_px[0]],
        [0.0, 1.0, height / 2 + centre_offset_px[1]],
        [0.0, 0.0, 1.0]])
    keystone = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [tilt[0], tilt[1], 1.0]])
    # Centre the SHEET, not the peg-frame origin.  The origin is the
    # round peg, which sits near the punched edge rather than in the
    # middle of the paper, so centring it runs most of the sheet off
    # the frame -- and then the outline fit latches onto the image
    # border instead of the paper and everything downstream is wrong.
    centroid = calibration.sheet.corners().mean(axis=0)
    recentre = np.array([
        [1.0, 0.0, -centroid[0]],
        [0.0, 1.0, -centroid[1]],
        [0.0, 0.0, 1.0]])
    return move @ scl @ rot @ keystone @ recentre


def render(calibration: Calibration, homography: np.ndarray,
           size_px: Tuple[int, int], polarity: str = "dark",
           noise: float = 0.0, seed: int = 0) -> np.ndarray:
    """Render a sheet on its pegs as seen through ``homography``."""
    width, height = size_px
    ys, xs = np.mgrid[0:height, 0:width].astype(float)
    pts = np.column_stack([xs.ravel(), ys.ravel()])
    mm = apply_homography(np.linalg.inv(homography), pts)
    mx = mm[:, 0].reshape(height, width)
    my = mm[:, 1].reshape(height, width)

    # One output pixel, expressed in millimetres, sets the edge softness.
    scale = abs(np.linalg.det(homography[:2, :2])) ** 0.5
    soft = 1.0 / max(scale, 1e-6)

    def cover(signed_mm: np.ndarray) -> np.ndarray:
        return np.clip(0.5 - signed_mm / soft, 0.0, 1.0)

    corners = calibration.sheet.corners()
    lo = corners.min(axis=0)
    hi = corners.max(axis=0)
    sheet = (cover(lo[0] - mx) * cover(mx - hi[0])
             * cover(lo[1] - my) * cover(my - hi[1]))

    peg = calibration.peg
    positions = peg.positions()
    pegs = cover(np.hypot(mx - positions[1, 0], my - positions[1, 1])
                 - peg.round_diameter_mm / 2)
    for px, py in (positions[0], positions[2]):
        pegs = np.maximum(pegs, cover(np.maximum(
            np.abs(mx - px) - peg.rect_long_mm / 2,
            np.abs(my - py) - peg.rect_short_mm / 2)))

    image = sheet * (1.0 - pegs) if polarity == "dark" else \
        np.maximum(sheet * 0.6, pegs)
    if noise > 0:
        image = image + np.random.default_rng(seed).normal(
            0.0, noise, image.shape)
    return np.clip(image, 0.0, 1.0)
