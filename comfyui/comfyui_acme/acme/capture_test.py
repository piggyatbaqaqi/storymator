"""Camera capture: set-then-verify, and refusing to trust a set().

Every behaviour here exists because the evaluation in
docs/planning/camera-input-node.md measured it going wrong on real
hardware.  The fakes below reproduce the specific ways V4L2 lies.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import pytest

from acme.capture import (CaptureRequest, CaptureSession, ControlResult,
                          apply_request, capture_report, capture_token,
                          device_index, failures, frame_to_rgb,
                          verify_against)
from acme.model import Calibration, FieldSpec, PegModel, SheetModel


class FakeCamera:
    """A camera that records what it was asked, in order.

    ``lies`` maps a control to the value it will report regardless of
    what was set -- which is what a V4L2 driver does when it silently
    substitutes.  ``rejects`` names controls whose ``set`` returns
    False.
    """

    def __init__(self, lies: Optional[Dict[str, float]] = None,
                 rejects: Tuple[str, ...] = ()):
        self.order: List[str] = []
        self.values: Dict[str, float] = {}
        self.reads: List[str] = []
        self.trace: List[Tuple[str, str]] = []
        self._lies = lies or {}
        self._rejects = rejects

    def set_control(self, name: str, value: float) -> bool:
        self.order.append(name)
        self.trace.append(("set", name))
        if name in self._rejects:
            return False
        self.values[name] = value
        return True

    def get_control(self, name: str) -> float:
        self.reads.append(name)
        self.trace.append(("get", name))
        if name in self._lies:
            return self._lies[name]
        return self.values.get(name, 0.0)


class NegotiatingCamera:
    """A camera that negotiates the whole format, as V4L2 does.

    Measured on v4k_01 2026-09-21: ``set(width, 3264)`` returns **True**
    and then reads back **640**, because 3264x480 is not a supported
    mode and the driver keeps the one it has.  Setting the height
    completes a supported pair and both read back correctly.

    So a readback taken between the two is real, transient, and
    meaningless -- which is exactly what the first integration run
    caught.
    """

    MODES = ((640, 480), (3264, 2448))

    def __init__(self) -> None:
        self.order: List[str] = []
        self.reads: List[str] = []
        self.values: Dict[str, float] = {}
        self._want = [640, 480]
        self._active = (640, 480)

    def set_control(self, name: str, value: float) -> bool:
        self.order.append(name)
        if name in ("width", "height"):
            self._want[0 if name == "width" else 1] = int(value)
            if tuple(self._want) in self.MODES:
                self._active = tuple(self._want)   # type: ignore[assignment]
        else:
            self.values[name] = value
        return True

    def get_control(self, name: str) -> float:
        self.reads.append(name)
        if name == "width":
            return float(self._active[0])
        if name == "height":
            return float(self._active[1])
        return self.values.get(name, 0.0)


FULL = CaptureRequest(width=3264, height=2448, focus=134)


# --- ordering -------------------------------------------------------

def test_fourcc_is_requested_before_the_geometry():
    """Measured: 8x throughput turns on this order alone.

    3264x2448 in YUYV gave 1.3 fps and 4.53 s to first frame; MJPG
    gave 10.7 fps and 0.58 s.  The driver accepts the geometry either
    way, so nothing downstream reveals the mistake.
    """
    cam = FakeCamera()
    apply_request(cam, FULL)
    assert "fourcc" in cam.order, "FOURCC must be requested at all"
    assert cam.order.index("fourcc") < cam.order.index("width")
    assert cam.order.index("fourcc") < cam.order.index("height")


def test_mjpg_is_the_default_fourcc():
    assert CaptureRequest(width=3264, height=2448).fourcc == "MJPG"


def test_autofocus_is_disabled_before_an_absolute_focus_is_set():
    """An absolute focus set while autofocus is live does not stick."""
    cam = FakeCamera()
    apply_request(cam, FULL)
    assert "autofocus" in cam.order
    assert cam.order.index("autofocus") < cam.order.index("focus")
    assert cam.values["autofocus"] == 0


def test_autofocus_is_left_alone_when_no_focus_is_requested():
    cam = FakeCamera()
    apply_request(cam, CaptureRequest(width=1280, height=720))
    assert "focus" not in cam.order


# --- set-then-verify ------------------------------------------------

def test_every_control_set_is_also_read_back():
    cam = FakeCamera()
    apply_request(cam, FULL)
    assert set(cam.reads) == set(cam.order), \
        "a control that is set but never read back is a control that lies"


def test_a_silent_substitution_is_reported_as_a_failure():
    """set() returns True, the value is not what was asked for."""
    cam = FakeCamera(lies={"focus": 0.0})
    results = apply_request(cam, FULL)
    bad = failures(results)
    assert [r.name for r in bad] == ["focus"]
    assert bad[0].requested == 134
    assert bad[0].actual == 0.0


def test_a_rejected_set_is_reported_as_a_failure():
    cam = FakeCamera(rejects=("focus",))
    bad = failures(apply_request(cam, FULL))
    assert [r.name for r in bad] == ["focus"]
    assert bad[0].accepted is False


def test_geometry_is_judged_on_the_finished_format_not_a_half_set_one():
    """The bug the first integration run found.

    Verifying each control the instant it is set reports width 3264 as
    having become 640, which is true at that moment and irrelevant: the
    format is not finished being described.
    """
    cam = NegotiatingCamera()
    assert failures(apply_request(cam, FULL)) == []


def test_nothing_is_read_back_until_everything_has_been_set():
    """Stated directly, so the ordering cannot drift back.

    A later control can also clobber an earlier one, which a readback
    taken mid-sequence would miss; what matters is the state the camera
    is left in.
    """
    cam = FakeCamera()
    apply_request(cam, FULL)
    kinds = [kind for kind, _ in cam.trace]
    half = len(kinds) // 2
    assert kinds == ["set"] * half + ["get"] * half


def test_a_request_that_takes_cleanly_has_no_failures():
    assert failures(apply_request(FakeCamera(), FULL)) == []


def test_brightness_is_passed_through_in_the_driver_scale():
    """Upstream normalised brightness to 0-1; set(0.5) read back 0.0.

    The node's own default therefore pegged brightness to minimum on
    every capture.  Integers, in whatever scale the driver uses.
    """
    cam = FakeCamera()
    apply_request(cam, CaptureRequest(width=1280, height=720,
                                      brightness=128))
    assert cam.values["brightness"] == 128


def test_control_result_ok_requires_both_acceptance_and_readback():
    assert ControlResult("focus", 134, 134, True).ok
    assert not ControlResult("focus", 134, 134, False).ok
    assert not ControlResult("focus", 134, 0, True).ok


# --- frame conversion -----------------------------------------------

def test_frame_to_rgb_reverses_the_channels_and_scales():
    bgr = np.zeros((2, 3, 3), dtype=np.uint8)
    bgr[..., 0] = 255           # blue channel, in BGR
    out = frame_to_rgb(bgr)
    assert out.dtype == np.float32
    assert out.shape == (2, 3, 3)
    assert np.allclose(out[..., 2], 1.0), "blue must land in channel 2"
    assert np.allclose(out[..., 0], 0.0)


def test_frame_to_rgb_does_not_add_a_batch_dimension():
    """Batching is the node's job, via nodes/_convert.stack_to_tensor."""
    assert frame_to_rgb(np.zeros((4, 5, 3), np.uint8)).shape == (4, 5, 3)


