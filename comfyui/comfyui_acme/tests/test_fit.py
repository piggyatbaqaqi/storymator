"""The fit, against synthetic captures with known ground truth."""

import numpy as np
import pytest

from acme.fit import fit_pose
from acme.geometry import apply_homography
from acme.model import Calibration
from acme.synth import camera_homography, render

SIZE = (900, 1100)


def _capture(**kwargs):
    cal = Calibration()
    h = camera_homography(cal, SIZE, **kwargs)
    return cal, h, render(cal, h, SIZE)


def test_square_on_capture_registers():
    cal, truth, image = _capture()
    pose = fit_pose(image, cal)
    assert pose.accepted, pose.reason
    assert pose.peg_residual_px < 1.5


@pytest.mark.parametrize("rotation", [-25.0, -8.0, 8.0, 25.0])
def test_rotation_is_removed(rotation):
    """A rotated capture must land on the same canonical coordinates:
    this is the rev 0 operating mode, where rotation comes from moving
    the camera."""
    cal, truth, image = _capture(rotation_deg=rotation)
    pose = fit_pose(image, cal)
    assert pose.accepted, pose.reason
    # The round peg is the canonical origin, so it must map to (0, 0).
    origin = apply_homography(pose.transform, np.array([[
        *_peg_in_image(truth, cal)]]))[0]
    assert np.linalg.norm(origin) < 0.5      # mm


def _peg_in_image(truth, cal):
    return apply_homography(truth, cal.peg.positions()[1:2])[0]


@pytest.mark.parametrize("tilt", [(2e-4, 0.0), (0.0, 3e-4), (2e-4, -2e-4)])
def test_keystone_is_removed(tilt):
    """Heavy obliquity is wanted by the rig, so the fit must handle a
    genuine projective view rather than assuming the sheet is square-on."""
    cal, truth, image = _capture(tilt=tilt)
    pose = fit_pose(image, cal)
    assert pose.accepted, pose.reason
    assert pose.peg_residual_px < 1.5


def test_registration_is_consistent_across_camera_moves():
    """The property the whole plugin exists to provide: two captures
    from different camera positions must agree in canonical
    coordinates."""
    cal = Calibration()
    probe_mm = np.array([[40.0, 90.0], [-60.0, 150.0]])

    landed = []
    for kwargs in ({"rotation_deg": -12.0, "scale": 0.95},
                   {"rotation_deg": 17.0, "tilt": (1.5e-4, 0.0),
                    "centre_offset_px": (25.0, -18.0)}):
        h = camera_homography(cal, SIZE, **kwargs)
        pose = fit_pose(render(cal, h, SIZE), cal)
        assert pose.accepted, pose.reason
        in_image = apply_homography(h, probe_mm)
        landed.append(apply_homography(pose.transform, in_image))

    disagreement = np.linalg.norm(landed[0] - landed[1], axis=1)
    assert disagreement.max() < 0.3, f"{disagreement} mm apart"


def test_missing_sheet_is_refused_with_a_reason():
    cal = Calibration()
    pose = fit_pose(np.zeros((400, 400)), cal)
    assert not pose.accepted
    assert "paper_not_found" in pose.reason
    assert pose.transform is None


def test_sheet_without_pegs_is_refused():
    cal = Calibration()
    h = camera_homography(cal, SIZE)
    image = render(cal, h, SIZE)
    # Paint the pegs out; the outline survives, the datum does not.
    pegs = apply_homography(h, cal.peg.positions())
    for x, y in pegs:
        xi, yi = int(round(x)), int(round(y))
        image[max(0, yi - 40):yi + 40, max(0, xi - 90):xi + 90] = 1.0
    pose = fit_pose(image, cal)
    assert not pose.accepted
    assert ("no_candidates" in pose.reason
            or "no_consistent_triple" in pose.reason), pose.reason


def test_a_refused_pose_carries_no_transform():
    """A caller must not be able to use a refused fit by accident."""
    pose = fit_pose(np.zeros((400, 400)), Calibration())
    assert pose.transform is None


def test_noise_does_not_break_the_fit():
    cal, truth, image = _capture(rotation_deg=6.0)
    noisy = render(cal, truth, SIZE, noise=0.02, seed=7)
    pose = fit_pose(noisy, cal)
    assert pose.accepted, pose.reason


def test_registration_never_mirrors_the_sheet():
    """Paper viewed from one side cannot be mirrored, but a homography
    fitted to a reflected corner labelling will happily deliver one.

    Caught on 2026-09-18: two captures of the same sheet registered to
    |y| agreeing within 0.03 mm and the *sign* disagreeing, because the
    orientation search enumerated corner swaps (reflections) alongside
    rotations, and because eigh's arbitrary eigenvector signs let the
    corner winding flip between frames.
    """
    cal = Calibration()
    probe = np.array([[40.0, 90.0], [-60.0, 150.0]])
    landed = []
    for kwargs in ({"rotation_deg": -10.0},
                   {"rotation_deg": 14.0, "tilt": (1.2e-4, 0.0),
                    "scale": 0.93}):
        h = camera_homography(cal, SIZE, **kwargs)
        pose = fit_pose(render(cal, h, SIZE), cal)
        assert pose.accepted, pose.reason
        assert np.linalg.det(pose.transform[:2, :2]) > 0, \
            "the fit reversed handedness"
        landed.append(apply_homography(pose.transform,
                                       apply_homography(h, probe)))
    assert np.allclose(np.sign(landed[0]), np.sign(landed[1])), (
        f"registered coordinates disagree in sign: "
        f"{landed[0].tolist()} vs {landed[1].tolist()}")
