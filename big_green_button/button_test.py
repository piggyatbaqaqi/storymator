"""Tests for ``big_green_button.button``.

Mostly consistency checks on the device facts.  They look trivial and
they are, but they are the ones that fail usefully: the identity is
repeated in a keyd config, a by-id path and a hook path, and the way
this breaks is one of them being updated and the others not.
"""

from __future__ import annotations

from big_green_button import button, keyd_config
from big_green_button.input_devices import InputDevice

KBD = InputDevice(
    name="LinTx USB Keyboard", vendor="8089", product="0019",
    uniq="BEC8023D", handlers=("sysrq", "kbd", "event24", "leds"))
MOUSE = InputDevice(
    name="LinTx USB Keyboard Mouse", vendor="8089", product="0019",
    uniq="BEC8023D", handlers=("mouse2", "event25", "js0"))
INTERNAL = InputDevice(
    name="AT Translated Set 2 keyboard", vendor="0001", product="0001",
    handlers=("sysrq", "kbd", "event3", "leds"))


class TestIdentity:

    def test_the_keyd_id_is_built_from_the_usb_id(self) -> None:
        assert button.KEYD_ID == f"k:{button.VENDOR}:{button.PRODUCT}"

    def test_the_keyd_id_restricts_itself_to_the_keyboard(self) -> None:
        """Bare 8089:0019 would also hand keyd this device's js0."""
        assert button.KEYD_ID.startswith("k:")

    def test_the_usb_id_is_lowercase_hex_of_four_digits(self) -> None:
        for part in (button.VENDOR, button.PRODUCT):
            assert len(part) == 4
            assert part == part.lower()
            int(part, 16)

    def test_the_by_id_path_carries_the_serial(self) -> None:
        assert button.SERIAL in button.BY_ID_PATH

    def test_the_by_id_path_is_the_keyboard_interface(self) -> None:
        assert button.BY_ID_PATH.endswith("-event-kbd")

    def test_every_bound_key_is_a_name_keyd_knows(self) -> None:
        """A typo here is a journal line keyd shrugs off at load time."""
        assert set(button.KEYS) <= keyd_config.KEY_NAMES

    def test_both_returns_are_bound(self) -> None:
        assert set(button.KEYS) == {"enter", "kpenter"}

    def test_the_hook_path_is_absolute(self) -> None:
        """keyd runs it through a shell from its own working directory."""
        assert button.HOOK_PATH.startswith("/")

    def test_the_hook_lives_in_the_hook_dir(self) -> None:
        assert button.HOOK_PATH.startswith(button.HOOK_DIR + "/")

    def test_the_hook_is_not_under_usr_local(self) -> None:
        """On this machine /usr/local and /usr/local/bin are root:src
        mode 0775, and group src is just the operator.  A hook keyd runs
        as root must not sit anywhere a non-root user can replace it."""
        assert not button.HOOK_PATH.startswith("/usr/local/")

    def test_the_config_name_ends_in_conf(self) -> None:
        """keyd loads only ``*.conf`` out of /etc/keyd."""
        assert button.KEYD_CONFIG_NAME.endswith(".conf")


class TestInstalledConfigPath:

    def test_joins_the_keyd_directory_and_the_name(self) -> None:
        assert button.installed_config_path() == (
            "/etc/keyd/big-green-button.conf")


class TestFind:

    def test_returns_both_interfaces(self) -> None:
        got = button.find([INTERNAL, MOUSE, KBD])
        assert {d.name for d in got} == {KBD.name, MOUSE.name}

    def test_puts_the_keyboard_interface_first(self) -> None:
        """Callers want the interface keyd manages, and want it cheaply."""
        assert button.find([MOUSE, KBD])[0].name == KBD.name

    def test_ignores_other_devices(self) -> None:
        assert button.find([INTERNAL]) == ()

    def test_an_empty_bus(self) -> None:
        assert button.find([]) == ()


class TestIsAttached:

    def test_true_when_the_keyboard_interface_is_present(self) -> None:
        assert button.is_attached([INTERNAL, KBD]) is True

    def test_false_when_only_the_mouse_interface_is_present(self) -> None:
        """Not a state the kernel produces, but the grab follows the
        keyboard interface, so that is what 'attached' has to mean."""
        assert button.is_attached([MOUSE]) is False

    def test_false_when_the_button_is_unplugged(self) -> None:
        assert button.is_attached([INTERNAL]) is False

    def test_reads_the_real_bus_when_given_nothing(self) -> None:
        assert button.is_attached() in (True, False)
