"""The node layer, imported for real.

These need ComfyUI on the path and its dependencies installed -- which
means running under the environment ComfyUI itself runs in. They skip
rather than fail otherwise, so the pack's own arithmetic stays testable
anywhere.

``tests/test_node_contract.py`` checks the same modules by parsing and
needs none of that; it is the cheap guard, this is the real one.
"""

import numpy as np
import pytest

pytest.importorskip("comfy_api.latest",
                    reason="needs ComfyUI on the path; run under the "
                           "environment ComfyUI runs in")

from comfyui_acme.acme.model import (Calibration, FieldSpec,  # noqa: E402
                                     PegModel, SheetModel)
from comfyui_acme.nodes import PHASE_1, AcmeCapture  # noqa: E402
from comfyui_acme.nodes import capture as capture_node  # noqa: E402

PROV = {"frame_size_px": [640, 480], "focus_absolute": 134}


def _calibration(provenance=PROV):
    return Calibration(peg=PegModel(), sheet=SheetModel(),
                       field_spec=FieldSpec(), provenance=provenance)


class FakeCapture:
    """A camera that takes every setting and returns one grey frame."""

    def __init__(self, width=640, height=480):
        self._w, self._h = width, height
        self._values = {}

    def set(self, prop, value):
        self._values[prop] = value
        return True

    def get(self, prop):
        import cv2
        if prop == cv2.CAP_PROP_FRAME_WIDTH:
            return float(self._w)
        if prop == cv2.CAP_PROP_FRAME_HEIGHT:
            return float(self._h)
        return float(self._values.get(prop, 0.0))

    def read(self):
        return True, np.full((self._h, self._w, 3), 128, np.uint8)

    def release(self):
        pass


@pytest.fixture
def rig(monkeypatch):
    """Point the node's session at a fake camera."""
    from comfyui_acme.acme.capture import CaptureSession
    camera = FakeCapture()
    monkeypatch.setattr(capture_node, "_SESSION",
                        CaptureSession(lambda index: camera))
    return camera


def _run(**kwargs):
    defaults = dict(device="0", width=640, height=480, fourcc="MJPG",
                    focus_absolute=134, on_mismatch="refuse",
                    calibration=_calibration())
    defaults.update(kwargs)
    return AcmeCapture.execute(**defaults)


# --- schemas ---------------------------------------------------------

def test_every_registered_node_builds_its_schema():
    for cls in PHASE_1:
        cls.define_schema()


def test_node_ids_are_unique():
    ids = [cls.define_schema().node_id for cls in PHASE_1]
    assert len(ids) == len(set(ids))


def test_capture_declares_the_inputs_and_outputs_it_promises():
    schema = AcmeCapture.define_schema()
    assert [i.id for i in schema.inputs] == [
        "device", "width", "height", "fourcc", "focus_absolute",
        "on_mismatch", "calibration"]
    assert [o.id for o in schema.outputs] == ["image", "report", "verified"]


def test_capture_never_serves_a_cached_frame():
    assert AcmeCapture.fingerprint_inputs() != AcmeCapture.fingerprint_inputs()


# --- the refuse/warn decision ----------------------------------------

def test_a_matching_capture_is_returned_and_marked_verified(rig):
    image, report, verified = _run().result
    assert verified is True
    assert image.shape == (1, 480, 640, 3)
    assert "NOT VERIFIED" not in report


def test_refuse_is_the_default_and_it_raises(rig):
    """A silently wrong lens model is what this node exists to catch."""
    with pytest.raises(RuntimeError, match="NOT VERIFIED"):
        _run(focus_absolute=635)


def test_warn_returns_the_frame_but_marks_it_unverified(rig):
    image, report, verified = _run(focus_absolute=635,
                                   on_mismatch="warn").result
    assert verified is False
    assert "635" in report and "134" in report
    assert image.shape == (1, 480, 640, 3)


def test_a_frame_size_mismatch_is_refused_too(rig):
    with pytest.raises(RuntimeError, match="NOT VERIFIED"):
        _run(calibration=_calibration({"frame_size_px": [3264, 2448],
                                       "focus_absolute": 134}))


def test_no_calibration_is_unverified_rather_than_assumed_fine(rig):
    """Nothing to check against is not the same as checked and clean."""
    with pytest.raises(RuntimeError, match="unverified"):
        _run(calibration=None)
