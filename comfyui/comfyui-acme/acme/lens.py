"""Lens intrinsics: the one calibration that is worth storing.

Pose is solved per frame from the sheet, so nothing that gets knocked
needs recalibrating.  Intrinsics are different: focal length, principal
point and radial distortion belong to the lens, survive the camera
being moved, and change only if zoom or focus change.  Calibrate once,
tape the focus ring.

Two things they buy:

* **Distortion removal.**  At 4K with a wide lens, uncorrected radial
  distortion is tens of pixels at the frame corners.  That goes
  straight into the registration residual, where it is indistinguishable
  from paper curl.
* **The sheet's aspect ratio.**  A rectangle's proportions *cannot* be
  recovered from a single perspective view without intrinsics --
  measured on the first rig photograph, the along-bar dimension solved
  to 10.63 in whatever perpendicular dimension was assumed, because the
  perpendicular one is simply unconstrained.  With a calibrated camera
  it becomes recoverable.

**OpenCV is imported lazily, inside the functions.**  Everything else
in ``acme`` runs without it, and a pack that fails to import because an
optional dependency is missing is a pack nobody can test.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np


def _cv2():
    try:
        import cv2
    except ModuleNotFoundError as exc:      # pragma: no cover
        raise RuntimeError(
            "lens calibration needs OpenCV: pip install "
            "opencv-contrib-python (see requirements.txt). Registration "
            "itself does not."
        ) from exc
    return cv2


def find_board(gray: np.ndarray, columns: int, rows: int):
    """Inner-corner positions of a checkerboard, to sub-pixel.

    Tries the sector-based detector first: it is markedly better on
    blur and uneven lighting, which is what a desk lamp and a wide-open
    lens deliver.  Falls back to the classic detector plus
    ``cornerSubPix`` when that finds nothing.
    """
    cv2 = _cv2()
    eight = np.clip(gray * 255.0, 0, 255).astype(np.uint8)
    size = (columns, rows)

    found, corners = cv2.findChessboardCornersSB(
        eight, size, flags=cv2.CALIB_CB_EXHAUSTIVE | cv2.CALIB_CB_ACCURACY)
    if found:
        return corners.reshape(-1, 2).astype(np.float64)

    found, corners = cv2.findChessboardCorners(
        eight, size,
        flags=(cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
               | cv2.CALIB_CB_FAST_CHECK))
    if not found:
        return None
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 1e-4)
    refined = cv2.cornerSubPix(eight, corners, (11, 11), (-1, -1), criteria)
    return refined.reshape(-1, 2).astype(np.float64)


def board_points(columns: int, rows: int, square_mm: float) -> np.ndarray:
    grid = np.zeros((rows * columns, 3), dtype=np.float32)
    grid[:, :2] = np.mgrid[0:columns, 0:rows].T.reshape(-1, 2)
    return grid * float(square_mm)


def calibrate(frames: Sequence[np.ndarray], columns: int, rows: int,
              square_mm: float
              ) -> Tuple[np.ndarray, np.ndarray, float, List[int], List[int]]:
    """Intrinsics from several views of a checkerboard.

    Returns ``(camera_matrix, dist_coeffs, rms_px, used, skipped)``.
    ``rms_px`` is OpenCV's reprojection error; under about 0.5 px on a
    dozen well-spread views is healthy, and a figure that will not come
    down usually means the board was not moved enough between shots
    rather than that the lens is bad.
    """
    cv2 = _cv2()
    if len(frames) < 3:
        raise ValueError(f"need at least 3 views, got {len(frames)}")

    objp = board_points(columns, rows, square_mm)
    object_points, image_points, used, skipped = [], [], [], []
    shape = None
    for i, frame in enumerate(frames):
        corners = find_board(frame, columns, rows)
        if corners is None:
            skipped.append(i)
            continue
        shape = frame.shape[1], frame.shape[0]
        object_points.append(objp)
        image_points.append(corners.astype(np.float32))
        used.append(i)

    if len(used) < 3:
        raise ValueError(
            f"found the {columns}x{rows} board in only {len(used)} of "
            f"{len(frames)} views; need 3. Check the inner-corner counts "
            f"-- they are the corners *between* squares, not the squares")

    rms, matrix, dist, _, _ = cv2.calibrateCamera(
        object_points, image_points, shape, None, None)
    return (np.asarray(matrix, float), np.asarray(dist, float).ravel(),
            float(rms), used, skipped)


def undistort_points(points: np.ndarray, camera_matrix: np.ndarray,
                     dist_coeffs: np.ndarray) -> np.ndarray:
    """Map measured pixels to where an ideal lens would have put them.

    Correcting the handful of landmarks rather than resampling the
    whole frame: it is exact, it costs nothing, and it leaves the
    original pixels untouched for the registration warp to sample.
    """
    cv2 = _cv2()
    pts = np.asarray(points, dtype=np.float64).reshape(-1, 1, 2)
    out = cv2.undistortPoints(pts, np.asarray(camera_matrix, float),
                              np.asarray(dist_coeffs, float),
                              P=np.asarray(camera_matrix, float))
    return out.reshape(-1, 2)
