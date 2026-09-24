"""Two candidate replacements for the sheet's corner finder.

:func:`acme.detect.sheet_corners` sorts boundary points into four
sides using a local frame from :func:`acme.detect._principal_angle`,
which takes the sheet's orientation from the **second moments of its
area**.  On this rig that is degenerate, not merely inaccurate.

A 279.4 x 215.9 mm sheet has an aspect ratio of 1.29, but seen from
the camera's angle the long axis foreshortens and the mask comes out
essentially square: measured over the whole corpus, **43 of 46 frames
sit between 1.00 and 1.06**.  The covariance of a square is isotropic,
so its principal axis is arbitrary -- and the reported angle duly
wanders between 1 and 45 degrees with no relation to how the sheet is
actually placed.  Squaring the bar to the frame does not help, and the
`square` session was shot to check exactly that: the sheet is visibly
square in `square_013` and `square_014`, and the angle comes back
-31.5 and -44.4 degrees.

The frames it gets right are the ones where the arbitrary axis happens
to land near zero.  That is luck, and it has been carrying the whole
outline stage.

Both candidates below take the orientation from the **boundary**
instead, where the corners are.  They are kept side by side so the
choice is made by measurement rather than by argument; `outline_test`
runs the same battery against each.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:            # pragma: no cover
    from .model import Calibration

import numpy as np


def _cv2():
    import cv2
    return cv2


def corner_order(corners: np.ndarray) -> np.ndarray:
    """Corners in a consistent, non-mirrored cyclic order.

    Winding matters downstream: :func:`acme.fit.fit_pose` rejects a
    homography whose linear part has a negative determinant, on the
    grounds that it describes a sheet seen from behind.  A corner
    finder that returned its vertices in whichever order the contour
    tracer happened to walk would make that check fire at random.

    Ordered clockwise in image coordinates -- which is
    counter-clockwise on screen, since y runs down -- starting from
    the corner nearest the origin.
    """
    pts = np.asarray(corners, dtype=float).reshape(-1, 2)
    if len(pts) != 4:
        raise ValueError(f"need four corners, got {len(pts)}")
    centre = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - centre[1], pts[:, 0] - centre[0])
    ordered = pts[np.argsort(angles)]
    start = int(np.argmin(ordered.sum(axis=1)))
    return np.roll(ordered, -start, axis=0)


def _boundary(mask: np.ndarray) -> np.ndarray:
    from scipy import ndimage
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        raise ValueError("no sheet: the mask is empty")
    ys, xs = np.nonzero(mask & ~ndimage.binary_erosion(mask, iterations=1))
    if len(xs) < 40:
        raise ValueError(f"only {len(xs)} boundary points; is the sheet "
                         f"fully in frame?")
    return np.column_stack([xs, ys]).astype(float)


def _fit_sides(points: np.ndarray, corners: np.ndarray,
               gray: Optional[np.ndarray]):
    """Fit a line to each side and intersect them, sub-pixel if asked.

    Assignment is by *which pair of corners a point falls between*,
    measured along the quadrilateral, rather than by sign in some
    global frame.  That is the whole repair: no frame means no
    degenerate frame.
    """
    from .detect import _refine_edge
    from .geometry import fit_line, line_intersection

    corners = corner_order(corners)
    centre = corners.mean(axis=0)
    fits, samples = [], {}
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        along = b - a
        length = float(np.linalg.norm(along))
        if length < 1.0:
            raise ValueError("degenerate quadrilateral: a side of zero length")
        unit = along / length
        rel = points - a
        t = rel @ unit
        # Perpendicular offset, signed towards the centre, so the
        # opposite side of the sheet is never mistaken for this one.
        off = rel[:, 0] * unit[1] - rel[:, 1] * unit[0]
        inward = np.sign((centre - a)[0] * unit[1] - (centre - a)[1] * unit[0])
        # The middle 80 %, because a punched sheet's corner is rounded
        # and often dog-eared while each edge carries thousands of
        # points of evidence.
        near = ((t > 0.1 * length) & (t < 0.9 * length)
                & (np.abs(off) < 0.06 * length)
                & (off * inward >= -0.06 * length))
        side = points[near]
        if len(side) < 50:
            raise ValueError(f"only {len(side)} boundary points on side "
                             f"{i}; is the sheet fully in frame?")
        origin, direction = fit_line(side)
        samples[i] = side
        if gray is not None:
            refined = _refine_edge(gray, origin, direction,
                                   extent=0.8 * length)
            if refined is not None:
                origin, direction = fit_line(refined)
                samples[i] = refined
        fits.append((origin, direction))

    found = np.array([
        line_intersection(*fits[(i - 1) % 4], *fits[i]) for i in range(4)])
    return corner_order(found), {str(k): v for k, v in samples.items()}


def corners_min_area_rect(mask: np.ndarray,
                          gray: Optional[np.ndarray] = None,
                          return_samples: bool = False):
    """Orientation from ``cv2.minAreaRect``, then the existing side sort.

    The smallest enclosing rotated rectangle is fixed by the extreme
    points of the boundary, so a near-square mask is no obstacle: a
    square has a well-defined minimum-area box even though it has no
    well-defined principal axis.

    The smaller change of the two.  Everything after the local frame --
    the middle-80 % trim, the sub-pixel gradient refinement, the
    intersection of fitted lines -- is kept, so the sub-pixel accuracy
    that the rigid peg stage depends on is kept with it.

    It inherits one weakness: the box is fitted to the *convex hull*,
    and a keystoned quadrilateral is not a rotated rectangle, so the
    box's angle is a compromise between the two pairs of opposite
    edges rather than either one.  The line fits absorb that, because
    the box is used only to say which side is which.
    """
    cv2 = _cv2()
    points = _boundary(mask)
    box = cv2.boxPoints(cv2.minAreaRect(
        points.astype(np.float32).reshape(-1, 1, 2)))
    corners, samples = _fit_sides(points, np.asarray(box, dtype=float), gray)
    return (corners, samples) if return_samples else corners


def corners_approx_poly(mask: np.ndarray,
                        gray: Optional[np.ndarray] = None,
                        return_samples: bool = False):
    """The quadrilateral itself, from ``cv2.approxPolyDP``.

    No local frame and no four-way sort: Douglas-Peucker reduces the
    contour to its dominant vertices directly, and boundary points are
    assigned to a side by which pair of vertices they fall between.  A
    keystone is not a special case, because nothing here assumes the
    shape is a rectangle.

    ``approxPolyDP`` returns whatever vertex count its tolerance
    produces, and the epsilon that yields four is not knowable in
    advance -- a rounded or dog-eared corner gives three or five.  So
    it is searched for by bisection rather than taken as a fixed
    fraction of the perimeter, and the hull is used rather than the raw
    contour so that a notch in one edge cannot become a fifth vertex.
    """
    cv2 = _cv2()
    points = _boundary(mask)
    hull = cv2.convexHull(points.astype(np.float32).reshape(-1, 1, 2))
    perimeter = cv2.arcLength(hull, True)

    quad = None
    lo, hi = 0.0005, 0.25
    for _ in range(40):
        mid = (lo + hi) / 2.0
        approx = cv2.approxPolyDP(hull, mid * perimeter, True)
        if len(approx) > 4:
            lo = mid                      # too fine, keep coarsening
        else:
            if len(approx) == 4:
                quad = approx
            hi = mid                      # too coarse, back off
    if quad is None:
        raise ValueError(
            "no four-sided outline: approxPolyDP found no tolerance "
            "giving four vertices, so the sheet is not a quadrilateral "
            "in this frame -- clipped, folded, or merged with its "
            "surroundings")
    corners, samples = _fit_sides(
        points, quad.reshape(-1, 2).astype(float), gray)
    return (corners, samples) if return_samples else corners


def outline_quality(corners: np.ndarray, mask: np.ndarray):
    """``(iou, worst_corner_distance_px)`` of a quad against the mask.

    The measure the two candidates are compared on. IoU alone hides a
    single bad corner in a large area; the worst corner alone ignores a
    quad that is wrong everywhere by a little.
    """
    cv2 = _cv2()
    mask = np.asarray(mask, dtype=bool)
    quad = corner_order(corners)
    filled = np.zeros(mask.shape, dtype=np.uint8)
    cv2.fillPoly(filled, [np.round(quad).astype(np.int32)], 1)
    drawn = filled.astype(bool)
    union = (drawn | mask).sum()
    iou = float((drawn & mask).sum() / union) if union else 0.0

    edge = _boundary(mask)
    worst = max(float(np.min(np.hypot(edge[:, 0] - x, edge[:, 1] - y)))
                for x, y in quad)
    return iou, worst


def predict_peg_windows(gray: np.ndarray,
                        calibration: "Calibration",
                        mask: Optional[np.ndarray] = None) -> np.ndarray:
    """Where the three pegs should be, from the sheet outline alone.

    ``bin/measure-ink`` needs to know where to look before any ink
    signature exists, so this cannot use colour and does not.  The
    outline gives a homography, the bar's nominal geometry says where
    the pegs sit in the sheet's frame, and the inverse puts them back
    in pixels.

    Returns ``(3, 2)`` image points ordered along the bar, matching
    :meth:`acme.model.PegModel.positions` -- one rectangular peg, the
    round peg, the other rectangular peg.

    **The four-fold labelling ambiguity is resolved on luminance.** Two
    of the four cyclic labellings map the sheet's long edge onto the
    model's short one and are thrown out by aspect; the remaining pair
    differ by 180 degrees, which puts the pegs against one long edge or
    the other. Choosing between those is what pegs are *for*, and
    :func:`acme.fit.fit_pose` uses the peg line to do it -- but that is
    not available here, so the darker trio wins. A peg is chrome
    against paper and reads dark from any angle; the opposite edge is
    bare paper.

    This is a *proposal*, and the caller samples a window around each
    point rather than a pixel.  Measured against pegs located by hand
    on six rig captures, it lands **41 to 139 px** from the real thing,
    and the error tracks the paper's bow: the outline fit assumes a
    flat rectangle, and this sheet's free end departs from one by 3 to
    12 mm.  ``PREDICTED_RADIUS_PX`` is sized from that.

    Refining each point onto the darkest compact spot nearby was tried
    and rejected.  It helps on blank paper -- 110 px to 21 on
    ``square_013`` -- and it fails on artwork, where a drawn line is
    darker and more compact than a chrome crown: on ``square_014`` it
    got 139 px only as far as 117, having snapped onto the drawing.
    Anything that keys on darkness alone is confusable by art, which
    is the failure this project keeps rediscovering.
    """
    from .detect import find_sheet
    from .geometry import apply_homography, homography_from_points

    gray = np.asarray(gray, dtype=float)
    if mask is None:
        mask = find_sheet(gray)
    corners = corners_approx_poly(mask, gray)
    model = np.asarray(calibration.sheet.corners(), dtype=float)
    pegs_mm = np.asarray(calibration.peg.positions(), dtype=float)

    best, best_score = None, np.inf
    for shift in range(4):
        order = np.roll(np.arange(4), -shift)
        try:
            h = homography_from_points(corners[order], model)
        except (ValueError, np.linalg.LinAlgError):
            continue
        # A reflected labelling fits a mirrored sheet, which cannot
        # happen to paper viewed from one side.
        if np.linalg.det(h[:2, :2]) <= 0:
            continue
        try:
            points = apply_homography(np.linalg.inv(h), pegs_mm)
        except np.linalg.LinAlgError:       # pragma: no cover - degenerate
            continue
        # Millimetres per pixel is the square root of the linear
        # part's determinant, since h maps image to mm.
        mm_per_px = float(abs(np.linalg.det(h[:2, :2]))) ** 0.5
        if mm_per_px <= 1e-9:               # pragma: no cover - degenerate
            continue
        radius = 0.5 * calibration.peg.round_diameter_mm / mm_per_px
        score = _peg_darkness(gray, points, radius)
        if score < best_score:
            best, best_score = points, score
    if best is None:
        raise ValueError(
            "no usable sheet labelling: every orientation of the outline "
            "was degenerate or mirrored")
    return best


# How wide a window a caller should sample around each predicted
# point.  Set from the prediction's measured accuracy over the corpus
# -- worst 139 px -- with a little margin.  The pegs are 101.6 mm
# apart, about 737 px on this rig, so windows this size do not meet.
PREDICTED_RADIUS_PX = 160


def _peg_darkness(gray: np.ndarray, points: np.ndarray,
                  radius_px: float) -> float:
    """How much darker than its surroundings each point is, summed.

    Lower is better, and a labelling pointing at bare paper scores
    about zero.

    **Sized to the peg, and read at a low percentile.** A fixed window
    read at its median fails at both ends: on a rendered test scene the
    round peg is 16 px across, so a 28 px disc is mostly paper and its
    median says "paper" even when centred exactly on the peg. Taking
    the tenth percentile instead asks whether anything dark is in
    there, which is the actual question, and survives the peg filling
    only part of the disc.

    The comparison is local — disc against surrounding annulus,
    normalised by the annulus — because illumination across this sheet
    varies by 42 %, and an absolute threshold would just be measuring
    which end of the bar is better lit.
    """
    rows, cols = gray.shape[:2]
    inner = max(3.0, radius_px)
    outer = max(inner * 3.0, inner + 6.0)
    reach = int(np.ceil(outer))
    ys, xs = np.ogrid[-reach:reach + 1, -reach:reach + 1]
    distance = np.hypot(xs, ys)
    disc = distance <= inner
    annulus = (distance > inner * 1.6) & (distance <= outer)

    total = 0.0
    for x, y in points:
        cx, cy = int(round(x)), int(round(y))
        if not (reach <= cx < cols - reach and reach <= cy < rows - reach):
            continue
        window = gray[cy - reach:cy + reach + 1, cx - reach:cx + reach + 1]
        around = float(np.median(window[annulus]))
        if around <= 1e-6:
            continue
        total += (float(np.percentile(window[disc], 10)) - around) / around
    return total
