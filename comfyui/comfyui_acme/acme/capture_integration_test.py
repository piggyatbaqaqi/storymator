"""Capture against the real rig.  Opt in with ``--integration``.

These assert the things that cannot be faked: that the driver really
does deliver 3264x2448, that an absolute focus really sticks, and that
MJPG really is worth the extra ``set`` call.  Each one exists because
the evaluation in docs/planning/camera-input-node.md measured it, and
a regression here would be silent everywhere else.

Requires **v4k_01 on the bench with charuco_0001 in view**, and the
camera free -- ComfyUI holding the device will fail these.
"""

import glob
import json
import os
import time

import numpy as np
import pytest

from acme.capture import (CaptureRequest, Cv2Device, apply_request,
                          device_index, failures, frame_to_rgb,
                          verify_against)

cv2 = pytest.importorskip("cv2")

pytestmark = pytest.mark.integration

WIDTH, HEIGHT, FOCUS = 3264, 2448, 134
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                    "..", "..", ".."))
CALIBRATION = os.path.join(REPO, "data", "calibration", "distortion",
                           "v4k_01", "v4k_01.json")


def _v4k_path():
    """The V4K's stable address, or None.

    By-id rather than a hard-coded by-path, so this survives being
    plugged into a different port -- but note by-id carries no serial
    for this camera, so two V4Ks would be ambiguous.
    """
    found = glob.glob("/dev/v4l/by-id/*IPEVO_V4K*index0")
    return found[0] if found else None


@pytest.fixture(scope="module")
def camera():
    path = _v4k_path()
    if path is None:
        pytest.skip("v4k_01 is not plugged in")
    cap = cv2.VideoCapture(device_index(path))
    if not cap.isOpened():
        pytest.skip(f"{path} is busy -- is ComfyUI holding it?")
    yield cap
    cap.release()


@pytest.fixture(scope="module")
def device(camera):
    """The camera as a ControlDevice, which is what apply_request takes."""
    return Cv2Device(camera)


# --- what the driver actually does ----------------------------------

def test_the_camera_delivers_the_calibrated_frame_size(camera, device):
    """1920x1080 would silently invalidate the intrinsics."""
    results = apply_request(device, CaptureRequest(width=WIDTH,
                                                   height=HEIGHT,
                                                   focus=FOCUS))
    assert failures(results) == []
    ok, frame = camera.read()
    assert ok
    assert frame.shape[:2] == (HEIGHT, WIDTH)


def test_absolute_focus_sticks(device):
    """Measured by hand: set(134) reads back 134.0, set(635) 635.0.

    The whole v4k_01 calibration is valid at 134 and nowhere else.
    """
    for want in (FOCUS, 635):
        results = apply_request(device, CaptureRequest(
            width=WIDTH, height=HEIGHT, focus=want))
        assert failures(results) == [], f"focus {want} did not take"


def test_mjpg_is_materially_faster_than_yuyv(camera, device):
    """Measured 2026-09-21: 10.7 fps against 1.3, and 0.58 s to first
    frame against 4.53.  One extra set() call, an order of magnitude.

    Asserts 3x rather than 8x: this is a regression guard, not a
    benchmark, and it shares a bus with whatever else is plugged in.
    """
    def fps(fourcc):
        apply_request(device, CaptureRequest(width=WIDTH, height=HEIGHT,
                                             fourcc=fourcc))
        camera.read()                       # settle
        start = time.time()
        for _ in range(3):
            camera.read()
        return 3.0 / (time.time() - start)

    yuyv, mjpg = fps("YUYV"), fps("MJPG")
    assert mjpg > 3 * yuyv, f"MJPG {mjpg:.1f} fps vs YUYV {yuyv:.1f}"


# --- end to end, with the target in view -----------------------------

def test_a_captured_frame_converts_to_a_usable_image(camera, device):
    apply_request(device, CaptureRequest(width=WIDTH, height=HEIGHT,
                                         focus=FOCUS))
    ok, frame = camera.read()
    assert ok
    rgb = frame_to_rgb(frame)
    assert rgb.shape == (HEIGHT, WIDTH, 3)
    assert rgb.dtype == np.float32
    assert 0.0 <= rgb.min() and rgb.max() <= 1.0
    assert rgb.std() > 0.01, "an even field means the lens cap is on"


def test_the_calibration_target_is_found_in_a_live_frame(camera, device):
    """The one test that exercises capture through to detection.

    Needs charuco_0001 in view. If this passes, the capture path
    delivers frames the rest of the pack can actually use.
    """
    apply_request(device, CaptureRequest(width=WIDTH, height=HEIGHT,
                                         focus=FOCUS))
    camera.read()
    ok, frame = camera.read()
    assert ok
    board = cv2.aruco.CharucoBoard(
        (7, 9), 25.3163, 25.3163 * 18 / 25,
        cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250))
    corners, ids, _, _ = cv2.aruco.CharucoDetector(board).detectBoard(
        cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    assert corners is not None and len(corners) >= 12, \
        "charuco_0001 must be in view for this test"


# --- against the stored calibration ----------------------------------

def test_a_live_capture_verifies_against_the_stored_calibration(
        camera, device):
    """The node's whole reason for existing, end to end."""
    if not os.path.exists(CALIBRATION):
        pytest.skip(f"no calibration at {CALIBRATION}")
    provenance = json.load(open(CALIBRATION))["_provenance"]
    apply_request(device, CaptureRequest(width=WIDTH, height=HEIGHT,
                                         focus=FOCUS))
    ok, frame = camera.read()
    assert ok
    h, w = frame.shape[:2]
    assert verify_against(provenance, w, h, FOCUS) == []


def test_a_wrong_focus_is_caught_against_the_stored_calibration(camera):
    """Shooting at 635 against a 134 calibration -- the mistake already
    made by hand on the peg profiles."""
    if not os.path.exists(CALIBRATION):
        pytest.skip(f"no calibration at {CALIBRATION}")
    provenance = json.load(open(CALIBRATION))["_provenance"]
    assert verify_against(provenance, WIDTH, HEIGHT, 635)
