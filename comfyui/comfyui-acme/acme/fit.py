"""The two-stage registration fit, and its refusal.

Stage one takes the homography from the **sheet outline**, because four
corners in general position determine one and three collinear pegs do
not.  Stage two applies a small in-plane rigid correction from the
**pegs**, because the pegs are what the artist's drawing is actually
aligned to and punch tolerance is real.

The leftover disagreement between the observed peg triangle and the
known bar is the residual, and it is the reason this module can refuse.
"""

from __future__ import annotations


import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import numpy as np

from .detect import Blob, find_peg_candidates, find_sheet, sheet_corners
from .geometry import (apply_homography, homography_from_points,
                       point_line_distance, residuals, rigid_from_points, rms)
from .model import Calibration


@dataclass
class Pose:
    """One frame's registration, accepted or not.

    ``transform`` maps image pixels to peg-frame millimetres.  It is
    ``None`` exactly when ``accepted`` is False, so a caller cannot
    silently use a refused fit.
    """

    accepted: bool
    reason: str
    transform: Optional[np.ndarray] = None
    peg_residual_px: float = float("nan")
    peg_residual_max_px: float = float("nan")
    outline_residual_px: float = float("nan")
    punch_offset_mm: float = float("nan")
    corners_image: Optional[np.ndarray] = None
    pegs_image: Optional[np.ndarray] = None
    per_landmark_px: dict = field(default_factory=dict)

    def summary(self) -> str:
        if not self.accepted:
            return f"REJECTED  {self.reason}"
        return (f"accepted  residual {self.peg_residual_px:.2f} px "
                f"(max {self.peg_residual_max_px:.2f}), "
                f"outline {self.outline_residual_px:.2f} px, "
                f"punch offset {self.punch_offset_mm*1000:.0f} um")


def select_peg_triple(blobs: Sequence[Blob], spacing_px: float,
                      tolerance_px: float, max_candidates: int = 60
                      ) -> Tuple[Optional[List[Blob]], str]:
    """Pick the three blobs that match the bar, or explain the failure.

    Searches **pairs**, not triples.  The two rectangular pegs are
    2 x spacing apart with the round peg at their midpoint, so for each
    pair at the right separation there is exactly one place the third
    peg can be -- which turns an O(n^3) scan into O(n^2) with a lookup.
    On a noisy capture that is the difference between seconds and
    minutes, and noisy captures are the ones that produce the most
    candidates.

    The final check is that the round peg is the middle one.  It is
    cheap and it removes a whole class of false positive: three equally
    spaced marks along a drawn line pass the spacing test and fail this.
    """
    if len(blobs) < 3:
        return None, (f"no_candidates  found {len(blobs)} peg-like "
                      f"region(s), need 3")

    # Pegs are among the largest things inside the area window, so when
    # a frame produces a crowd, keep the biggest and say so if it fails.
    pool = sorted(blobs, key=lambda b: -b.area_px)[:max_candidates]
    centres = np.array([b.centre for b in pool])
    span = 2.0 * spacing_px

    best, best_score = None, None
    for i in range(len(pool)):
        for j in range(i + 1, len(pool)):
            separation = float(np.linalg.norm(centres[j] - centres[i]))
            if abs(separation - span) > 2.0 * tolerance_px:
                continue
            midpoint = (centres[i] + centres[j]) / 2.0
            distances = np.linalg.norm(centres - midpoint, axis=1)
            distances[[i, j]] = np.inf
            k = int(np.argmin(distances))
            if distances[k] > tolerance_px:
                continue
            triple = [pool[i], pool[k], pool[j]]
            if centres[i][0] > centres[j][0]:
                triple = [pool[j], pool[k], pool[i]]
            d1 = float(np.linalg.norm(triple[1].centre - triple[0].centre))
            d2 = float(np.linalg.norm(triple[2].centre - triple[1].centre))
            score = (abs(d1 - spacing_px) + abs(d2 - spacing_px)
                     + point_line_distance(triple[1].centre,
                                           triple[0].centre,
                                           triple[2].centre))
            if best_score is None or score < best_score:
                best, best_score = triple, score

    if best is None:
        return None, (f"no_consistent_triple  {len(blobs)} candidate(s), "
                      f"none forming a collinear trio spaced "
                      f"{spacing_px:.0f} px within {tolerance_px:.0f} px")

    elongations = [b.elongation for b in best]
    if int(np.argmin(elongations)) != 1:
        return None, (f"peg_pattern_mismatch  the least elongated peg is not "
                      f"the centre one (elongations "
                      f"{elongations[0]:.1f}/{elongations[1]:.1f}/"
                      f"{elongations[2]:.1f}); the round peg should be in "
                      f"the middle")
    return best, "ok"


def _punched_edge(corners: np.ndarray, peg_centroid: np.ndarray) -> int:
    """Index of the corner starting the edge nearest the pegs."""
    distances = [
        point_line_distance(peg_centroid, corners[i], corners[(i + 1) % 4])
        for i in range(4)
    ]
    return int(np.argmin(distances))


