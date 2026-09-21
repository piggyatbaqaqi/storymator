"""Landmarks that are not in the paper plane, and what that costs.

A registration fit assumes its landmarks lie on the sheet. Two of the
three do not, and the third does for a reason worth stating.

**The rectangular landmarks are holes.** The slots are 15.75 mm against
a 12.70 mm peg, so about 3 mm stands open, and on-axis light does not
reach into it -- the open slot reads as dark as the peg and the blob
that gets detected is the hole. A hole is in the paper plane, h = 0,
and needs no correction at all. Measured on the rig 2026-09-21: the
span between the two rect landmarks came out 203.47 mm against a
nominal 203.23, off by +0.24.

**The round landmark is the peg's dome**, because the round peg grips
its hole -- no clearance, so no open hole to see. The dome is
hemispherical, so its apparent position is the projection of the
sphere's *centre*, 5.567 mm above the paper on honbay_0001.

A landmark at height *h*, seen from working distance *Z*, appears
pushed **away** from the principal point. Writing ``r`` for its
*observed* distance from that point, the displacement is ``r*h/Z`` and
the correction is to move it back inward by the same amount.

(The same shift written in terms of the landmark's *true* position is
``r_true*h/(Z-h)``. They agree; ``r*h/Z`` is the one to use, because
observed is what a detector hands you.)

Measured against prediction on the rig, for the round landmark 119 mm
off the axis at Z = 306 mm: predicted 2.2 mm, observed 2.43 mm, while
using the dome's apex instead of its centre would have predicted 3.53
and does not fit.
"""

from __future__ import annotations

from typing import Optional, Sequence

import numpy as np


def working_distance_mm(camera_matrix: np.ndarray, px_per_mm: float) -> float:
    """How far the paper plane is, from the focal length and the scale.

    ``fx`` is in pixels and ``px_per_mm`` is the scale *at the paper*,
    so their ratio is the distance in millimetres.
    """
    return float(camera_matrix[0, 0]) / float(px_per_mm)


def correct_parallax(points_px: np.ndarray,
                     heights_mm: Sequence[float],
                     camera_matrix: Optional[np.ndarray],
                     px_per_mm: float) -> np.ndarray:
    """Move raised landmarks back into the paper plane.

    ``heights_mm`` is per point: 0 for anything already in the plane,
    such as a hole. Returns the points unchanged when there are no
    intrinsics, since neither the principal point nor the working
    distance is knowable without them.

    Scaling the radius by ``1 - h/Z`` *is* a shift of ``r*h/Z``, and
    doing it that way keeps the direction exactly radial rather than
    accumulating error in a normalise-and-step.
    """
    points = np.asarray(points_px, dtype=float)
    if camera_matrix is None:
        return points.copy()
    heights = np.asarray(heights_mm, dtype=float)
    if heights.shape[0] != points.shape[0]:
        raise ValueError(f"{heights.shape[0]} heights for "
                         f"{points.shape[0]} points")
    distance = working_distance_mm(camera_matrix, px_per_mm)
    principal = np.array([camera_matrix[0, 2], camera_matrix[1, 2]],
                         dtype=float)
    shrink = (1.0 - heights / distance)[:, None]
    return principal + (points - principal) * shrink
