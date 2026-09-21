"""Capture from the rig's camera, and refuse to lie about it.

A thin adapter, as the rest of ``nodes/`` is: the ordering rules, the
readback policy, the report and the session all live in
:mod:`acme.capture`, where they can be tested without ComfyUI or a
camera.  See docs/planning/camera-input-node.md for the measurements
that shaped them.
"""

from __future__ import annotations

from typing import List, Optional

from comfy_api.latest import io, ui

from ..acme.capture import (CaptureRequest, CaptureSession, Cv2Device,
                            apply_request, capture_report, capture_token,
                            device_index, failures, frame_to_rgb,
                            verify_against)
from ._convert import stack_to_tensor
from .registration import CATEGORY, AcmeCalibrationType

#: One camera, held open across executions.  V3 nodes are classmethods
#: with no instance to hang a handle on, and re-opening a UVC device
#: costs 0.58 s at best and 4.53 s at worst on v4k_01.
_SESSION: Optional[CaptureSession] = None


def _session() -> CaptureSession:
    global _SESSION
    if _SESSION is None:
        def _open(index: int):
            import cv2
            capture = cv2.VideoCapture(index)
            if not capture.isOpened():
                raise RuntimeError(
                    f"cannot open camera {index}; another program -- "
                    f"another ComfyUI tab, a video call -- may hold it")
            return capture
        _SESSION = CaptureSession(_open)
    return _SESSION


class AcmeCapture(io.ComfyNode):
    """One frame from the rig, checked against the calibration.

    The check is the point.  Intrinsics belong to a camera **at one
    focus**: v4k_01's are valid at ``focus_absolute`` 134 and nowhere
    else, and a frame shot at any other focus carries a lens model that
    does not describe it.  Nothing in the picture says so, which is why
    this node would rather stop than hand one downstream.

    Two things are done in a particular order, both measured:

    * **FOURCC before the geometry.** 3264x2448 in YUYV gives 1.3 fps
      and 4.53 s to first frame; MJPG gives 10.7 fps and 0.58 s. The
      driver accepts the geometry either way and says nothing.
    * **Every control read back only once all of them are set.** V4L2
      negotiates the format as a unit, so ``set(width, 3264)`` returns
      True and reads back 640 until the height completes a supported
      pair.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeCapture",
            display_name="ACME Capture",
            category=CATEGORY,
            description="Capture a frame, verified against the "
                        "calibration it will be interpreted with.",
            inputs=[
                io.String.Input(
                    "device",
                    default="/dev/v4l/by-id/"
                            "usb-IPEVO_Corp._IPEVO_V4K-video-index0",
                    tooltip="A by-id or by-path symlink, a /dev/videoN "
                            "node, or a bare index. Prefer a symlink: "
                            "/dev/videoN renumbers on replug. Note the "
                            "V4K reports no USB serial, so two of them "
                            "are indistinguishable by descriptor and "
                            "by-path is the only way to tell them "
                            "apart."),
                io.Int.Input("width", default=3264, min=160, max=8192,
                             tooltip="Must match what the calibration "
                                     "was measured at, or the intrinsics "
                                     "do not describe the frame."),
                io.Int.Input("height", default=2448, min=120, max=8192),
                io.Combo.Input(
                    "fourcc", options=["MJPG", "YUYV"],
                    tooltip="MJPG unless you have a reason. Measured on "
                            "v4k_01 at 3264x2448: MJPG 10.7 fps, YUYV "
                            "1.3 fps."),
                io.Int.Input(
                    "focus_absolute", default=134, min=-1, max=1023,
                    tooltip="-1 leaves focus alone, which is almost "
                            "always wrong: intrinsics belong to one "
                            "focus. v4k_01 is calibrated at 134."),
                io.Combo.Input(
                    "on_mismatch", options=["refuse", "warn"],
                    tooltip="What to do when the capture does not match "
                            "the calibration. Refusing is the default "
                            "because the alternative is a silently "
                            "wrong lens model, which is exactly what "
                            "this node exists to catch."),
                AcmeCalibrationType.Input(
                    "calibration", optional=True,
                    tooltip="Checked against, not used to capture. "
                            "Without it the frame is returned "
                            "unverified and the report says so."),
            ],
            outputs=[
                io.Image.Output("image"),
                io.String.Output("report"),
                io.Boolean.Output("verified"),
            ],
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        """Never serve a cached frame.

        A registration pass that silently re-used one would look like
        perfect repeatability, which is the worst way to be wrong.
        """
        return capture_token()

    @classmethod
    def execute(cls, device, width, height, fourcc, focus_absolute,
                on_mismatch, calibration=None) -> io.NodeOutput:
        capture = _session().open(device_index(device))
        request = CaptureRequest(
            width=int(width), height=int(height), fourcc=fourcc,
            focus=None if int(focus_absolute) < 0 else int(focus_absolute))
        results = apply_request(Cv2Device(capture), request)

        ok, frame = capture.read()
        if not ok or frame is None:
            raise RuntimeError(
                f"camera {device} accepted its settings but returned no "
                f"frame; {capture_report(results, [])}")

        actual_h, actual_w = frame.shape[:2]
        problems: List[str] = [f"control {r.name} asked {r.requested:g} "
                               f"and reads {r.actual:g}"
                               for r in failures(results)]
        if calibration is None:
            problems.append("no calibration was given, so this frame is "
                            "unverified")
        else:
            problems += verify_against(calibration.provenance, actual_w,
                                       actual_h, request.focus)

        text = capture_report(results, problems)
        if problems and on_mismatch == "refuse":
            raise RuntimeError(text)

        return io.NodeOutput(stack_to_tensor([frame_to_rgb(frame)]), text,
                             not problems, ui=ui.PreviewText(text))
