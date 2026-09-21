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
        raise NotImplementedError


@dataclass(frozen=True)
class ControlResult:
    """One control, as requested and as the device actually reports it."""

    name: str
    requested: float
    actual: float
    accepted: bool

    @property
    def ok(self) -> bool:
        raise NotImplementedError


def apply_request(device: ControlDevice,
                  request: CaptureRequest) -> List[ControlResult]:
    """Apply every control in order and read each one back."""
    raise NotImplementedError


def failures(results: Sequence[ControlResult]) -> List[ControlResult]:
    """The controls that did not take."""
    raise NotImplementedError


def frame_to_rgb(frame: np.ndarray) -> np.ndarray:
    """BGR uint8 as OpenCV delivers it -> RGB float32 in 0..1."""
    raise NotImplementedError


def verify_against(provenance: Optional[Dict], width: int, height: int,
                   focus: Optional[int]) -> List[str]:
    """Mismatches between a capture and the calibration's provenance.

    Empty means consistent. A calibration with no provenance block
    cannot be checked, which is not the same as passing, so that is
    reported too.
    """
    raise NotImplementedError


def device_index(spec: str) -> int:
    """Resolve a device spec to an OpenCV index.

    Accepts ``/dev/video3``, a ``/dev/v4l/by-path/...`` symlink, or a
    bare integer. By-path is the useful one: the V4K reports no USB
    serial, so the port it is plugged into is its only stable identity.
    """
    raise NotImplementedError


def capture_token() -> str:
    """A value that differs every call, for ComfyUI's ``IS_CHANGED``.

    A registration pass that silently re-used a cached frame would look
    like perfect repeatability, which is the worst way to be wrong.
    """
    raise NotImplementedError
