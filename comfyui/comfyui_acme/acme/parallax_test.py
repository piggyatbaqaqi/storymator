"""Parallax on landmarks that stand above the paper.

Every number here was measured on honbay_0001 and v4k_01; see
data/calibration/pegs/honbay_0001/README.md.
"""

import numpy as np
import pytest

from acme.parallax import correct_parallax, working_distance_mm

pending = pytest.mark.xfail(reason="parallax correction not implemented")

FX, CX, CY = 2625.44, 1640.2, 1204.2
K = np.array([[FX, 0.0, CX], [0.0, FX, CY], [0.0, 0.0, 1.0]])
PX_PER_MM = 8.59                      # at the paper, on the measured frame
Z = FX / PX_PER_MM                    # 305.6 mm
ROUND_H = 5.567                       # sphere centre above the paper


@pending
def test_working_distance_is_focal_length_over_scale():
    assert working_distance_mm(K, PX_PER_MM) == pytest.approx(Z, rel=1e-9)


# --- what must not move ---------------------------------------------

@pending
def test_a_landmark_in_the_paper_plane_is_untouched():
    """The rect landmarks are holes. h = 0, and nothing happens."""
    pts = np.array([[500.0, 900.0], [2800.0, 2100.0]])
    out = correct_parallax(pts, [0.0, 0.0], K, PX_PER_MM)
    assert np.allclose(out, pts)


@pending
def test_a_landmark_on_the_optical_axis_is_untouched():
    """Height only matters off-axis: straight down the axis a raised
    point projects to the same place as its footprint."""
    pts = np.array([[CX, CY]])
    out = correct_parallax(pts, [ROUND_H], K, PX_PER_MM)
    assert np.allclose(out, pts, atol=1e-9)


@pending
def test_without_intrinsics_nothing_is_corrected():
    """No principal point and no working distance, so no correction --
    the same way distortion is skipped when OpenCV is absent."""
    pts = np.array([[1878.0, 2202.0]])
    assert np.allclose(correct_parallax(pts, [ROUND_H], None, PX_PER_MM), pts)


# --- the correction itself -------------------------------------------

@pending
def test_the_shift_is_r_times_h_over_z():
    """Stated in terms of the OBSERVED radius, which is what a detector
    hands you."""
    pts = np.array([[CX + 1000.0, CY]])
    out = correct_parallax(pts, [ROUND_H], K, PX_PER_MM)
    r_mm = 1000.0 / PX_PER_MM
    assert (1000.0 - (out[0, 0] - CX)) / PX_PER_MM == pytest.approx(
        r_mm * ROUND_H / Z, rel=1e-6)


@pending
def test_the_shift_points_at_the_principal_point():
    """Inward, radially -- not along an image axis."""
    for offset in ([+700.0, +900.0], [-700.0, +900.0], [+700.0, -900.0]):
        pts = np.array([[CX + offset[0], CY + offset[1]]])
        out = correct_parallax(pts, [ROUND_H], K, PX_PER_MM)
        before, after = pts[0] - [CX, CY], out[0] - [CX, CY]
        assert np.linalg.norm(after) < np.linalg.norm(before)
        # same direction, shorter
        assert np.allclose(after / np.linalg.norm(after),
                           before / np.linalg.norm(before), atol=1e-9)


@pending
def test_heights_are_applied_per_landmark():
    """The round peg is raised and the rect holes are not, so only one
    of the three may move."""
    pts = np.array([[961.0, 2102.0], [1878.0, 2202.0], [2687.0, 2269.0]])
    out = correct_parallax(pts, [0.0, ROUND_H, 0.0], K, PX_PER_MM)
    assert np.allclose(out[0], pts[0])
    assert np.allclose(out[2], pts[2])
    assert not np.allclose(out[1], pts[1])


# --- the thing it is for ----------------------------------------------

@pending
def test_correcting_the_round_landmark_restores_equal_spacing():
    """The end-to-end claim, on a synthetic rig with known truth.

    Three collinear landmarks 101.62 mm apart in the paper plane. Raise
    the middle one to the dome's centre height and re-project: the two
    gaps stop being equal, which is exactly what the rig showed --
    104.13 and 99.34 mm against 101.62, errors +2.51 and -2.28 summing
    to +0.24, one landmark displaced and two clean.

    The correction must put them back.
    """
    spacing, off_axis = 101.62, 119.0     # mm; the rig's round landmark
    x_mm = np.array([-spacing, 0.0, spacing]) + off_axis
    y_mm = np.full(3, 40.0)
    heights = np.array([0.0, ROUND_H, 0.0])
    # a raised point projects as though it were further out by Z/(Z-h)
    k = Z / (Z - heights)
    pts = np.stack([CX + x_mm * k * PX_PER_MM,
                    CY + y_mm * k * PX_PER_MM], axis=1)

    raw = np.abs(np.diff(pts[:, 0])) / PX_PER_MM
    assert abs(raw[0] - raw[1]) > 2.0, "the synthetic case must be skewed"

    out = correct_parallax(pts, heights, K, PX_PER_MM)
    gaps = np.linalg.norm(np.diff(out, axis=0), axis=1) / PX_PER_MM
    assert gaps[0] == pytest.approx(spacing, abs=0.05)
    assert gaps[1] == pytest.approx(spacing, abs=0.05)


@pending
def test_the_measured_rig_case_predicts_what_was_observed():
    """119 mm off-axis at Z = 306 predicted 2.2 mm; 2.43 was seen.

    Also pins that the dome's APEX is the wrong height to use: it
    predicts 3.53 mm, which does not fit.
    """
    pts = np.array([[CX + 119.0 * PX_PER_MM, CY]])
    for h, expected in ((ROUND_H, 2.2), (8.787, 3.5)):
        out = correct_parallax(pts, [h], K, PX_PER_MM)
        shift = (pts[0, 0] - out[0, 0]) / PX_PER_MM
        assert shift == pytest.approx(expected, abs=0.1)
