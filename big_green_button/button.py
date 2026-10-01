"""What the big green button is, and how to recognise it.

One place for the device's identity so the config artifact, the
validator and the CLI cannot drift apart.  See
``docs/big-green-button.md``.
"""

from __future__ import annotations

import posixpath
from typing import Final, Iterable

from . import input_devices
from .input_devices import InputDevice

#: USB vendor:product of the LinTx button.  Shared by its keyboard and
#: its mouse interface, which is why KEYD_ID carries the ``k:`` prefix.
VENDOR: Final[str] = "8089"
PRODUCT: Final[str] = "0019"

#: ``Uniq`` from the proc file; also the serial in the by-id path.
SERIAL: Final[str] = "BEC8023D"

#: The id to write in a keyd ``[ids]`` section: keyboard interface only.
KEYD_ID: Final[str] = f"k:{VENDOR}:{PRODUCT}"

#: Stable path to the keyboard interface, for diagnostics only -- keyd
#: opens the device itself and we never read it.
BY_ID_PATH: Final[str] = (
    f"/dev/input/by-id/usb-LinTx_USB_Keyboard_{SERIAL}-if01-event-kbd")

#: Keys the button is known to send.  Measured: it only ever sends
#: ``enter`` (scancode 70028).  ``kpenter`` is bound anyway so a
#: firmware mode change cannot quietly start leaking Returns.
KEYS: Final[tuple[str, ...]] = ("enter", "kpenter")

#: Where the installed artifacts live on this machine.
KEYD_CONFIG_DIR: Final[str] = "/etc/keyd"
KEYD_CONFIG_NAME: Final[str] = "big-green-button.conf"
#: Deliberately NOT under /usr/local: on this machine /usr/local and
#: /usr/local/bin are root:src mode 0775, so group src -- which is just
#: the operator -- could replace a hook keyd runs as root.  /opt is
#: root:root 0755, and HOOK_DIR is created the same way.
HOOK_DIR: Final[str] = "/opt/big-green-button"
HOOK_PATH: Final[str] = f"{HOOK_DIR}/press"


def installed_config_path() -> str:
    """``/etc/keyd/big-green-button.conf``."""
    return posixpath.join(KEYD_CONFIG_DIR, KEYD_CONFIG_NAME)


def find(devices: Iterable[InputDevice]) -> tuple[InputDevice, ...]:
    """The button's interfaces among ``devices``, keyboard first."""
    found = input_devices.find(devices, VENDOR, PRODUCT)
    return tuple(sorted(found, key=lambda d: not d.is_keyboard))


def is_attached(devices: Iterable[InputDevice] | None = None) -> bool:
    """True when the button's keyboard interface is on the bus."""
    if devices is None:
        devices = input_devices.read_devices()
    return any(d.is_keyboard for d in find(devices))