# --- verification against the calibration ---------------------------

PROV = {"frame_size_px": [3264, 2448], "focus_absolute": 134}


def test_verify_against_passes_a_consistent_capture():
    assert verify_against(PROV, 3264, 2448, 134) == []


def test_verify_against_catches_a_frame_size_mismatch():
    problems = verify_against(PROV, 1920, 1080, 134)
    assert len(problems) == 1
    assert "1920" in problems[0] and "3264" in problems[0]


def test_verify_against_catches_a_focus_mismatch():
    """The mistake already made by hand on the peg profiles.

    Shooting at focus 635 against a calibration measured at 134 gives
    intrinsics that do not describe the frames, and nothing in the
    image says so.
    """
    problems = verify_against(PROV, 3264, 2448, 635)
    assert len(problems) == 1
    assert "635" in problems[0] and "134" in problems[0]


def test_verify_against_reports_both_mismatches_at_once():
    assert len(verify_against(PROV, 1920, 1080, 635)) == 2


def test_absent_provenance_is_reported_rather_than_passing():
    """Cannot-check is not the same as checked-and-fine."""
    problems = verify_against(None, 3264, 2448, 134)
    assert problems, "a calibration with no provenance cannot be verified"


def test_provenance_survives_a_calibration_round_trip():
    """Calibration.to_dict/from_dict dropped the provenance block.

    Without this the verify input has nothing to check against.
    """
    cal = Calibration(peg=PegModel(), sheet=SheetModel(),
                      field_spec=FieldSpec(), provenance=PROV)
    back = Calibration.from_dict(cal.to_dict())
    assert back.provenance == PROV


