"""Tests for ``big_green_button.input_devices``.

PROC is a trimmed verbatim copy of this machine's
/proc/bus/input/devices: the laptop's internal keyboard, a touchpad
with no ``kbd`` handler, and the button's two interfaces.  Trimmed
rather than invented because the format has details worth keeping --
the trailing space on every ``H:`` line (written ``\x20`` so this
file has no trailing whitespace of its own), the empty ``U: Uniq=``,
and one device with no ``eventN`` handler at all.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from big_green_button import input_devices
from big_green_button.input_devices import InputDevice

PROC = '''I: Bus=0011 Vendor=0001 Product=0001 Version=ab83
N: Name="AT Translated Set 2 keyboard"
P: Phys=isa0060/serio0/input0
S: Sysfs=/devices/platform/i8042/serio0/input/input3
U: Uniq=
H: Handlers=sysrq kbd event3 leds\x20
B: PROP=0
B: EV=120013

I: Bus=0018 Vendor=27c6 Product=01e0 Version=0100
N: Name="GXTP5100:00 27C6:01E0 Touchpad"
P: Phys=i2c-GXTP5100:00
S: Sysfs=/devices/pci0000:80/0000:80:15.1/input/input8
U: Uniq=
H: Handlers=mouse1 event5\x20
B: PROP=5
B: EV=1b

I: Bus=0003 Vendor=048d Product=c197 Version=0110
N: Name="ITE Tech. Inc. ITE Device(8258)"
P: Phys=usb-0000:80:14.0-4/input0
S: Sysfs=/devices/pci0000:80/0000:80:14.0/usb3/3-4/input/input11
U: Uniq=
H: Handlers=
B: PROP=0
B: EV=9

I: Bus=0003 Vendor=8089 Product=0019 Version=0200
N: Name="LinTx USB Keyboard"
P: Phys=usb-0000:80:14.0-7/input1
S: Sysfs=/devices/pci0000:80/0000:80:14.0/usb3/3-7/3-7:1.1/input/input217
U: Uniq=BEC8023D
H: Handlers=sysrq kbd event24 leds\x20
B: PROP=0
B: EV=120013

I: Bus=0003 Vendor=8089 Product=0019 Version=0200
N: Name="LinTx USB Keyboard Mouse"
P: Phys=usb-0000:80:14.0-7/input1
S: Sysfs=/devices/pci0000:80/0000:80:14.0/usb3/3-7/3-7:1.1/input/input218
U: Uniq=BEC8023D
H: Handlers=mouse2 event25 js0\x20
B: PROP=0
B: EV=1f
'''

pytestmark = pytest.mark.xfail(raises=NotImplementedError, strict=True,
                               reason="skeleton; implementation to follow")


class TestParseProcDevices:

    def test_finds_every_stanza(self) -> None:
        assert len(input_devices.parse_proc_devices(PROC)) == 5

    def test_keeps_file_order(self) -> None:
        got = [d.name for d in input_devices.parse_proc_devices(PROC)]
        assert got == [
            "AT Translated Set 2 keyboard",
            "GXTP5100:00 27C6:01E0 Touchpad",
            "ITE Tech. Inc. ITE Device(8258)",
            "LinTx USB Keyboard",
            "LinTx USB Keyboard Mouse",
        ]

    def test_strips_the_quotes_from_the_name(self) -> None:
        first = input_devices.parse_proc_devices(PROC)[0]
        assert first.name == "AT Translated Set 2 keyboard"

    def test_reads_the_i_line(self) -> None:
        button = input_devices.parse_proc_devices(PROC)[3]
        assert (button.bus, button.vendor, button.product,
                button.version) == ("0003", "8089", "0019", "0200")

    def test_lowercases_the_usb_id(self) -> None:
        """The proc file is lowercase hex; keep ids comparable as strings."""
        touchpad = input_devices.parse_proc_devices(PROC)[1]
        assert (touchpad.vendor, touchpad.product) == ("27c6", "01e0")

    def test_reads_uniq_phys_and_sysfs(self) -> None:
        button = input_devices.parse_proc_devices(PROC)[3]
        assert button.uniq == "BEC8023D"
        assert button.phys == "usb-0000:80:14.0-7/input1"
        assert button.sysfs.endswith("/input217")

    def test_empty_uniq_is_an_empty_string(self) -> None:
        assert input_devices.parse_proc_devices(PROC)[0].uniq == ""

    def test_splits_handlers_and_drops_the_trailing_space(self) -> None:
        button = input_devices.parse_proc_devices(PROC)[3]
        assert button.handlers == ("sysrq", "kbd", "event24", "leds")

    def test_a_device_with_no_handlers(self) -> None:
        assert input_devices.parse_proc_devices(PROC)[2].handlers == ()

    def test_empty_text_yields_nothing(self) -> None:
        assert input_devices.parse_proc_devices("") == ()

    def test_blank_lines_alone_yield_nothing(self) -> None:
        assert input_devices.parse_proc_devices("\n\n\n") == ()

    def test_a_final_stanza_without_a_trailing_blank_line(self) -> None:
        text = PROC.rstrip() + "\n"
        assert len(input_devices.parse_proc_devices(text)) == 5


class TestIsKeyboard:

    def test_true_when_the_kernel_gave_it_the_kbd_handler(self) -> None:
        button = input_devices.parse_proc_devices(PROC)[3]
        assert button.is_keyboard is True

    def test_false_for_the_buttons_mouse_interface(self) -> None:
        """Same vendor:product as the button; this is why k: exists."""
        mouse = input_devices.parse_proc_devices(PROC)[4]
        assert mouse.is_keyboard is False

    def test_false_when_there_are_no_handlers(self) -> None:
        assert input_devices.parse_proc_devices(PROC)[2].is_keyboard is False


class TestEventPath:

    def test_builds_the_dev_input_path(self) -> None:
        button = input_devices.parse_proc_devices(PROC)[3]
        assert button.event_path == "/dev/input/event24"

    def test_none_when_the_device_has_no_event_handler(self) -> None:
        assert input_devices.parse_proc_devices(PROC)[2].event_path is None

    def test_ignores_the_js_and_mouse_handlers(self) -> None:
        mouse = input_devices.parse_proc_devices(PROC)[4]
        assert mouse.event_path == "/dev/input/event25"


class TestFind:

    def test_returns_both_interfaces_of_the_button(self) -> None:
        devices = input_devices.parse_proc_devices(PROC)
        got = input_devices.find(devices, "8089", "0019")
        assert [d.name for d in got] == ["LinTx USB Keyboard",
                                         "LinTx USB Keyboard Mouse"]

    def test_keyboard_only_drops_the_mouse_interface(self) -> None:
        devices = input_devices.parse_proc_devices(PROC)
        got = input_devices.find(devices, "8089", "0019", keyboard_only=True)
        assert [d.name for d in got] == ["LinTx USB Keyboard"]

    def test_matching_is_case_insensitive(self) -> None:
        """keyd ids get typed by hand; 27C6 and 27c6 are one device."""
        devices = input_devices.parse_proc_devices(PROC)
        assert len(input_devices.find(devices, "27C6", "01E0")) == 1

    def test_no_match_is_empty(self) -> None:
        devices = input_devices.parse_proc_devices(PROC)
        assert input_devices.find(devices, "dead", "beef") == ()

    def test_an_empty_haystack(self) -> None:
        assert input_devices.find([], "8089", "0019") == ()


class TestReadDevices:

    def test_reads_and_parses_a_file(self, tmp_path: Path) -> None:
        path = tmp_path / "devices"
        path.write_text(PROC)
        got = input_devices.read_devices(str(path))
        assert [d.vendor for d in got][-1] == "8089"

    def test_the_real_proc_file_parses(self) -> None:
        """Cheap canary: the kernel's format is stable, so this holds."""
        assert len(input_devices.read_devices()) > 0


class TestFormatDevices:

    def test_names_the_device_and_its_event_path(self) -> None:
        button = input_devices.parse_proc_devices(PROC)[3]
        line = input_devices.format_devices([button])
        assert "LinTx USB Keyboard" in line
        assert "/dev/input/event24" in line
        assert "8089:0019" in line

    def test_one_line_per_device(self) -> None:
        devices = input_devices.parse_proc_devices(PROC)
        out = input_devices.format_devices(devices)
        assert len(out.splitlines()) == len(devices)

    def test_empty_input_is_empty_output(self) -> None:
        assert input_devices.format_devices([]) == ""

    def test_survives_a_device_with_no_event_path(self) -> None:
        bare = InputDevice(name="nothing", vendor="0000", product="0000")
        assert "nothing" in input_devices.format_devices([bare])
