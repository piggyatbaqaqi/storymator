"""The node layer, imported for real.

These need ComfyUI on the path and its dependencies installed -- which
means running under the environment ComfyUI itself runs in. They skip
rather than fail otherwise, so the pack's own arithmetic stays testable
anywhere.

``tests/test_node_contract.py`` checks the same modules by parsing and
needs none of that; it is the cheap guard, this is the real one.
"""

import numpy as np
import torch
import pytest

pytest.importorskip("comfy_api.latest",
                    reason="needs ComfyUI on the path; run under the "
                           "environment ComfyUI runs in")

from comfyui_acme.acme.model import (Calibration, FieldSpec,  # noqa: E402
                                     PegModel, SheetModel)
from comfyui_acme.acme.synth import camera_homography, render  # noqa: E402
from comfyui_acme.nodes import (PHASE_1, AcmeCapture,  # noqa: E402
                                AcmeDetectSheet)
from comfyui_acme.nodes import capture as capture_node  # noqa: E402
from comfyui_acme.nodes._convert import (stack_to_tensor,  # noqa: E402
                                         to_gray)

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


# --- the diagnostic view ---------------------------------------------

SIZE = (1280, 960)


def _scene(n=1):
    """A synthetic capture, as a ComfyUI IMAGE batch."""
    cal = _calibration(None)
    frames = [render(cal, camera_homography(cal, SIZE), SIZE)
              for _ in range(n)]
    rgb = [np.repeat(f[:, :, None], 3, axis=2) if f.ndim == 2 else f
           for f in frames]
    return cal, rgb, stack_to_tensor(rgb)


def _detect(batch, cal):
    return AcmeDetectSheet.execute(batch, cal, 1.5, "dark").result


def _neutral(img):
    """Where the picture is grey, i.e. not drawn on."""
    return (img[..., 0] == img[..., 1]) & (img[..., 1] == img[..., 2])


def test_gray_comes_last_so_existing_links_survive():
    """Appended, not inserted.  A workflow already wired to overlay and
    report must not have its links shifted by a diagnostic."""
    schema = AcmeDetectSheet.define_schema()
    assert [o.id for o in schema.outputs] == [
        "pose", "overlay", "report", "gray"]


def test_the_background_is_the_luminance_the_detector_was_given():
    """Not a mean of the channels.  Rec. 709 suppresses the undercolour
    relative to graphite, and a diagnostic showing anything else would
    be worse than none -- the whole point is 'what did the detector
    see'."""
    cal, rgb, batch = _scene()
    gray = _detect(batch, cal)[3][0].numpy()
    want = to_gray(rgb[0])
    keep = _neutral(gray)
    assert keep.mean() > 0.9, "the annotations should not cover the frame"
    assert np.allclose(gray[..., 0][keep], want[keep], atol=1e-6)


def test_the_markers_are_red_on_the_grey():
    """Red is maximally legible on neutral, and nothing else in the
    picture can be mistaken for it: a grey pixel has R == G == B, so
    any pixel with R > G is a mark."""
    cal, _, batch = _scene()
    gray = _detect(batch, cal)[3][0].numpy()
    drawn = ~_neutral(gray)
    assert drawn.sum() > 500, "expected the corners and pegs to be drawn"
    r, g, b = gray[..., 0][drawn], gray[..., 1][drawn], gray[..., 2][drawn]
    assert np.median(r) > np.median(g)
    assert np.median(r) > np.median(b)


def test_the_markers_stay_red_whatever_the_verdict():
    """The overlay output carries the verdict in green or red.  This
    one answers a different question -- where did it look, and what did
    it find -- and one fixed colour keeps it readable either way."""
    cal, _, batch = _scene()
    accepted, *_ = _detect(batch, cal)
    gray = _detect(batch, cal)[3][0].numpy()
    assert accepted[0].accepted, "this synthetic scene should fit"
    drawn = ~_neutral(gray)
    assert np.median(gray[..., 0][drawn]) > np.median(gray[..., 1][drawn])


def test_gray_is_a_previewable_image_not_a_bare_channel():
    """ComfyUI IMAGE is (B, H, W, 3); a PreviewImage must just work."""
    cal, _, batch = _scene()
    gray = _detect(batch, cal)[3]
    assert gray.shape == (1, SIZE[1], SIZE[0], 3)
    assert gray.dtype == torch.float32


def test_gray_is_emitted_for_every_frame_in_the_batch():
    """Frame i of gray must be frame i of the input, like every other
    per-frame output on this node."""
    cal, rgb, batch = _scene(2)
    gray = _detect(batch, cal)[3]
    assert gray.shape[0] == 2
    for i in range(2):
        img = gray[i].numpy()
        keep = _neutral(img)
        assert np.allclose(img[..., 0][keep], to_gray(rgb[i])[keep],
                           atol=1e-6)


# --- the marks the operator actually looks at -------------------------

rect_pending = pytest.mark.xfail(reason="pegs are still drawn as circles")


@rect_pending
def test_the_peg_marks_follow_the_slot_not_a_fixed_circle():
    """What the operator expects to see.

    A circle says "something is here". An outline says "this is the
    shape I fitted, at this angle, this long" -- which is checkable at
    a glance and is the whole reason for fitting rectangles.
    """
    cal, _, batch = _scene()
    poses, _, _, gray = _detect(batch, cal)
    assert poses[0].accepted, poses[0].reason
    assert poses[0].peg_rects is not None
    img = gray[0].numpy()
    drawn = ~_neutral(img)

    # the marks around each peg must span that peg's fitted length
    for centre, rect in zip(poses[0].pegs_image, poses[0].peg_rects):
        x0, y0 = int(centre[0]) - 90, int(centre[1]) - 90
        near = drawn[max(y0, 0):y0 + 180, max(x0, 0):x0 + 180]
        ys, xs = np.nonzero(near)
        assert len(xs), "no marks near this peg"
        span = max(xs.max() - xs.min(), ys.max() - ys.min())
        assert span >= rect.long_px - 4, (
            f"marks span {span} px for a {rect.long_px:.0f} px slot")
