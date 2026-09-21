"""Camera capture: the parts that are not OpenCV and not a node.

The whole point of this module is **set-then-verify**. V4L2 controls
fail silently and routinely — ``cap.set()`` returns True and the value
does not change, or returns True and the driver quietly substitutes its
own. Evaluated against `comfyui_webcamcapture` on 2026-09-21,
``brightness`` set to 0.5 read back as 0.0, and ``aperture`` did not
exist at all. A capture layer that sets and hopes will produce frames
whose intrinsics are silently wrong.

Two things make that concrete for this rig:

* **The v4k_01 calibration is valid at ``focus_absolute`` 134 and
  nowhere else.** Frames captured at any other focus carry intrinsics
  that do not describe them.
* **FOURCC must be set before the geometry.** Measured on v4k_01:
  3264x2448 in YUYV gives 4.53 s to first frame and 1.3 fps, against
  0.58 s and 10.7 fps once MJPG is requested first. The driver accepts
  the geometry either way and says nothing.

Devices are addressed through the small :class:`ControlDevice` protocol
rather than ``cv2.VideoCapture`` directly, so this module needs neither
OpenCV nor a camera to test, and the node adapts.

See docs/planning/camera-input-node.md.
"""

from __future__ import annotations

import itertools
import os
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Sequence, Tuple

import numpy as np


class ControlDevice(Protocol):
    """What :func:`apply_request` needs of a camera."""

    def set_control(self, name: str, value: float) -> bool:
        """Request one control. True if the driver accepted it."""
        ...

    def get_control(self, name: str) -> float:
        """Read one control back."""
        ...


@dataclass(frozen=True)
class CaptureRequest:
    """What to ask the camera for.

    ``brightness`` and friends are **integers in the driver's own
    scale**, deliberately. Normalising them to 0-1 is how the upstream
    node silently pegged brightness to minimum.
    """

    width: int
    height: int
    fourcc: str = "MJPG"
    focus: Optional[int] = None
    auto_exposure: Optional[int] = None
    auto_white_balance: Optional[int] = None
    brightness: Optional[int] = None

    def controls(self) -> List[Tuple[str, float]]:
        """Controls in the order they must be applied.

        Order is load-bearing twice: FOURCC before geometry, and
        autofocus off before an absolute focus.
        """
        out: List[Tuple[str, float]] = [
            ("fourcc", float(fourcc_code(self.fourcc))),
            ("width", float(self.width)),
            ("height", float(self.height)),
        ]
        if self.focus is not None:
            # Autofocus first: an absolute focus set while the lens is
            # still hunting does not stick, and nothing says so.
            out.append(("autofocus", 0.0))
            out.append(("focus", float(self.focus)))
        for name, value in (("auto_exposure", self.auto_exposure),
                            ("auto_white_balance", self.auto_white_balance),
                            ("brightness", self.brightness)):
            if value is not None:
                out.append((name, float(value)))
        return out


@dataclass(frozen=True)
class ControlResult:
    """One control, as requested and as the device actually reports it."""

    name: str
    requested: float
    actual: float
    accepted: bool

    @property
    def ok(self) -> bool:
        """Accepted *and* reading back what was asked for.

        Both halves are needed: V4L2 returns False on a control it does
        not have, and True on one it silently substitutes.
        """
        return self.accepted and abs(self.actual - self.requested) <= 0.5


def apply_request(device: ControlDevice,
                  request: CaptureRequest) -> List[ControlResult]:
    """Apply every control in order, then read the whole lot back.

    **Set everything first.** V4L2 negotiates the format as a unit, not
    field by field: measured on v4k_01, ``set(width, 3264)`` returns
    True and then reads back 640, because 3264x480 is not a supported
    mode and the driver keeps the one it has. Setting the height
    completes a supported pair and both read back correctly. A readback
    taken between the two is real, transient and meaningless.

    Deferring every readback is also the stricter check, not merely a
    workaround for geometry: a later control can silently clobber an
    earlier one, and what matters is the state the camera is left in.
    """
    requested = request.controls()
    accepted = [bool(device.set_control(name, value))
                for name, value in requested]
    return [ControlResult(name=name, requested=value,
                          actual=float(device.get_control(name)),
                          accepted=took)
            for (name, value), took in zip(requested, accepted)]


