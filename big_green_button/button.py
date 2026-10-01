"""What the big green button is, and how to recognise it.

One place for the device's identity so the config artifact, the
validator and the CLI cannot drift apart.  See
``docs/big-green-button.md``.
"""

from __future__ import annotations

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

#: Keys the button is known to send.  Cheap HID buttons disagree about
#: which Return they report, so bind both.
KEYS: Final[tuple[str, ...]] = ("enter", "kpenter")

#: Where the installed artifacts live on this machine.
KEYD_CONFIG_DIR: Final[str] = "/etc/keyd"
KEYD_CONFIG_NAME: Final[str] = "big-green-button.conf"
HOOK_PATH: Final[str] = "/usr/local/bin/big-green-button-press"


def installed_config_path() -> str:
    """``/etc/keyd/big-green-button.conf``."""
    raise NotImplementedError


def find(devices: Iterable[InputDevice]) -> tuple[InputDevice, ...]:
    """The button's interfaces among ``devices``, keyboard first."""
    raise NotImplementedError


def is_attached(devices: Iterable[InputDevice] | None = None) -> bool:
    """True when the button's keyboard interface is on the bus."""
    if devices is None:
        devices = input_devices.read_devices()
    raise NotImplementedError
