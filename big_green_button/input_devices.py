"""Read ``/proc/bus/input/devices`` and find a device by USB id.

The button is identified by vendor:product, but ``8089:0019`` names two
interfaces on this device -- a keyboard and a mouse/joystick -- so every
lookup here can be narrowed to the one that carries the ``kbd`` handler.
That is the same distinction keyd draws with its ``k:`` id prefix, and
getting it wrong is how you end up with keyd managing ``js0``.

Parsing is split from reading so the tests can feed a captured copy of
the proc file rather than whatever happens to be plugged in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Iterable, Sequence

PROC_DEVICES: Final[str] = "/proc/bus/input/devices"


@dataclass(frozen=True)
class InputDevice:
    """One ``I:``/``N:``/``H:`` stanza of the proc file."""

    name: str
    vendor: str
    product: str
    bus: str = ""
    version: str = ""
    uniq: str = ""
    phys: str = ""
    sysfs: str = ""
    handlers: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_keyboard(self) -> bool:
        """True when the kernel gave this interface the ``kbd`` handler."""
        raise NotImplementedError

    @property
    def event_path(self) -> str | None:
        """``/dev/input/eventN`` for this interface, or None if it has none."""
        raise NotImplementedError


def parse_proc_devices(text: str) -> tuple[InputDevice, ...]:
    """Parse the whole proc file into devices, in file order."""
    raise NotImplementedError


def read_devices(path: str = PROC_DEVICES) -> tuple[InputDevice, ...]:
    """Read and parse the proc file."""
    raise NotImplementedError


def find(devices: Iterable[InputDevice], vendor: str, product: str,
         *, keyboard_only: bool = False) -> tuple[InputDevice, ...]:
    """Every interface matching ``vendor``:``product``, case-insensitively."""
    raise NotImplementedError


def format_devices(devices: Sequence[InputDevice]) -> str:
    """One human-readable line per device, for ``bin/big-green-button``."""
    raise NotImplementedError