def _rotation_deg(transform: np.ndarray) -> float:
    return abs(math.degrees(math.atan2(transform[1, 0], transform[0, 0])))


def fit_pose(gray: np.ndarray, calibration: Calibration,
             max_residual_px: float = 1.5,
             polarity: str = "dark",
             sheet_threshold: Optional[float] = None) -> Pose:
    """Register one frame, or say why not."""
    spec = calibration.field_spec
    peg = calibration.peg
    sheet_model = calibration.sheet

    try:
        mask = find_sheet(gray, sheet_threshold)
        corners = sheet_corners(mask, gray)
    except ValueError as exc:
        return Pose(False, f"paper_not_found  {exc}")

    # A rough pixels-per-mm, from the sheet's own diagonal, so the peg
    # search window does not depend on the camera being where we think.
    model_corners = sheet_model.corners()
    scale_px_mm = (np.linalg.norm(corners[2] - corners[0])
                   / np.linalg.norm(model_corners[2] - model_corners[0]))
    round_area, rect_area = peg.nominal_area_mm2()
    try:
        blobs = find_peg_candidates(
            gray, mask,
            min_area_px=0.25 * min(round_area, rect_area) * scale_px_mm ** 2,
            max_area_px=4.0 * max(round_area, rect_area) * scale_px_mm ** 2,
            polarity=polarity)
    except ValueError as exc:
        return Pose(False, str(exc))

    triple, why = select_peg_triple(
        blobs, peg.centre_spacing_mm * scale_px_mm,
        tolerance_px=max(6.0, 0.05 * peg.centre_spacing_mm * scale_px_mm))
    if triple is None:
        return Pose(False, why)

    pegs_image = np.array([b.centre for b in triple])
    peg_centroid = pegs_image.mean(axis=0)
    start = _punched_edge(corners, peg_centroid)

    # The bar is 180-degree symmetric and a nominally centred punch does
    # not break the tie, so both orderings of the punched edge are
    # geometrically valid.  Choose the one that rotates the frame least,
    # which is right whenever the camera is not upside down -- and say
    # so when the two are too close to call, rather than picking one and
    # flipping half a scene.
    candidates = []
    for flip in (False, True):
        idx = [(start + k) % 4 for k in range(4)]
        if flip:
            idx = [idx[1], idx[0], idx[3], idx[2]]
        try:
            h = homography_from_points(corners[idx], model_corners)
        except (ValueError, np.linalg.LinAlgError):
            continue
        candidates.append((idx, h))
    if not candidates:
        return Pose(False, "degenerate_outline  the four corners do not "
                           "support a homography")

    scored = sorted(candidates,
                    key=lambda c: _rotation_deg(spec.matrix() @ c[1]))
    idx, h = scored[0]
    if len(scored) == 2:
        gap = abs(_rotation_deg(spec.matrix() @ scored[1][1])
                  - _rotation_deg(spec.matrix() @ scored[0][1]))
        if gap < 20.0:
            return Pose(False,
                        f"ambiguous_orientation  the two sheet orientations "
                        f"differ by only {gap:.0f} deg of frame rotation; "
                        f"set bar_position explicitly")

    # Stage two: the pegs are the datum, so bring them onto the model.
    pegs_mm = apply_homography(h, pegs_image)
    model_pegs = peg.positions()
    if pegs_mm[0, 0] > pegs_mm[2, 0]:
        model_pegs = model_pegs[::-1]
    correction = rigid_from_points(pegs_mm, model_pegs)
    transform = correction @ h

    peg_errors = residuals(transform, pegs_image, model_pegs)
    corner_errors = residuals(transform, corners[idx], model_corners)
    px_mm = spec.px_per_mm
    peg_rms_px = rms(peg_errors) * px_mm
    punch_offset_mm = float(np.linalg.norm(correction[:2, 2]))

    pose = Pose(
        accepted=peg_rms_px <= max_residual_px,
        reason="accepted",
        transform=transform,
        peg_residual_px=peg_rms_px,
        peg_residual_max_px=float(peg_errors.max()) * px_mm,
        outline_residual_px=rms(corner_errors) * px_mm,
        punch_offset_mm=punch_offset_mm,
        corners_image=corners[idx],
        pegs_image=pegs_image,
        per_landmark_px={
            "peg_-x": float(peg_errors[0]) * px_mm,
            "peg_round": float(peg_errors[1]) * px_mm,
            "peg_+x": float(peg_errors[2]) * px_mm,
            **{f"corner_{i}": float(e) * px_mm
               for i, e in enumerate(corner_errors)},
        },
    )
    if not pose.accepted:
        pose.reason = (f"residual_too_high  {peg_rms_px:.2f} px > "
                       f"{max_residual_px:.2f} px threshold; check for "
                       f"paper curl or a mis-detected peg")
        pose.transform = None
    return pose