def failures(results: Sequence[ControlResult]) -> List[ControlResult]:
    """The controls that did not take."""
    return [r for r in results if not r.ok]


def frame_to_rgb(frame: np.ndarray) -> np.ndarray:
    """BGR uint8 as OpenCV delivers it -> RGB float32 in 0..1.

    No batch dimension: batching is the node's job, via
    ``nodes/_convert.stack_to_tensor``.
    """
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(f"expected an (H, W, 3) BGR frame, got "
                         f"{frame.shape}")
    rgb = np.ascontiguousarray(frame[..., ::-1])
    return (rgb.astype(np.float32) / 255.0)


def verify_against(provenance: Optional[Dict], width: int, height: int,
                   focus: Optional[int]) -> List[str]:
    """Mismatches between a capture and the calibration's provenance.

    Empty means consistent. A calibration with no provenance block
    cannot be checked, which is not the same as passing, so that is
    reported too.
    """
    if not provenance:
        return ["the calibration carries no provenance block, so this "
                "capture cannot be checked against it"]

    problems: List[str] = []

    size = provenance.get("frame_size_px")
    if size is None:
        problems.append("the calibration records no frame size, so the "
                        "capture geometry cannot be checked")
    elif [int(width), int(height)] != [int(v) for v in size]:
        problems.append(
            f"frame is {width}x{height} but the calibration was measured "
            f"at {int(size[0])}x{int(size[1])}")

    want = provenance.get("focus_absolute")
    if want is None:
        problems.append("the calibration records no focus, so it cannot "
                        "be checked; intrinsics belong to one focus")
    elif focus is None:
        problems.append(
            f"focus is not pinned, but the calibration is valid only at "
            f"focus_absolute {int(want)}")
    elif int(focus) != int(want):
        problems.append(
            f"focus is {int(focus)} but the calibration was measured at "
            f"{int(want)}")

    return problems


#: Our control names, and the ``cv2.CAP_PROP_*`` each maps to.  Named
#: rather than numeric so this module needs no OpenCV, and so a control
#: that does not exist in the installed build fails loudly.
CONTROL_PROPERTIES: Dict[str, str] = {
    "fourcc": "CAP_PROP_FOURCC",
    "width": "CAP_PROP_FRAME_WIDTH",
    "height": "CAP_PROP_FRAME_HEIGHT",
    "autofocus": "CAP_PROP_AUTOFOCUS",
    "focus": "CAP_PROP_FOCUS",
    "auto_exposure": "CAP_PROP_AUTO_EXPOSURE",
    "auto_white_balance": "CAP_PROP_AUTO_WB",
    "brightness": "CAP_PROP_BRIGHTNESS",
}


def fourcc_code(fourcc: str) -> int:
    """A four-character code as the integer V4L2 wants.

    Arithmetic rather than ``cv2.VideoWriter_fourcc`` so this module
    stays importable without OpenCV.
    """
    if len(fourcc) != 4:
        raise ValueError(f"a FOURCC is four characters, not {fourcc!r}")
    return sum(ord(c) << (8 * i) for i, c in enumerate(fourcc))


class VideoCaptureLike(Protocol):
    """The slice of ``cv2.VideoCapture`` the adapter touches.

    Structural rather than importing the real class, which would drag
    OpenCV into this module's import time for a type annotation.
    """

    def set(self, propId: int, value: float) -> bool: ...

    def get(self, propId: int) -> float: ...