# --- device addressing ----------------------------------------------

def test_device_index_accepts_a_bare_integer():
    assert device_index("3") == 3


def test_device_index_accepts_a_dev_node():
    assert device_index("/dev/video3") == 3


def test_device_index_resolves_a_by_path_symlink(tmp_path):
    """By-path is the V4K's only stable identity: it reports no USB
    serial, so two of them are indistinguishable by descriptor."""
    node = tmp_path / "video7"
    node.write_bytes(b"")
    link = tmp_path / "pci-0000:80:14.0-usb-0:8:1.0-video-index0"
    link.symlink_to(node)
    assert device_index(str(link)) == 7


def test_device_index_rejects_nonsense():
    with pytest.raises(ValueError):
        device_index("not-a-camera")


# --- re-execution ---------------------------------------------------

def test_capture_token_differs_between_calls():
    """ComfyUI caches by IS_CHANGED; a cached frame would look like
    perfect repeatability."""
    assert capture_token() != capture_token()


# --- the report the operator actually reads -------------------------

GOOD = [ControlResult("width", 3264, 3264, True),
        ControlResult("focus", 134, 134, True)]
BAD = [ControlResult("width", 3264, 3264, True),
       ControlResult("focus", 134, 0, True)]


def test_a_clean_capture_reports_itself_as_clean():
    text = capture_report(GOOD, [])
    assert "focus" in text
    assert "134" in text


def test_a_failed_control_is_named_with_both_numbers():
    """Requested and actual: "focus failed" alone does not help."""
    text = capture_report(BAD, [])
    assert "focus" in text
    assert "134" in text and "0" in text


def test_a_verification_problem_reaches_the_report_verbatim():
    problem = "focus is 635 but the calibration was measured at 134"
    assert problem in capture_report(GOOD, [problem])


def test_control_failures_and_verification_problems_both_appear():
    problem = "frame is 1920x1080 but the calibration was measured at ..."
    text = capture_report(BAD, [problem])
    assert problem in text
    assert "focus" in text


def test_a_clean_report_is_distinguishable_from_a_dirty_one():
    """Downstream and the operator both need a yes/no, not prose to
    parse."""
    assert capture_report(GOOD, []) != capture_report(BAD, [])


# --- holding the camera open ----------------------------------------

class FakeOpener:
    """Records opens and releases, so reuse can be asserted."""

    def __init__(self):
        self.opened: List[int] = []
        self.released: List[int] = []

    def __call__(self, index: int):
        self.opened.append(index)
        opener = self

        class _Capture:
            def __init__(self) -> None:
                self.index = index

            def release(self) -> None:
                opener.released.append(index)

        return _Capture()


def test_the_same_device_is_opened_once_and_reused():
    """Re-opening costs 0.58 s at best and 4.53 s at worst on v4k_01."""
    opener = FakeOpener()
    session = CaptureSession(opener)
    first = session.open(3)
    assert session.open(3) is first
    assert opener.opened == [3]


def test_changing_device_releases_the_old_one():
    opener = FakeOpener()
    session = CaptureSession(opener)
    session.open(3)
    session.open(4)
    assert opener.opened == [3, 4]
    assert opener.released == [3], "the old device must not be left held"


def test_close_releases_and_can_be_called_twice():
    opener = FakeOpener()
    session = CaptureSession(opener)
    session.open(3)
    session.close()
    session.close()
    assert opener.released == [3]
    assert session.index is None


def test_a_fresh_session_holds_nothing():
    assert CaptureSession(FakeOpener()).index is None
