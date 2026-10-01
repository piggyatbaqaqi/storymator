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

import re
from dataclasses import dataclass, field
from typing import Final, Iterable, Sequence

PROC_DEVICES: Final[str] = "/proc/bus/input/devices"

_EVENT_RE: Final[re.Pattern[str]] = re.compile(r"^event\d+$")


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
        return "kbd" in self.handlers

    @property
    def event_path(self) -> str | None:
        """``/dev/input/eventN`` for this interface, or None if it has none."""
        for handler in self.handlers:
            if _EVENT_RE.match(handler):
                return f"/dev/input/{handler}"
        return None


def _parse_stanza(block: str) -> InputDevice | None:
    """One blank-line-separated stanza, or None if it holds no device."""
    name = vendor = product = bus = version = uniq = phys = sysfs = ""
    handlers: tuple[str, ...] = ()
    seen_id = False

    for line in block.splitlines():
        if len(line) < 3 or line[1] != ":":
            continue
        tag, rest = line[0], line[2:].strip()
        if tag == "I":
            seen_id = True
            fields = dict(
                pair.split("=", 1) for pair in rest.split() if "=" in pair)
            bus = fields.get("Bus", "").lower()
            vendor = fields.get("Vendor", "").lower()
            product = fields.get("Product", "").lower()
            version = fields.get("Version", "").lower()
        elif tag == "N" and rest.startswith("Name="):
            name = rest[len("Name="):].strip().strip('"')
        elif tag == "P" and rest.startswith("Phys="):
            phys = rest[len("Phys="):].strip()
        elif tag == "S" and rest.startswith("Sysfs="):
            sysfs = rest[len("Sysfs="):].strip()
        elif tag == "U" and rest.startswith("Uniq="):
            uniq = rest[len("Uniq="):].strip()
        elif tag == "H" and rest.startswith("Handlers="):
            handlers = tuple(rest[len("Handlers="):].split())

    if not seen_id:
        return None
    return InputDevice(name=name, vendor=vendor, product=product, bus=bus,
                       version=version, uniq=uniq, phys=phys, sysfs=sysfs,
                       handlers=handlers)


def parse_proc_devices(text: str) -> tuple[InputDevice, ...]:
    """Parse the whole proc file into devices, in file order."""
    devices = []
    for block in re.split(r"\n\s*\n", text):
        if not block.strip():
            continue
        device = _parse_stanza(block)
        if device is not None:
            devices.append(device)
    return tuple(devices)


def read_devices(path: str = PROC_DEVICES) -> tuple[InputDevice, ...]:
    """Read and parse the proc file."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        return parse_proc_devices(handle.read())


def find(devices: Iterable[InputDevice], vendor: str, product: str,
         *, keyboard_only: bool = False) -> tuple[InputDevice, ...]:
    """Every interface matching ``vendor``:``product``, case-insensitively."""
    want = (vendor.lower(), product.lower())
    return tuple(
        d for d in devices
        if (d.vendor.lower(), d.product.lower()) == want
        and (d.is_keyboard or not keyboard_only))


def format_devices(devices: Sequence[InputDevice]) -> str:
    """One human-readable line per device, for ``bin/big-green-button``."""
    return "\n".join(
        f"{d.vendor}:{d.product}  {d.event_path or '-':20s}  "
        f"{'kbd' if d.is_keyboard else '   '}  {d.name}"
        for d in devices)