class Cv2Device:
    """Adapts ``cv2.VideoCapture`` to :class:`ControlDevice`.

    The indirection earns its keep twice: :mod:`acme.capture` stays
    testable without a camera, and the mapping from our names to
    ``CAP_PROP_*`` lives in one table rather than scattered through a
    node class.

    OpenCV is imported lazily, as in :mod:`acme.lens`, so importing
    this module costs nothing.
    """

    def __init__(self, capture: VideoCaptureLike) -> None:
        self._cap = capture

    def _prop(self, name: str) -> int:
        try:
            import cv2
        except ModuleNotFoundError as exc:   # pragma: no cover
            raise RuntimeError("capture needs OpenCV: pip install "
                               "opencv-contrib-python") from exc
        try:
            attr = CONTROL_PROPERTIES[name]
        except KeyError:
            raise ValueError(f"unknown control {name!r}") from None
        prop = getattr(cv2, attr, None)
        if prop is None:                     # pragma: no cover
            raise RuntimeError(f"this OpenCV build has no {attr}")
        return int(prop)

    def set_control(self, name: str, value: float) -> bool:
        return bool(self._cap.set(self._prop(name), float(value)))

    def get_control(self, name: str) -> float:
        return float(self._cap.get(self._prop(name)))


def device_index(spec: str) -> int:
    """Resolve a device spec to an OpenCV index.

    Accepts ``/dev/video3``, a ``/dev/v4l/by-path/...`` symlink, or a
    bare integer. By-path is the useful one: the V4K reports no USB
    serial, so the port it is plugged into is its only stable identity.
    """
    text = str(spec).strip()
    if text.isdigit():
        return int(text)
    name = os.path.basename(os.path.realpath(text))
    match = re.fullmatch(r"video(\d+)", name)
    if match is None:
        raise ValueError(
            f"{spec!r} does not resolve to a /dev/videoN node; give an "
            f"index, a device node, or a /dev/v4l/by-path symlink")
    return int(match.group(1))


def capture_report(results: Sequence[ControlResult],
                   problems: Sequence[str]) -> str:
    """What the operator needs to see on the node, in words.

    Silence is the enemy here: a capture at the wrong focus looks
    exactly like a capture at the right one.  Both numbers are printed
    for every control, because "focus failed" does not tell anyone
    which way to turn the dial.
    """
    bad = failures(results)
    lines = ["capture verified" if not (bad or problems)
             else "CAPTURE NOT VERIFIED", ""]
    if results:
        lines.append("controls:")
        for r in results:
            note = "" if r.accepted else ", and the driver refused it"
            lines.append(f"  {'!!' if not r.ok else '  '} {r.name:18s}"
                         f" asked {r.requested:g}, reads {r.actual:g}{note}")
    if problems:
        lines.append("")
        lines.append("against the calibration:")
        lines += [f"  - {p}" for p in problems]
    return "\n".join(lines)


class CaptureSession:
    """Holds one camera open across executions.

    Re-opening a UVC device costs half a second at best and four and a
    half at worst, measured on v4k_01, so a node that opened per
    execution would be unusable. V3 nodes have no instance state --
    ``execute`` is a classmethod -- so the handle lives here instead.

    ``opener`` is injected so this is testable without a camera.
    """

    def __init__(self, opener) -> None:
        self._opener = opener
        self._index: Optional[int] = None
        self._capture = None

    @property
    def index(self) -> Optional[int]:
        """Which device is currently held, if any."""
        return self._index

    def open(self, index: int):
        """The capture for ``index``, reusing the held one if it matches."""
        wanted = int(index)
        if self._capture is not None and self._index == wanted:
            return self._capture
        self.close()
        self._capture = self._opener(wanted)
        self._index = wanted
        return self._capture

    def close(self) -> None:
        """Release whatever is held. Safe to call when nothing is."""
        if self._capture is not None:
            try:
                self._capture.release()
            except Exception:       # pragma: no cover - driver teardown
                pass
        self._capture = None
        self._index = None


_SEQUENCE = itertools.count()


def capture_token() -> str:
    """A value that differs every call, for ComfyUI's ``IS_CHANGED``.

    A registration pass that silently re-used a cached frame would look
    like perfect repeatability, which is the worst way to be wrong.

    The counter rather than a clock alone: two calls inside one tick
    would otherwise collide, and that is exactly the case a cache hit
    arises in.
    """
    return f"{next(_SEQUENCE)}-{time.time_ns()}"
