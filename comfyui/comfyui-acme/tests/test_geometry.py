"""Geometry: the claims the design rests on."""

import math
import numpy as np
import pytest

from acme.geometry import (apply_homography, homography_from_points,
                           fit_line, line_intersection, residuals,
                           rigid_from_points, rms)


def test_homography_recovers_a_known_transform():
    src = np.array([[0.0, 0.0], [100.0, 0.0], [100.0, 50.0], [0.0, 50.0]])
    truth = np.array([[1.2, 0.1, 30.0],
                      [-0.05, 0.9, -12.0],
                      [3e-4, -1e-4, 1.0]])
    dst = apply_homography(truth, src)
    found = homography_from_points(src, dst)
    assert np.allclose(apply_homography(found, src), dst, atol=1e-8)


def test_collinear_points_are_refused():
    """The claim the whole two-stage design rests on: three collinear
    points -- which is exactly what the ACME pegs are -- cannot
    determine a homography, and a fourth on the same line does not
    help."""
    src = np.array([[0.0, 0.0], [10.0, 0.0], [20.0, 0.0], [30.0, 0.0]])
    dst = np.array([[1.0, 1.0], [11.0, 1.0], [21.0, 1.0], [31.0, 1.0]])
    with pytest.raises((ValueError, np.linalg.LinAlgError)):
        h = homography_from_points(src, dst)
        # If it returns at all, it must not be a usable transform: a
        # point off the line is unconstrained, so round-tripping one
        # cannot be expected to work.
        off_line = np.array([[15.0, 7.0]])
        assert np.allclose(apply_homography(h, off_line), off_line)


def test_rigid_fit_has_no_scale_freedom():
    """Scale must not be absorbed: a uniformly expanded point set should
    leave residual, not be fitted away.  Letting it through would let
    detection error quietly shrink the drawing."""
    src = np.array([[-100.0, 0.0], [0.0, 0.0], [100.0, 0.0]])
    dst = src * 1.02
    transform = rigid_from_points(src, dst)
    assert np.isclose(np.linalg.det(transform[:2, :2]), 1.0, atol=1e-9)
    assert rms(residuals(transform, src, dst)) > 1.0


def test_rigid_fit_recovers_rotation_and_translation():
    theta = math.radians(3.0)
    rot = np.array([[math.cos(theta), -math.sin(theta)],
                    [math.sin(theta), math.cos(theta)]])
    src = np.array([[-101.6, 0.0], [0.0, 0.0], [101.6, 0.0]])
    dst = src @ rot.T + np.array([0.4, -0.25])
    transform = rigid_from_points(src, dst)
    assert rms(residuals(transform, src, dst)) < 1e-9
    assert math.isclose(
        math.degrees(math.atan2(transform[1, 0], transform[0, 0])),
        3.0, abs_tol=1e-6)


def test_line_fit_survives_a_vertical_edge():
    """Total least squares, not y-on-x: a sheet edge is near-vertical as
    often as near-horizontal."""
    ys = np.linspace(0, 1000, 400)
    pts = np.column_stack([np.full_like(ys, 512.0), ys])
    origin, direction = fit_line(pts)
    assert abs(abs(direction[1]) - 1.0) < 1e-9
    assert abs(origin[0] - 512.0) < 1e-9


def test_line_intersection_rejects_parallels():
    with pytest.raises(ValueError):
        line_intersection(np.array([0.0, 0.0]), np.array([1.0, 0.0]),
                          np.array([0.0, 5.0]), np.array([1.0, 0.0]))
