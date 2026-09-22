"""The two-stage registration fit, and its refusal.

Stage one takes the homography from the **sheet outline**, because four
corners in general position determine one and three collinear pegs do
not.  Stage two applies a small in-plane rigid correction from the
**pegs**, because the pegs are what the artist's drawing is actually
aligned to and punch tolerance is real.

The leftover disagreement between the observed peg triangle and the
known bar is the residual, and it is the reason this module can refuse.

**The peg pattern is tested in millimetres, never in pixels.**  On a
real keystoned capture the two halves of the bar project to visibly
different lengths -- 778 px and 564 px on the first rig photograph, a
38 % difference for two spacings that are equal to a thousandth of an
inch on the bar itself.  Any equal-spacing test in image space is
therefore testing the camera angle.  Mapping candidates through the
outline homography first removes the projection, and then the spacings
really are equal.
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
from .parallax import correct_parallax
from .rect import Rect


#: How far the detected pegs may sit from the peg line before an
#: orientation is treated as implausible rather than merely worse.
#: Generous against everything that legitimately moves them -- punch
#: scatter is 0.27 mm sd across the ream, peg-top parallax reaches
#: ~2 mm, detection error ~1 mm -- and far below the ~192 mm that
#: fitting the sheet end for end produces.
PEG_LINE_TOLERANCE_MM = 25.0


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
    # The fitted slots, so the overlay can draw what was actually
    # matched rather than a circle that says only "something here".
    peg_rects: Optional[List["Rect"]] = None
    per_landmark_px: dict = field(default_factory=dict)

    def summary(self) -> str:
        if not self.accepted:
            return f"REJECTED  {self.reason}"
        return (f"accepted  residual {self.peg_residual_px:.2f} px "
                f"(max {self.peg_residual_max_px:.2f}), "
                f"outline {self.outline_residual_px:.2f} px, "
                f"punch offset {self.punch_offset_mm:.2f} mm")


def select_peg_triple(blobs: Sequence[Blob], positions_mm: np.ndarray,
                      spacing_mm: float, tolerance_mm: float,
                      max_candidates: int = 60
                      ) -> Tuple[Optional[List[int]], float, str]:
    """Indices of the three blobs matching the bar, in millimetre space.

    Searches **pairs**, not triples.  The rectangular pegs are
    2 x spacing apart with the round peg at their midpoint, so each
    qualifying pair leaves exactly one place for the third -- which
    turns an O(n^3) scan into O(n^2) with a lookup.  On a noisy capture
    that is the difference between seconds and minutes, and noisy
    captures produce the most candidates.

    Returns ``(indices, score, reason)`` with lower scores better.
    """
    if len(blobs) < 3:
        return None, float("inf"), (
            f"no_candidates  found {len(blobs)} peg-like region(s), need 3")

    order = sorted(range(len(blobs)), key=lambda i: -blobs[i].area_px
                   )[:max_candidates]
    pts = positions_mm[order]
    span = 2.0 * spacing_mm

    best: Optional[List[int]] = None
    best_score = float("inf")
    for a in range(len(order)):
        for b in range(a + 1, len(order)):
            separation = float(np.linalg.norm(pts[b] - pts[a]))
            if abs(separation - span) > 2 * tolerance_mm:
                continue
            midpoint = (pts[a] + pts[b]) / 2.0
            distance = np.linalg.norm(pts - midpoint, axis=1)
            distance[[a, b]] = np.inf
            c = int(np.argmin(distance))
            if distance[c] > tolerance_mm:
                continue
            left, right = (a, b) if pts[a][0] <= pts[b][0] else (b, a)
            d1 = float(np.linalg.norm(pts[c] - pts[left]))
            d2 = float(np.linalg.norm(pts[right] - pts[c]))
            straight = point_line_distance(pts[c], pts[left], pts[right])
            score = abs(d1 - spacing_mm) + abs(d2 - spacing_mm) + straight
            # The round peg belongs in the middle.  A preference rather
            # than a veto: on a real rig the pegs are specular metal and
            # the dark region is whichever part of each happens to be
            # shaded, so measured elongation is a lighting artefact as
            # much as a shape one.
            elong = [blobs[order[i]].elongation for i in (left, c, right)]
            if int(np.argmin(elong)) != 1:
                score += tolerance_mm
            if score < best_score:
                best = [order[left], order[c], order[right]]
                best_score = score

    if best is None:
        return None, float("inf"), (
            f"no_consistent_triple  {len(blobs)} candidate(s), none forming "
            f"a collinear trio spaced {spacing_mm:.1f} mm within "
            f"{tolerance_mm:.1f} mm")
    return best, best_score, "ok"


def _rotation_deg(transform: np.ndarray) -> float:
    return abs(math.degrees(math.atan2(transform[1, 0], transform[0, 0])))


def _orientations(corners: np.ndarray) -> List[List[int]]:
    """The four ways a rectangle's corners can be labelled.

    Which edge is the punched one cannot be decided before the pegs are
    located, and the pegs cannot be mapped to millimetres before an
    orientation is chosen.  Rather than break that circle with a guess,
    enumerate the four starting edges and let the bar's own geometry
    say which hypothesis is right.

    **Cyclic rotations only.**  Swapping a pair of corners instead
    produces a *reflection*, and a reflected labelling fits a mirrored
    sheet -- which cannot happen to paper viewed from one side, but
    which a homography will cheerfully deliver.  Admitting them once
    registered two captures of the same sheet into mirror images of
    each other, agreeing to 0.03 mm on |y| and disagreeing on its sign.
    """
    return [[(start + k) % 4 for k in range(4)] for start in range(4)]


def fit_pose(gray: np.ndarray, calibration: Calibration,
             max_residual_px: float = 1.5,
             polarity: str = "dark",
             sheet_threshold: Optional[float] = None,
             peg_contrast: float = 0.6,
             peg_tolerance_mm: float = 6.0,
             rgb: Optional[np.ndarray] = None) -> Pose:
    """Register one frame, or say why not."""
    spec = calibration.raster
    peg = calibration.peg
    model_corners = calibration.sheet.corners()
    model_pegs = peg.positions()

    try:
        mask = find_sheet(gray, sheet_threshold)
        corners, edge_samples = sheet_corners(
            mask, gray, return_samples=True)
    except ValueError as exc:
        return Pose(False, f"paper_not_found  {exc}")

    # Straighten the landmarks, not the picture.  Correcting a handful
    # of points is exact and free; resampling a 4K frame to correct it
    # is neither, and would blur the pixels the warp still has to
    # sample.  Skipped entirely when no intrinsics are present, which
    # keeps OpenCV optional.
    matrix = calibration.camera_matrix
    coeffs = calibration.dist_coeffs
    if matrix is not None and coeffs is not None:
        from .lens import undistort_points
        corners = undistort_points(corners, matrix, coeffs)
        # The edge samples measure the outline residual and must live in
        # the same space as the corners the transform was fitted to.
        # Straightening one and not the other silently compares a
        # corrected fit against uncorrected observations, which makes
        # applying a *good* calibration look like it made things worse.
        edge_samples = {
            name: undistort_points(pts, matrix, coeffs)
            for name, pts in edge_samples.items()
        }

    scale_px_mm = (np.linalg.norm(corners[2] - corners[0])
                   / np.linalg.norm(model_corners[2] - model_corners[0]))
    round_area, rect_area = peg.nominal_area_mm2()
    try:
        blobs = find_peg_candidates(
            gray, mask,
            min_area_px=float(0.05 * min(round_area, rect_area)
                              * scale_px_mm ** 2),
            max_area_px=float(6.0 * max(round_area, rect_area)
                              * scale_px_mm ** 2),
            polarity=polarity, contrast=peg_contrast,
            ink=calibration.ink, rgb=rgb)
    except ValueError as exc:
        return Pose(False, str(exc))
    if len(blobs) < 3:
        return Pose(False, f"no_candidates  found {len(blobs)} peg-like "
                           f"region(s), need 3")

    centres = np.array([b.centre for b in blobs])
    if matrix is not None and coeffs is not None:
        from .lens import undistort_points
        centres = undistort_points(centres, matrix, coeffs)

    accepted_hypotheses = []
    last_reason = "no_consistent_triple  no orientation produced a peg trio"
    for idx in _orientations(corners):
        try:
            h = homography_from_points(corners[idx], model_corners)
        except (ValueError, np.linalg.LinAlgError):
            continue
        # Belt and braces against the mirror above: a fit that reverses
        # handedness is describing a sheet seen from behind.
        if np.linalg.det(h[:2, :2]) <= 0:
            continue
        candidates_mm = apply_homography(h, centres)
        triple, score, reason = select_peg_triple(
            blobs, candidates_mm, peg.centre_spacing_mm, peg_tolerance_mm)
        if triple is None:
            last_reason = reason
            continue
        # How far the chosen pegs sit from the peg line, which is y = 0
        # by definition of the peg frame.  This is what separates an
        # orientation from its 180-degree twin; see below.
        off_line = float(np.abs(candidates_mm[triple][:, 1]).mean())
        accepted_hypotheses.append((score, off_line, idx, h, triple))

    if not accepted_hypotheses:
        return Pose(False, last_reason)

    # Several orientations fit the BAR equally well, because peg
    # spacing and collinearity are both unchanged by turning the sheet
    # end for end.  What is not unchanged is where the pegs land: the
    # punch is deliberately off-centre across the sheet, 12 mm from the
    # punched edge and 203.9 mm from the far one, so the wrong end puts
    # the pegs ~192 mm from the line they are nailed to.
    #
    # That is decisive and physical, where "prefer the smaller frame
    # rotation" is a guess about how the camera is mounted -- and it
    # guessed wrong on the first real rig capture, fitting the sheet
    # 180 degrees out with a 568 px outline residual while reporting a
    # plausible-looking peg fit.  Rule the implausible ones out first,
    # then keep the old tiebreak for hypotheses that are genuinely
    # ambiguous.
    def _preference(candidate):
        score, off_line, _, homography, _ = candidate
        return (off_line > PEG_LINE_TOLERANCE_MM,
                round(score, 2),
                _rotation_deg(spec.matrix() @ homography))

    accepted_hypotheses.sort(key=_preference)
    best_score, best_off_line, idx, h, triple = accepted_hypotheses[0]

    # Ranking the implausible last is not enough when EVERY hypothesis
    # is implausible -- the sort still hands one back.  Measured on a
    # page of real artwork: 44 to 56 candidates against 4 on blank
    # paper, and the fit settled on a letter of the title, a drawn
    # figure, and one real peg, reporting a punch offset of 120 mm
    # against a nominal 12.  It did that identically under two
    # lightings, so it looked repeatable.
    #
    # Refuse instead.  A refusal is visible; a confident fit of three
    # drawings is not, and the drawings are the whole point of the rig.
    if best_off_line > PEG_LINE_TOLERANCE_MM:
        return Pose(False, (
            f"peg_line  the best orientation puts the pegs "
            f"{best_off_line:.0f} mm from the peg line, past the "
            f"{PEG_LINE_TOLERANCE_MM:.0f} mm limit -- usually artwork "
            f"forming a false trio, since the punch sits "
            f"{abs(calibration.sheet.punch_offset_mm):.0f} mm from the "
            f"punched edge and cannot be anywhere near that far"))

    pegs_image = centres[triple]
    # Correct landmarks that stand above the paper, before the rigid
    # stage -- which would otherwise absorb the displacement into a
    # translation and hide it, exactly as it hid the 180-degree flip.
    # pegs_image itself stays as DETECTED, so the overlay keeps showing
    # the operator where the blob actually was.
    pegs_fitted = correct_parallax(
        pegs_image,
        [peg.rect_landmark_height_mm, peg.round_landmark_height_mm,
         peg.rect_landmark_height_mm],
        matrix, float(scale_px_mm))
    pegs_mm = apply_homography(h, pegs_fitted)
    correction = rigid_from_points(pegs_mm, model_pegs)
    transform = correction @ h

    peg_errors = residuals(transform, pegs_fitted, model_pegs)
    corner_errors = residuals(transform, corners[idx], model_corners)
    px_mm = spec.px_per_mm
    peg_rms_px = rms(peg_errors) * px_mm

    # Outline residual, measured properly: map every sampled edge point
    # into millimetres and ask how far it sits from the nearest side of
    # the model rectangle.  The four corners cannot answer this -- the
    # homography places them exactly by construction -- so what this
    # number reports is curl and lens distortion, the two things that
    # make a sheet not a plane.
    lo = model_corners.min(axis=0)
    hi = model_corners.max(axis=0)
    flat = np.vstack(list(edge_samples.values()))
    mapped = apply_homography(transform, flat)
    to_side = np.minimum(
        np.minimum(np.abs(mapped[:, 0] - lo[0]), np.abs(mapped[:, 0] - hi[0])),
        np.minimum(np.abs(mapped[:, 1] - lo[1]), np.abs(mapped[:, 1] - hi[1])))
    outline_rms_px = rms(to_side) * px_mm

    pose = Pose(
        accepted=peg_rms_px <= max_residual_px,
        reason="accepted",
        transform=transform,
        peg_residual_px=peg_rms_px,
        peg_residual_max_px=float(peg_errors.max()) * px_mm,
        outline_residual_px=outline_rms_px,
        punch_offset_mm=float(np.linalg.norm(correction[:2, 2])),
        corners_image=corners[idx],
        pegs_image=pegs_image,
        peg_rects=[Rect(centre=centres[i], long_px=blobs[i].long_px,
                        short_px=blobs[i].short_px,
                        angle_rad=blobs[i].angle_rad) for i in triple],
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
