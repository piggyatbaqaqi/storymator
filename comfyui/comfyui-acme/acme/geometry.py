"""Plane geometry for registration: lines, homographies, rigid fits.

Plain numpy on purpose.  None of this imports ComfyUI or torch, so the
acceptance harness and the tests can call it directly, and so it can be
reasoned about without a graph running.

Two numpy-2 traps are worked around here rather than in every caller:
``ndarray.ptp`` was removed, and ``np.cross`` no longer accepts
2-vectors.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np


def cross2(a: np.ndarray, b: np.ndarray) -> float:
    """2-D cross product; numpy 2 dropped the 2-vector case of np.cross."""
    return float(a[0] * b[1] - a[1] * b[0])


def fit_line(points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Total-least-squares line through Nx2 points -> (origin, unit dir).

    TLS rather than a y-on-x least squares, because a sheet edge is
    near-vertical as often as near-horizontal and the ordinary fit
    degenerates on one of them.
    """
    points = np.asarray(points, dtype=float)
    origin = points.mean(axis=0)
    _, _, vh = np.linalg.svd(points - origin, full_matrices=False)
    direction = vh[0]
    return origin, direction / np.linalg.norm(direction)


def line_intersection(o1: np.ndarray, d1: np.ndarray,
                      o2: np.ndarray, d2: np.ndarray) -> np.ndarray:
    """Intersection of two parametric lines. Raises if near-parallel."""
    a = np.array([d1, -d2], dtype=float).T
    if abs(np.linalg.det(a)) < 1e-9:
        raise ValueError("lines are parallel; no intersection")
    t = np.linalg.solve(a, np.asarray(o2, float) - np.asarray(o1, float))
    return np.asarray(o1, float) + t[0] * np.asarray(d1, float)


def point_line_distance(point: np.ndarray, a: np.ndarray,
                        b: np.ndarray) -> float:
    """Perpendicular distance from `point` to the segment's infinite line."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    return abs(cross2(b - a, np.asarray(point, float) - a)) / np.linalg.norm(b - a)


# ---------------------------------------------------------------------
# homography
# ---------------------------------------------------------------------

def _normalising_transform(points: np.ndarray) -> np.ndarray:
    """Hartley normalisation: centroid to origin, mean distance to sqrt(2).

    Without it the DLT's design matrix mixes terms of order 1 with terms
    of order 10^6 and the SVD loses most of its precision.
    """
    centroid = points.mean(axis=0)
    shifted = points - centroid
    mean_dist = np.sqrt((shifted ** 2).sum(axis=1)).mean()
    scale = np.sqrt(2.0) / mean_dist if mean_dist > 0 else 1.0
    return np.array([
        [scale, 0.0, -scale * centroid[0]],
        [0.0, scale, -scale * centroid[1]],
        [0.0, 0.0, 1.0],
    ], dtype=float)


def homography_from_points(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """3x3 homography mapping src -> dst, from 4 or more correspondences.

    Four points in **general position** are required.  Collinear points
    do not constrain a homography -- three points on a line fix a
    projective frame on that line and leave a three-parameter family
    open -- which is precisely why the registration fit takes its
    homography from the sheet outline and not from the pegs.
    """
    src = np.asarray(src, dtype=float)
    dst = np.asarray(dst, dtype=float)
    if src.shape != dst.shape or src.shape[0] < 4 or src.shape[1] != 2:
        raise ValueError("need matching Nx2 arrays with N >= 4")

    t_src = _normalising_transform(src)
    t_dst = _normalising_transform(dst)
    src_n = apply_homography(t_src, src)
    dst_n = apply_homography(t_dst, dst)

    rows = []
    for (x, y), (u, v) in zip(src_n, dst_n):
        rows.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        rows.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, vh = np.linalg.svd(np.array(rows, dtype=float))
    h_n = vh[-1].reshape(3, 3)

    h = np.linalg.inv(t_dst) @ h_n @ t_src
    if abs(h[2, 2]) < 1e-12:
        raise ValueError("degenerate homography; are the points collinear?")
    return h / h[2, 2]


def apply_homography(h: np.ndarray, points: np.ndarray) -> np.ndarray:
    """Map Nx2 points through a 3x3 homography."""
    points = np.atleast_2d(np.asarray(points, dtype=float))
    homo = np.column_stack([points, np.ones(len(points))])
    out = homo @ np.asarray(h, dtype=float).T
    w = out[:, 2:3]
    if np.any(np.abs(w) < 1e-12):
        raise ValueError("point maps to infinity under this homography")
    return out[:, :2] / w


# ---------------------------------------------------------------------
# rigid fit
# ---------------------------------------------------------------------

def rigid_from_points(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """3x3 rotation+translation taking src onto dst, in the least-squares
    sense.  Kabsch, in two dimensions.

    **Scale is deliberately not a free parameter.**  The correction this
    computes is the small in-plane disagreement between where the pegs
    are observed and where the model says they are; letting it absorb
    scale would let detection error quietly shrink the drawing, which
    looks like nothing and corrupts every spacing measurement
    downstream.
    """
    src = np.asarray(src, dtype=float)
    dst = np.asarray(dst, dtype=float)
    if src.shape != dst.shape or src.shape[0] < 2:
        raise ValueError("need matching Nx2 arrays with N >= 2")

    c_src = src.mean(axis=0)
    c_dst = dst.mean(axis=0)
    cov = (src - c_src).T @ (dst - c_dst)
    u, _, vt = np.linalg.svd(cov)
    d = np.sign(np.linalg.det(vt.T @ u.T))
    rot = vt.T @ np.diag([1.0, d]) @ u.T
    trans = c_dst - rot @ c_src

    out = np.eye(3)
    out[:2, :2] = rot
    out[:2, 2] = trans
    return out


def residuals(transform: np.ndarray, src: np.ndarray,
              dst: np.ndarray) -> np.ndarray:
    """Per-point distance between transform(src) and dst."""
    mapped = apply_homography(transform, src)
    return np.linalg.norm(mapped - np.asarray(dst, dtype=float), axis=1)


def rms(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    return float(np.sqrt((values ** 2).mean())) if values.size else 0.0
