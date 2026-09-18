"""Finding the sheet and the pegs in a captured frame.

Detection here is a *proposal* stage only.  It over-generates
deliberately; :mod:`acme.fit` does the deciding by testing candidates
against the known bar geometry.  That split is the whole robustness
story: on a sheet of artwork, any blob detector will happily return
eyes, knuckles and hatching in the same size range as a peg, and no
amount of threshold tuning fixes that.  Only the model does.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from scipy import ndimage

from .geometry import fit_line, line_intersection


@dataclass
class Blob:
    """A peg candidate, in image pixels."""
    x: float
    y: float
    area_px: float
    short_px: float
    long_px: float

    @property
    def centre(self) -> np.ndarray:
        return np.array([self.x, self.y], dtype=float)

    @property
    def elongation(self) -> float:
        return self.long_px / max(self.short_px, 1e-9)


def bimodal_threshold(gray: np.ndarray, low: float = 2.0,
                      high: float = 98.0) -> float:
    """Midpoint between the dark and bright populations.

    Otsu is the reflex choice here and it is the wrong one.  A frame of
    paper against a contrasting ground has a wide empty gap between its
    two modes, and Otsu's between-class variance is *identical* for
    every threshold inside that gap -- so ``argmax`` returns whichever
    bin floating-point noise happens to favour, which is arbitrary and,
    when it lands at the end of the range, catastrophic.

    A percentile midpoint has no such indifference, costs less, tracks
    exposure (a dim capture moves both percentiles and the midpoint
    with them), and is trivial to reason about when a frame misbehaves.
    """
    lo = float(np.percentile(gray, low))
    hi = float(np.percentile(gray, high))
    if hi - lo < 0.1:
        raise ValueError(
            f"no contrast  the frame spans only {hi - lo:.2f} between its "
            f"{low:g}th and {high:g}th percentiles; sheet and surround are "
            f"not separable")
    return (lo + hi) / 2.0


def largest_component(mask: np.ndarray) -> np.ndarray:
    labels, n = ndimage.label(mask)
    if n == 0:
        raise ValueError("nothing found")
    sizes = ndimage.sum(mask, labels, range(1, n + 1))
    return labels == (int(np.argmax(sizes)) + 1)


def find_sheet(gray: np.ndarray,
               threshold: Optional[float] = None) -> np.ndarray:
    """Filled mask of the sheet: the largest bright region.

    The sheet is assumed brighter than its surroundings, which holds for
    paper on a desk and for paper on the black card the bench procedure
    calls for.  Backlit capture inverts that; pass an explicit threshold
    and a pre-inverted image.
    """
    level = bimodal_threshold(gray) if threshold is None else threshold
    return ndimage.binary_fill_holes(largest_component(gray > level))


def _principal_angle(mask: np.ndarray) -> float:
    """Orientation of the sheet, from the second moments of its area."""
    ys, xs = np.nonzero(mask)
    pts = np.column_stack([xs, ys]).astype(float)
    cov = np.cov((pts - pts.mean(axis=0)).T)
    _, evecs = np.linalg.eigh(cov)
    major = evecs[:, -1]
    # eigh's eigenvector signs are arbitrary.  Left alone, the local
    # frame flips at random between frames, which reverses the winding
    # of the corners this function is used to order -- and a reversed
    # winding is a mirrored sheet, which no homography should ever be
    # asked to fit.  Pin the major axis to the right half-plane.
    if major[0] < 0 or (major[0] == 0 and major[1] < 0):
        major = -major
    return float(np.arctan2(major[1], major[0]))


def _refine_edge(gray: np.ndarray, origin: np.ndarray, direction: np.ndarray,
                 extent: float, search_px: float = 4.0,
                 samples: int = 200) -> Optional[np.ndarray]:
    """Sub-pixel edge points, from the gradient across the edge.

    A mask boundary sits half a pixel inside the true edge, on every
    side, which shrinks the detected sheet by about a pixel in each
    dimension.  That is a 0.13 % scale error on a 765 px sheet -- and
    **the peg stage cannot absorb it**, because that fit is rigid and
    has no scale freedom by design.  So the outline has to be right to
    sub-pixel before it is handed on.

    The edge is located as the centroid of the intensity gradient along
    the surface normal, which is unbiased for a symmetric edge profile
    whatever the threshold happened to be.
    """
    normal = np.array([-direction[1], direction[0]])
    ts = np.linspace(-extent / 2, extent / 2, samples)
    offsets = np.arange(-search_px, search_px + 0.25, 0.25)

    along = origin[None, :] + ts[:, None] * direction[None, :]
    probe = along[:, None, :] + offsets[None, :, None] * normal[None, None, :]
    values = ndimage.map_coordinates(
        gray, [probe[..., 1].ravel(), probe[..., 0].ravel()],
        order=1, mode="nearest").reshape(len(ts), len(offsets))

    weights = np.abs(np.gradient(values, axis=1))
    total = weights.sum(axis=1)
    good = total > 1e-6
    if good.sum() < samples // 4:
        return None
    centre = (weights[good] * offsets[None, :]).sum(axis=1) / total[good]
    # A crossing pinned to the end of the search window is not a
    # crossing; it means the edge was not inside the window.
    inside = np.abs(centre) < search_px - 0.3
    if inside.sum() < samples // 4:
        return None
    return along[good][inside] + centre[inside, None] * normal[None, :]


def sheet_corners(mask: np.ndarray, gray: Optional[np.ndarray] = None,
                  return_samples: bool = False):
    """Four corners, as the intersections of four fitted edges.

    Corners are never located directly.  A punched sheet's corner is
    rounded and is often dog-eared, while each edge carries thousands of
    pixels of evidence; the middle 80 % of each side is fitted so that
    corner rounding is excluded from the fit that defines it.

    Sides are assigned in the **sheet's own frame**, found from the
    mask's principal axes, rather than in image axes.  An image-axis
    assignment silently mis-sorts points near the corners as soon as the
    sheet is rotated, and collapses entirely past about 20 degrees --
    which is an ordinary camera placement, not an edge case.

    Pass ``gray`` to refine the edges to sub-pixel; see
    :func:`_refine_edge` for why that is required rather than optional.

    Returns (4, 2) image points, in cyclic order.  With
    ``return_samples``, also the edge points the fit used -- which are
    what makes a *meaningful* outline residual possible: a homography
    from exactly four corners fits those four corners exactly, so their
    residual is identically zero and measures nothing.  Hundreds of
    points along the edges over-determine it, and their scatter is
    paper curl and lens distortion made visible.
    """
    eroded = ndimage.binary_erosion(mask, iterations=1)
    ys, xs = np.nonzero(mask & ~eroded)
    pts = np.column_stack([xs, ys]).astype(float)
    centre = pts.mean(axis=0)

    theta = _principal_angle(mask)
    rot = np.array([[np.cos(-theta), -np.sin(-theta)],
                    [np.sin(-theta), np.cos(-theta)]])
    local = (pts - centre) @ rot.T

    lengthwise = np.abs(local[:, 0]) > np.abs(local[:, 1])
    groups = {
        "minus_u": (lengthwise & (local[:, 0] < 0), 1),
        "plus_u": (lengthwise & (local[:, 0] > 0), 1),
        "minus_v": (~lengthwise & (local[:, 1] < 0), 0),
        "plus_v": (~lengthwise & (local[:, 1] > 0), 0),
    }

    fits = {}
    samples = {}
    for name, (selector, axis) in groups.items():
        side = pts[selector]
        side_local = local[selector]
        if len(side) < 50:
            raise ValueError(f"only {len(side)} boundary points on the "
                             f"{name} edge; is the sheet fully in frame?")
        lo, hi = np.percentile(side_local[:, axis], [10, 90])
        keep = (side_local[:, axis] >= lo) & (side_local[:, axis] <= hi)
        origin, direction = fit_line(side[keep])
        samples[name] = side[keep]
        if gray is not None:
            refined = _refine_edge(gray, origin, direction, extent=(hi - lo))
            if refined is not None:
                origin, direction = fit_line(refined)
                samples[name] = refined
        fits[name] = (origin, direction)

    corners = np.array([
        line_intersection(*fits["minus_v"], *fits["minus_u"]),
        line_intersection(*fits["minus_v"], *fits["plus_u"]),
        line_intersection(*fits["plus_v"], *fits["plus_u"]),
        line_intersection(*fits["plus_v"], *fits["minus_u"]),
    ])
    if return_samples:
        return corners, samples
    return corners


def find_peg_candidates(gray: np.ndarray, sheet: np.ndarray,
                        min_area_px: float, max_area_px: float,
                        polarity: str = "dark",
                        threshold: Optional[float] = None,
                        contrast: float = 0.6) -> List[Blob]:
    """Compact regions inside the sheet that could be pegs.

    ``polarity`` is a rig property rather than a tuning knob.  A sheet
    lifted off the bar shows its punched holes, which read dark; a sheet
    sitting on the bar shows the peg tops, which may read either way
    depending on how they are lit.  Both are supported and neither is
    guessed at.

    Deliberately permissive: the area window spans an order of
    magnitude, because rejecting a real peg here is unrecoverable
    whereas admitting a knuckle is not -- the model test in
    :func:`acme.fit.select_peg_triple` removes it.
    """
    if polarity not in ("dark", "bright"):
        raise ValueError("polarity must be 'dark' or 'bright'")

    inside = ndimage.binary_erosion(sheet, iterations=2)
    values = gray[inside]

    # Threshold relative to the paper level rather than by splitting the
    # histogram.  The pegs are roughly 0.2 % of the sheet's area, and at
    # that imbalance there is no meaningful second mode to find -- the
    # histogram is the paper distribution with a negligible smear
    # beside it, so any split-the-modes method is really choosing where
    # to cut the paper.  The paper level itself is the robust thing to
    # measure, and keying off it tracks exposure for free: a dim capture
    # moves the median and the threshold with it.
    paper = float(np.median(values))
    if threshold is not None:
        level = threshold
    elif polarity == "dark":
        level = paper * contrast
    else:
        level = paper + (float(np.percentile(values, 99.9)) - paper) \
            * (1.0 - contrast)

    picked = (gray < level) if polarity == "dark" else (gray > level)
    picked &= inside

    coverage = picked.sum() / max(inside.sum(), 1)
    if coverage > 0.25:
        raise ValueError(
            f"exposure  {coverage:.0%} of the sheet is on the peg side of "
            f"the threshold (paper level {paper:.2f}); the frame is "
            f"probably clipped or the polarity is wrong")

    labels, n = ndimage.label(picked)

    blobs: List[Blob] = []
    # find_objects gives each component's bounding box, so the pixel
    # scan is over the blob rather than the whole frame.  Scanning the
    # frame per component is O(components x pixels), which on a noisy
    # capture with thousands of specks is minutes rather than seconds.
    boxes = ndimage.find_objects(labels)
    for index, box in enumerate(boxes, start=1):
        if box is None:
            continue
        window = labels[box] == index
        area = float(window.sum())
        if not (min_area_px <= area <= max_area_px) or area < 4:
            continue
        ys, xs = np.nonzero(window)
        ys = ys + box[0].start
        xs = xs + box[1].start
        pts = np.column_stack([xs, ys]).astype(float)
        centre = pts.mean(axis=0)
        cov = np.cov((pts - centre).T)
        if not np.all(np.isfinite(cov)):
            continue
        _, evecs = np.linalg.eigh(np.atleast_2d(cov))
        extent = np.ptp((pts - centre) @ evecs, axis=0)
        blobs.append(Blob(x=float(centre[0]), y=float(centre[1]),
                          area_px=area,
                          short_px=float(min(extent)),
                          long_px=float(max(extent))))
    return blobs
