"""Lens calibration, against synthetic views with known intrinsics."""

import math

import numpy as np
import pytest

from acme.lens import board_points, calibrate, find_board, undistort_points

cv2 = pytest.importorskip("cv2")

COLUMNS, ROWS, SQUARE_MM = 9, 6, 20.0
SIZE = (1280, 960)
TRUE_K = np.array([[1100.0, 0.0, 640.0],
                   [0.0, 1100.0, 480.0],
                   [0.0, 0.0, 1.0]])
TRUE_DIST = np.array([-0.22, 0.09, 0.0, 0.0, 0.0])


def _render(rotation, translation, distort=True):
    """A checkerboard view, rendered backwards through the lens model.

    For each pixel of the *distorted* output, undistort it to ideal
    coordinates, carry that back to the board plane through the pose
    homography, and read the pattern there.  Going this way round means
    the distortion applied is exactly the model being tested, rather
    than an approximation of its inverse.
    """
    rvec = np.asarray(rotation, float).reshape(3, 1)
    tvec = np.asarray(translation, float).reshape(3, 1)
    rot, _ = cv2.Rodrigues(rvec)
    plane = TRUE_K @ np.column_stack([rot[:, 0], rot[:, 1], tvec.ravel()])

    width, height = SIZE
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float64)
    pixels = np.column_stack([xs.ravel(), ys.ravel()])
    ideal = (undistort_points(pixels, TRUE_K, TRUE_DIST) if distort
             else pixels)

    homo = np.column_stack([ideal, np.ones(len(ideal))])
    board = homo @ np.linalg.inv(plane).T
    w = board[:, 2:3]
    w[np.abs(w) < 1e-12] = 1e-12
    bx = (board[:, 0] / w[:, 0]).reshape(height, width)
    by = (board[:, 1] / w[:, 0]).reshape(height, width)

    checker = ((np.floor(bx / SQUARE_MM) + np.floor(by / SQUARE_MM)) % 2)
    inside = ((bx > -SQUARE_MM) & (bx < COLUMNS * SQUARE_MM)
              & (by > -SQUARE_MM) & (by < ROWS * SQUARE_MM))
    return np.where(inside, 0.15 + 0.7 * checker, 0.5)


# Tilted views pin the focal length; views that push the board into the
# frame CORNERS are what pin radial distortion, because that is the only
# place it is large enough to measure.  With centred views only, k1 came
# back as -0.17 against a true -0.22 -- which is the same mistake as
# calibrating a real camera without moving the board to the edges, and
# the reason the node's tooltip says to.
POSES = [
    ((0.0, 0.0, 0.0), (-90.0, -60.0, 420.0)),
    ((0.28, 0.0, 0.0), (-90.0, -55.0, 430.0)),
    ((-0.26, 0.0, 0.0), (-88.0, -62.0, 415.0)),
    ((0.0, 0.30, 0.0), (-95.0, -58.0, 425.0)),
    ((0.0, -0.28, 0.05), (-86.0, -60.0, 410.0)),
    ((0.20, 0.20, 0.0), (-92.0, -57.0, 440.0)),
    ((-0.18, -0.22, -0.05), (-89.0, -61.0, 405.0)),
    ((0.10, 0.12, 0.0), (-239.0, -138.0, 420.0)),
    ((-0.12, 0.10, 0.0), (59.0, -138.0, 420.0)),
    ((0.12, -0.10, 0.0), (-239.0, 38.0, 420.0)),
    ((-0.10, -0.12, 0.03), (59.0, 38.0, 420.0)),
    ((0.0, 0.0, 0.15), (-235.0, 30.0, 415.0)),
    ((0.0, 0.0, -0.15), (55.0, -132.0, 425.0)),
]


def test_board_is_found_in_a_distorted_view():
    corners = find_board(_render(*POSES[0]), COLUMNS, ROWS)
    assert corners is not None
    assert corners.shape == (COLUMNS * ROWS, 2)


def test_board_points_are_a_planar_grid():
    grid = board_points(COLUMNS, ROWS, SQUARE_MM)
    assert grid.shape == (COLUMNS * ROWS, 3)
    assert np.allclose(grid[:, 2], 0.0)
    assert math.isclose(float(np.ptp(grid[:, 0])),
                        (COLUMNS - 1) * SQUARE_MM)


def test_intrinsics_and_distortion_are_recovered():
    frames = [_render(r, t) for r, t in POSES]
    matrix, dist, rms, used, skipped = calibrate(
        frames, COLUMNS, ROWS, SQUARE_MM)
    assert len(used) >= 5, f"only found the board in {len(used)} views"
    assert rms < 1.0, f"reprojection rms {rms:.3f} px"
    assert abs(matrix[0, 0] - TRUE_K[0, 0]) / TRUE_K[0, 0] < 0.03
    assert abs(matrix[1, 1] - TRUE_K[1, 1]) / TRUE_K[1, 1] < 0.03
    assert abs(matrix[0, 2] - TRUE_K[0, 2]) < 25
    assert abs(matrix[1, 2] - TRUE_K[1, 2]) < 25
    assert abs(dist[0] - TRUE_DIST[0]) < 0.05, f"k1 {dist[0]:.3f}"


def test_undistortion_actually_straightens_a_line():
    """The point of the exercise: collinear world points must come back
    collinear.  On a 1280 px frame this distortion bows them by tens of
    pixels, which is exactly the magnitude that would otherwise land in
    the registration residual."""
    xs = np.linspace(100, 1180, 40)
    straight = np.column_stack([xs, np.full_like(xs, 120.0)])
    bent = cv2.projectPoints(
        np.column_stack([(straight - TRUE_K[:2, 2]) / TRUE_K[[0, 1], [0, 1]],
                         np.ones(len(xs))]).astype(np.float64),
        np.zeros(3), np.zeros(3), TRUE_K, TRUE_DIST)[0].reshape(-1, 2)

    def bow(points):
        a, b = points[0], points[-1]
        d = (b - a) / np.linalg.norm(b - a)
        rel = points - a
        # 2-D cross product by hand; numpy 2 dropped the 2-vector case.
        return float(np.abs(d[0] * rel[:, 1] - d[1] * rel[:, 0]).max())

    assert bow(bent) > 10.0, (
        "the test distortion is too mild to prove anything")
    assert bow(undistort_points(bent, TRUE_K, TRUE_DIST)) < 0.5


def test_too_few_views_is_refused():
    with pytest.raises(ValueError, match="at least 3"):
        calibrate([_render(*POSES[0])], COLUMNS, ROWS, SQUARE_MM)


def test_wrong_board_size_says_so_usefully():
    frames = [_render(r, t) for r, t in POSES[:4]]
    with pytest.raises(ValueError, match="inner-corner"):
        calibrate(frames, COLUMNS + 2, ROWS + 2, SQUARE_MM)
