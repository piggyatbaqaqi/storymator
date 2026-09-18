"""ChArUco calibration, against synthetic views with known intrinsics.

ChArUco rather than a plain checkerboard because every corner carries
an identity, so a partly visible or partly occluded board still
contributes -- which is exactly the board you get when pushing it into
the frame corners, and the corners are where distortion is measurable.
"""

import numpy as np
import pytest

from acme.lens import (calibrate_charuco, charuco_board, find_charuco,
                       undistort_points)

cv2 = pytest.importorskip("cv2")

COLUMNS, ROWS, SQUARE_MM, MARKER_MM = 7, 9, 25.0, 18.0
SIZE = (1280, 960)
TRUE_K = np.array([[1150.0, 0.0, 632.0],
                   [0.0, 1150.0, 474.0],
                   [0.0, 0.0, 1.0]])
TRUE_DIST = np.array([-0.20, 0.07, 0.0, 0.0, 0.0])

BOARD = charuco_board(COLUMNS, ROWS, SQUARE_MM, MARKER_MM)
_PX_PER_MM = 6.0
_BITMAP = BOARD.generateImage(
    (int(COLUMNS * SQUARE_MM * _PX_PER_MM),
     int(ROWS * SQUARE_MM * _PX_PER_MM)))


def _render(rotation, translation):
    """One view, rendered backwards through the lens model."""
    rot, _ = cv2.Rodrigues(np.asarray(rotation, float).reshape(3, 1))
    tvec = np.asarray(translation, float)
    plane = TRUE_K @ np.column_stack([rot[:, 0], rot[:, 1], tvec])

    width, height = SIZE
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float64)
    ideal = undistort_points(
        np.column_stack([xs.ravel(), ys.ravel()]), TRUE_K, TRUE_DIST)
    homo = np.column_stack([ideal, np.ones(len(ideal))])
    board_mm = homo @ np.linalg.inv(plane).T
    w = board_mm[:, 2:3]
    w[np.abs(w) < 1e-12] = 1e-12

    bx = (board_mm[:, 0] / w[:, 0]) * _PX_PER_MM
    by = (board_mm[:, 1] / w[:, 0]) * _PX_PER_MM
    inside = ((bx >= 0) & (bx < _BITMAP.shape[1] - 1)
              & (by >= 0) & (by < _BITMAP.shape[0] - 1))
    out = np.full(bx.shape, 200.0)
    out[inside] = _BITMAP[by[inside].astype(int), bx[inside].astype(int)]
    return (out.reshape(height, width) / 255.0)


# Closer than the checkerboard poses (the board fills more frame, which
# is better calibration practice) and the last six push it far enough
# that part of it leaves the frame -- which is the case ChArUco exists
# to handle, and where distortion is actually measurable.
POSES = [
    ((0.0, 0.0, 0.0), (-88.0, -113.0, 450.0)),
    ((0.26, 0.0, 0.0), (-88.0, -108.0, 460.0)),
    ((-0.24, 0.0, 0.0), (-86.0, -115.0, 445.0)),
    ((0.0, 0.28, 0.0), (-93.0, -111.0, 455.0)),
    ((0.0, -0.26, 0.04), (-84.0, -113.0, 440.0)),
    ((0.18, 0.18, 0.0), (-90.0, -110.0, 470.0)),
    ((0.12, 0.10, 0.0), (-276.0, -239.0, 450.0)),
    ((-0.14, 0.12, 0.0), (107.0, -239.0, 450.0)),
    ((0.14, -0.12, 0.0), (-276.0, 19.0, 450.0)),
    ((-0.12, -0.14, 0.03), (107.0, 19.0, 450.0)),
    ((0.0, 0.0, 0.14), (-270.0, 14.0, 445.0)),
    ((0.0, 0.0, -0.14), (102.0, -234.0, 455.0)),
]


def test_board_is_found_and_corners_are_identified():
    corners, ids = find_charuco(_render(*POSES[0]), BOARD)
    assert corners is not None
    assert len(ids) > 20
    # ids are unique and within the board's corner count
    assert len(set(ids.tolist())) == len(ids)
    assert ids.max() < (COLUMNS - 1) * (ROWS - 1)


def test_a_partly_visible_board_still_contributes():
    """The reason for using ChArUco at all: a board pushed off the edge
    of the frame is still usable, and those are the views that pin
    distortion down."""
    corners, ids = find_charuco(_render(*POSES[6]), BOARD)
    assert corners is not None
    full = len(find_charuco(_render(*POSES[0]), BOARD)[1])
    assert 6 <= len(ids) < full


def test_intrinsics_and_distortion_are_recovered():
    frames = [_render(r, t) for r, t in POSES]
    matrix, dist, rms, used, skipped = calibrate_charuco(frames, BOARD)
    assert len(used) >= 8, f"board found in only {len(used)} views"
    assert rms < 1.0, f"reprojection rms {rms:.3f} px"
    assert abs(matrix[0, 0] - TRUE_K[0, 0]) / TRUE_K[0, 0] < 0.03
    assert abs(matrix[0, 2] - TRUE_K[0, 2]) < 30
    assert abs(dist[0] - TRUE_DIST[0]) < 0.05, f"k1 {dist[0]:.3f}"


def test_square_size_does_not_change_the_intrinsics():
    """Scaling the board scales the extrinsics and nothing else, so a
    print that came out 7 % large still calibrates the lens correctly.
    Worth pinning down: it is the difference between 'measure the board
    first' and 'the print scale does not matter here'."""
    frames = [_render(r, t) for r, t in POSES]
    truth, _, _, _, _ = calibrate_charuco(frames, BOARD)
    wrong = charuco_board(COLUMNS, ROWS, SQUARE_MM * 1.069,
                          MARKER_MM * 1.069)
    scaled, _, _, _, _ = calibrate_charuco(frames, wrong)
    assert np.allclose(truth, scaled, rtol=1e-6), (
        "intrinsics moved when only the assumed square size changed")


def test_too_few_views_is_refused():
    with pytest.raises(ValueError, match="at least 3"):
        calibrate_charuco([_render(*POSES[0])], BOARD)
