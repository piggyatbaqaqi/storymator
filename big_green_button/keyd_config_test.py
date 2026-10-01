"""Tests for ``big_green_button.keyd_config``.

Two halves.  The first exercises the parser, renderer and validator on
hand-written configs.  The second -- TestShippedConfig -- points the
validator at the artifact we actually install, which is the point of
the module: keyd answers a typo with a journal line and a half-applied
keymap, and a half-applied keymap on this config means the button goes
back to typing Return with nothing to say so.
"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path
from typing import Iterable

import pytest

from big_green_button import button, keyd_config
from big_green_button.keyd_config import (Binding, ConfigError, DeviceId,
                                          KeydConfig)

_HERE = Path(__file__).resolve().parent
SHIPPED = _HERE / "etc" / "big-green-button.conf"
SHIPPED_HOOK = _HERE / "hook" / "big-green-button-press"

MINIMAL = """[ids]

k:8089:0019

[main]

enter = command(/usr/local/bin/big-green-button-press)
"""


class TestKeyNamesTable:
    """The vendored copy of ``keyd.rvaiya list-keys``."""

    def test_holds_the_keys_the_button_sends(self) -> None:
        assert {"enter", "kpenter"} <= keyd_config.KEY_NAMES

    def test_holds_f24_for_the_keystroke_alternative(self) -> None:
        assert "f24" in keyd_config.KEY_NAMES

    def test_holds_noop(self) -> None:
        assert "noop" in keyd_config.KEY_NAMES

    def test_holds_the_shifted_aliases(self) -> None:
        """list-keys reports ``!`` and ``Q`` as names in their own right."""
        assert {"!", "Q"} <= keyd_config.KEY_NAMES

    def test_does_not_hold_obvious_typos(self) -> None:
        assert "entre" not in keyd_config.KEY_NAMES
        assert "f25" not in keyd_config.KEY_NAMES

    @pytest.mark.skipif(shutil.which("keyd.rvaiya") is None,
                        reason="keyd is not installed here")
    def test_agrees_with_the_installed_keyd(self) -> None:
        """Catches the table going stale across a keyd upgrade."""
        out = os.popen("keyd.rvaiya list-keys").read()
        live = {ln.strip() for ln in out.splitlines() if ln.strip()}
        assert live == set(keyd_config.KEY_NAMES)


class TestDeviceIdParse:

    def test_a_bare_vendor_product(self) -> None:
        got = DeviceId.parse("8089:0019")
        assert (got.vendor, got.product, got.kind, got.hash) == (
            "8089", "0019", "", "")

    def test_the_keyboard_prefix(self) -> None:
        assert DeviceId.parse("k:8089:0019").kind == "k"

    def test_the_mouse_prefix(self) -> None:
        assert DeviceId.parse("m:046d:b01d").kind == "m"

    def test_the_three_part_form_the_monitor_prints(self) -> None:
        """keyd logs ``8089:0019:6f7af444``; accept what it hands you."""
        got = DeviceId.parse("8089:0019:6f7af444")
        assert (got.vendor, got.product, got.hash) == (
            "8089", "0019", "6f7af444")

    def test_lowercases_the_hex(self) -> None:
        got = DeviceId.parse("27C6:01E0")
        assert (got.vendor, got.product) == ("27c6", "01e0")

    def test_tolerates_surrounding_space(self) -> None:
        assert DeviceId.parse("  k:8089:0019  ").kind == "k"

    @pytest.mark.parametrize("bad", [
        "", "8089", "8089:", ":0019", "808:0019", "8089:001",
        "x:8089:0019", "8089-0019", "zzzz:0019", "k:8089",
    ])
    def test_rejects_malformed_ids(self, bad: str) -> None:
        with pytest.raises(ConfigError):
            DeviceId.parse(bad)


class TestDeviceIdStr:

    @pytest.mark.parametrize("text", [
        "8089:0019", "k:8089:0019", "m:046d:b01d", "8089:0019:6f7af444",
    ])
    def test_round_trips(self, text: str) -> None:
        assert str(DeviceId.parse(text)) == text


class TestDeviceIdMatches:

    def test_a_bare_id_matches_the_keyboard(self) -> None:
        assert DeviceId.parse("8089:0019").matches(
            "8089", "0019", is_keyboard=True) is True

    def test_a_bare_id_also_matches_the_mouse(self) -> None:
        """Which is exactly the accident ``k:`` exists to avoid."""
        assert DeviceId.parse("8089:0019").matches(
            "8089", "0019", is_keyboard=False) is True

    def test_k_matches_only_the_keyboard(self) -> None:
        kid = DeviceId.parse("k:8089:0019")
        assert kid.matches("8089", "0019", is_keyboard=True) is True
        assert kid.matches("8089", "0019", is_keyboard=False) is False

    def test_m_matches_only_the_mouse(self) -> None:
        mid = DeviceId.parse("m:8089:0019")
        assert mid.matches("8089", "0019", is_keyboard=False) is True
        assert mid.matches("8089", "0019", is_keyboard=True) is False

    def test_a_different_device_never_matches(self) -> None:
        assert DeviceId.parse("k:8089:0019").matches(
            "0001", "0001", is_keyboard=True) is False

    def test_comparison_ignores_hex_case(self) -> None:
        assert DeviceId.parse("27c6:01e0").matches(
            "27C6", "01E0", is_keyboard=False) is True

    def test_the_monitor_hash_does_not_narrow_the_match(self) -> None:
        """We never learn the hash of an attached device, so ignore it."""
        assert DeviceId.parse("8089:0019:6f7af444").matches(
            "8089", "0019", is_keyboard=True) is True


class TestBinding:

    def test_a_command_action(self) -> None:
        b = Binding("enter", "command(/usr/local/bin/press)")
        assert b.action_name == "command"
        assert b.action_arg == "/usr/local/bin/press"

    def test_a_bare_key_name_has_no_action(self) -> None:
        b = Binding("enter", "f24")
        assert b.action_name is None
        assert b.action_arg is None

    def test_noop_reads_as_a_bare_name(self) -> None:
        """``noop`` takes no parentheses and is also a list-keys name."""
        assert Binding("enter", "noop").action_name is None

    def test_a_layer_action(self) -> None:
        b = Binding("capslock", "layer(nav)")
        assert (b.action_name, b.action_arg) == ("layer", "nav")

    def test_an_empty_argument(self) -> None:
        assert Binding("enter", "macro()").action_arg == ""

    def test_nested_parentheses_stay_in_the_argument(self) -> None:
        """A shell command may legitimately contain brackets."""
        b = Binding("enter", "command(sh -c 'f(){ :; }; f')")
        assert b.action_arg == "sh -c 'f(){ :; }; f'"


class TestKeydConfigClaims:

    def test_an_explicit_keyboard_id(self) -> None:
        cfg = KeydConfig(ids=(DeviceId("8089", "0019", kind="k"),))
        assert cfg.claims("8089", "0019", is_keyboard=True) is True

    def test_leaves_the_mouse_interface_alone(self) -> None:
        cfg = KeydConfig(ids=(DeviceId("8089", "0019", kind="k"),))
        assert cfg.claims("8089", "0019", is_keyboard=False) is False

    def test_an_unlisted_device(self) -> None:
        cfg = KeydConfig(ids=(DeviceId("8089", "0019", kind="k"),))
        assert cfg.claims("0001", "0001", is_keyboard=True) is False

    def test_the_wildcard_claims_any_keyboard(self) -> None:
        cfg = KeydConfig(wildcard=True)
        assert cfg.claims("0001", "0001", is_keyboard=True) is True

    def test_the_wildcard_does_not_claim_mice(self) -> None:
        """keyd's manual: the wildcard matches keyboards only."""
        cfg = KeydConfig(wildcard=True)
        assert cfg.claims("8089", "0019", is_keyboard=False) is False

    def test_an_exclusion_beats_the_wildcard(self) -> None:
        cfg = KeydConfig(wildcard=True,
                         excluded=(DeviceId("0001", "0001"),))
        assert cfg.claims("0001", "0001", is_keyboard=True) is False

    def test_an_empty_config_claims_nothing(self) -> None:
        assert KeydConfig().claims("8089", "0019", is_keyboard=True) is False


class TestKeydConfigBindings:

    def test_returns_the_named_layer(self) -> None:
        main = (Binding("enter", "f24"),)
        cfg = KeydConfig(layers={"main": main})
        assert cfg.bindings("main") == main

    def test_defaults_to_main(self) -> None:
        main = (Binding("enter", "f24"),)
        assert KeydConfig(layers={"main": main}).bindings() == main

    def test_an_absent_layer_is_empty(self) -> None:
        assert KeydConfig(layers={"main": ()}).bindings("nav") == ()


class TestKeydConfigHookPaths:

    def test_extracts_the_program_without_its_arguments(self) -> None:
        cfg = KeydConfig(layers={"main": (
            Binding("enter", "command(/usr/bin/foo --bar baz)"),)})
        assert cfg.hook_paths() == ("/usr/bin/foo",)

    def test_ignores_bindings_that_are_not_commands(self) -> None:
        cfg = KeydConfig(layers={"main": (Binding("enter", "f24"),)})
        assert cfg.hook_paths() == ()

    def test_deduplicates_in_first_appearance_order(self) -> None:
        """enter and kpenter share one hook; report it once."""
        cfg = KeydConfig(layers={"main": (
            Binding("enter", "command(/b/two)"),
            Binding("kpenter", "command(/a/one)"),
            Binding("space", "command(/b/two)"))})
        assert cfg.hook_paths() == ("/b/two", "/a/one")

    def test_spans_every_layer(self) -> None:
        cfg = KeydConfig(layers={
            "main": (Binding("enter", "command(/a)"),),
            "nav": (Binding("enter", "command(/b)"),)})
        assert set(cfg.hook_paths()) == {"/a", "/b"}


class TestParse:

    def test_a_minimal_config(self) -> None:
        cfg = keyd_config.parse(MINIMAL)
        assert cfg.ids == (DeviceId("8089", "0019", kind="k"),)
        assert cfg.bindings("main") == (
            Binding("enter", "command(/usr/local/bin/big-green-button-press)"),
        )

    def test_ignores_comments_and_blank_lines(self) -> None:
        text = ("# a note\n\n[ids]\n\n# another\nk:8089:0019\n"
                "\n[main]\n\nenter = noop\n")
        assert keyd_config.parse(text).bindings("main") == (
            Binding("enter", "noop"),)

    def test_tolerates_space_around_the_equals(self) -> None:
        text = "[ids]\n8089:0019\n[main]\nenter    =    f24\n"
        assert keyd_config.parse(text).bindings("main") == (
            Binding("enter", "f24"),)

    def test_does_not_treat_a_trailing_hash_as_a_comment(self) -> None:
        """keyd only ignores lines that BEGIN with a hash.  A trailing
        one becomes part of the action, which is a real foot-gun worth
        reproducing rather than smoothing over -- validate() flags it."""
        text = "[ids]\n8089:0019\n[main]\nenter = f24 # why not\n"
        assert keyd_config.parse(text).bindings("main") == (
            Binding("enter", "f24 # why not"),)

    def test_several_layers(self) -> None:
        text = ("[ids]\n8089:0019\n[main]\ncapslock = layer(nav)\n"
                "[nav]\nh = left\nl = right\n")
        cfg = keyd_config.parse(text)
        assert set(cfg.layers) == {"main", "nav"}
        assert len(cfg.bindings("nav")) == 2

    def test_the_wildcard_form(self) -> None:
        text = "[ids]\n*\n-0001:0001\n[main]\nenter = noop\n"
        cfg = keyd_config.parse(text)
        assert cfg.wildcard is True
        assert cfg.excluded == (DeviceId("0001", "0001"),)
        assert cfg.ids == ()

    def test_a_layer_with_no_bindings(self) -> None:
        cfg = keyd_config.parse("[ids]\n8089:0019\n[main]\n")
        assert cfg.layers == {"main": ()}

    def test_rejects_a_file_that_does_not_begin_with_ids(self) -> None:
        """keyd's own requirement, and it rejects the whole file."""
        with pytest.raises(ConfigError):
            keyd_config.parse("[main]\nenter = noop\n")

    def test_rejects_a_binding_before_any_section(self) -> None:
        with pytest.raises(ConfigError):
            keyd_config.parse("enter = noop\n[ids]\n8089:0019\n")

    def test_rejects_a_malformed_id(self) -> None:
        with pytest.raises(ConfigError):
            keyd_config.parse("[ids]\nnot-an-id\n[main]\nenter = noop\n")

    def test_rejects_junk_in_a_layer(self) -> None:
        with pytest.raises(ConfigError):
            keyd_config.parse("[ids]\n8089:0019\n[main]\nnonsense\n")

    def test_rejects_an_unclosed_section_header(self) -> None:
        with pytest.raises(ConfigError):
            keyd_config.parse("[ids\n8089:0019\n")

    def test_rejects_empty_text(self) -> None:
        with pytest.raises(ConfigError):
            keyd_config.parse("")


class TestRender:

    def test_round_trips_through_parse(self) -> None:
        ids = [DeviceId("8089", "0019", kind="k")]
        bindings = [Binding("enter", "command(/usr/local/bin/press)"),
                    Binding("kpenter", "command(/usr/local/bin/press)")]
        cfg = keyd_config.parse(keyd_config.render(ids, bindings))
        assert cfg.ids == tuple(ids)
        assert cfg.bindings("main") == tuple(bindings)

    def test_accepts_ids_as_strings(self) -> None:
        out = keyd_config.render(["k:8089:0019"], [Binding("enter", "noop")])
        assert "k:8089:0019" in out

    def test_the_ids_section_comes_first(self) -> None:
        out = keyd_config.render(["8089:0019"], [Binding("enter", "noop")])
        sections = [ln for ln in out.splitlines() if ln.startswith("[")]
        assert sections[0] == "[ids]"

    def test_a_header_becomes_comment_lines(self) -> None:
        out = keyd_config.render(["8089:0019"], [Binding("enter", "noop")],
                                 header="one\ntwo")
        assert out.startswith("# one\n# two\n")

    def test_a_header_does_not_disturb_the_round_trip(self) -> None:
        out = keyd_config.render(["8089:0019"], [Binding("enter", "noop")],
                                 header="hello")
        assert keyd_config.parse(out).bindings("main") == (
            Binding("enter", "noop"),)

    def test_a_named_layer(self) -> None:
        out = keyd_config.render(["8089:0019"], [Binding("h", "left")],
                                 layer="nav")
        assert "[nav]" in out
        assert keyd_config.parse(out).bindings("nav") == (
            Binding("h", "left"),)


class TestKeyNamesFunction:

    def test_falls_back_to_the_vendored_table(self) -> None:
        assert keyd_config.key_names("/nonexistent/keyd") == (
            keyd_config.KEY_NAMES)

    @pytest.mark.skipif(shutil.which("keyd.rvaiya") is None,
                        reason="keyd is not installed here")
    def test_asks_the_installed_binary(self) -> None:
        assert {"enter", "kpenter", "f24"} <= keyd_config.key_names()


class TestValidate:

    def test_a_good_config_has_no_problems(self) -> None:
        assert keyd_config.validate(keyd_config.parse(MINIMAL)) == []

    def test_flags_an_unknown_key_name(self) -> None:
        cfg = keyd_config.parse("[ids]\n8089:0019\n[main]\nentre = noop\n")
        problems = keyd_config.validate(cfg)
        assert any("entre" in p for p in problems)

    def test_flags_an_unknown_action(self) -> None:
        cfg = keyd_config.parse("[ids]\n8089:0019\n[main]\nenter = f25\n")
        assert any("f25" in p for p in keyd_config.validate(cfg))

    def test_flags_the_trailing_hash_foot_gun(self) -> None:
        cfg = keyd_config.parse(
            "[ids]\n8089:0019\n[main]\nenter = f24 # why not\n")
        assert keyd_config.validate(cfg) != []

    def test_flags_an_unknown_action_form(self) -> None:
        cfg = keyd_config.parse(
            "[ids]\n8089:0019\n[main]\nenter = summon(demon)\n")
        assert any("summon" in p for p in keyd_config.validate(cfg))

    def test_accepts_every_documented_action(self) -> None:
        for name in sorted(keyd_config.ACTIONS - {"noop", "command"}):
            cfg = keyd_config.parse(
                f"[ids]\n8089:0019\n[main]\nenter = {name}(x)\n")
            assert keyd_config.validate(cfg) == [], name

    def test_flags_a_relative_command_path(self) -> None:
        """keyd runs the command from its own working directory."""
        cfg = keyd_config.parse(
            "[ids]\n8089:0019\n[main]\nenter = command(press.sh)\n")
        assert any("press.sh" in p for p in keyd_config.validate(cfg))

    def test_flags_the_wildcard(self) -> None:
        """Legal keyd, wrong here: it would claim the internal keyboard."""
        cfg = keyd_config.parse("[ids]\n*\n[main]\nenter = noop\n")
        assert keyd_config.validate(cfg) != []

    def test_flags_a_config_that_claims_nothing(self) -> None:
        cfg = keyd_config.parse("[ids]\n[main]\nenter = noop\n")
        assert keyd_config.validate(cfg) != []

    def test_flags_a_key_bound_twice_in_one_layer(self) -> None:
        cfg = keyd_config.parse(
            "[ids]\n8089:0019\n[main]\nenter = noop\nenter = f24\n")
        assert any("enter" in p for p in keyd_config.validate(cfg))

    def test_reports_every_problem_not_just_the_first(self) -> None:
        cfg = keyd_config.parse(
            "[ids]\n*\n[main]\nentre = noop\nenter = f25\n")
        assert len(keyd_config.validate(cfg)) >= 3

    def test_known_keys_can_be_overridden(self) -> None:
        """So a newer keyd's table can be used against an old config."""
        cfg = keyd_config.parse("[ids]\n8089:0019\n[main]\nenter = noop\n")
        assert keyd_config.validate(cfg, known_keys=["enter"]) == []
        assert keyd_config.validate(cfg, known_keys=["space"]) != []

    def test_every_problem_is_a_plain_string(self) -> None:
        cfg = keyd_config.parse("[ids]\n*\n[main]\nentre = f25\n")
        assert all(isinstance(p, str) for p in keyd_config.validate(cfg))


class TestCheckHookPermissions:
    """keyd runs the hook as root, so anyone who can write it is root.

    Every assertion here matches a phrase with a leading space, never a
    bare word.  pytest names ``tmp_path`` after the test function and
    the problems quote the path, so ``"writable" in problem`` is true
    for a test called ``test_a_group_writable_hook`` whatever the code
    does.  Three of these tests passed vacuously before that was
    noticed; a tmpdir path never contains a space, so the phrases do
    not collide with it.
    """

    def _hook(self, tmp_path: Path, mode: int = 0o755) -> Path:
        path = tmp_path / "press"
        path.write_text("#!/bin/sh\nexit 0\n")
        path.chmod(mode)
        return path

    def _about_the_file(self, problems: Iterable[str]) -> list[str]:
        return [p for p in problems if not p.startswith("the directory ")]

    def test_a_missing_hook(self, tmp_path: Path) -> None:
        problems = keyd_config.check_hook_permissions(
            str(tmp_path / "absent"))
        assert any(" does not exist" in p for p in problems)

    def test_a_hook_that_is_not_executable(self, tmp_path: Path) -> None:
        path = self._hook(tmp_path, 0o644)
        problems = keyd_config.check_hook_permissions(str(path))
        assert any(" is not executable" in p for p in problems)

    def test_an_executable_hook_is_not_flagged_for_it(
            self, tmp_path: Path) -> None:
        path = self._hook(tmp_path, 0o755)
        problems = keyd_config.check_hook_permissions(str(path))
        assert not any(" is not executable" in p for p in problems)

    def test_a_group_writable_hook(self, tmp_path: Path) -> None:
        path = self._hook(tmp_path, 0o775)
        problems = self._about_the_file(
            keyd_config.check_hook_permissions(str(path)))
        assert any(" is writable by group or other" in p for p in problems)

    def test_a_world_writable_hook(self, tmp_path: Path) -> None:
        path = self._hook(tmp_path, 0o777)
        problems = self._about_the_file(
            keyd_config.check_hook_permissions(str(path)))
        assert any(" is writable by group or other" in p for p in problems)

    def test_a_tight_hook_is_not_flagged_as_writable(
            self, tmp_path: Path) -> None:
        path = self._hook(tmp_path, 0o700)
        problems = self._about_the_file(
            keyd_config.check_hook_permissions(str(path)))
        assert not any(" is writable by group or other" in p
                       for p in problems)

    def test_a_hook_not_owned_by_root(self, tmp_path: Path) -> None:
        path = self._hook(tmp_path)
        problems = keyd_config.check_hook_permissions(str(path))
        assert any(" is owned by uid " in p for p in problems)

    def test_the_mode_is_quoted_so_the_operator_can_see_it(
            self, tmp_path: Path) -> None:
        path = self._hook(tmp_path, 0o777)
        problems = self._about_the_file(
            keyd_config.check_hook_permissions(str(path)))
        assert any("0777" in p for p in problems)

    def test_a_world_writable_parent_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "wide"
        d.mkdir(mode=0o777)
        d.chmod(0o777)
        path = self._hook(d)
        problems = keyd_config.check_hook_permissions(str(path))
        assert any(p.startswith("the directory ") and str(d) in p
                   for p in problems)

    def test_a_sticky_parent_directory_is_not_flagged(
            self, tmp_path: Path) -> None:
        """/tmp is 1777; sticky stops other users replacing the file."""
        d = tmp_path / "sticky"
        d.mkdir(mode=0o777)
        d.chmod(0o777 | stat.S_ISVTX)
        path = self._hook(d)
        problems = keyd_config.check_hook_permissions(str(path))
        assert not any(p.startswith("the directory ") for p in problems)

    def test_a_tight_parent_directory_is_not_flagged(
            self, tmp_path: Path) -> None:
        path = self._hook(tmp_path)
        problems = keyd_config.check_hook_permissions(str(path))
        assert not any(p.startswith("the directory ") for p in problems)

    def test_every_problem_is_a_plain_string(self, tmp_path: Path) -> None:
        path = self._hook(tmp_path, 0o666)
        problems = keyd_config.check_hook_permissions(str(path))
        assert all(isinstance(p, str) for p in problems)


class TestFindIdConflicts:

    def test_no_conflict_between_different_devices(self) -> None:
        configs = {
            "a.conf": keyd_config.parse(
                "[ids]\nk:8089:0019\n[main]\nenter = noop\n"),
            "b.conf": keyd_config.parse(
                "[ids]\nk:048d:c197\n[main]\nenter = noop\n")}
        assert keyd_config.find_id_conflicts(configs) == []

    def test_two_files_claiming_the_same_id(self) -> None:
        """keyd allows an id in one file only, and ignores the loser."""
        text = "[ids]\nk:8089:0019\n[main]\nenter = noop\n"
        configs = {"a.conf": keyd_config.parse(text),
                   "b.conf": keyd_config.parse(text)}
        problems = keyd_config.find_id_conflicts(configs)
        assert len(problems) == 1
        assert "a.conf" in problems[0] and "b.conf" in problems[0]

    def test_k_and_m_on_one_device_do_not_conflict(self) -> None:
        """They select different interfaces, so both can be managed."""
        configs = {
            "kbd.conf": keyd_config.parse(
                "[ids]\nk:8089:0019\n[main]\nenter = noop\n"),
            "mouse.conf": keyd_config.parse(
                "[ids]\nm:8089:0019\n[main]\nenter = noop\n")}
        assert keyd_config.find_id_conflicts(configs) == []

    def test_a_bare_id_conflicts_with_a_k_prefixed_one(self) -> None:
        configs = {
            "bare.conf": keyd_config.parse(
                "[ids]\n8089:0019\n[main]\nenter = noop\n"),
            "kbd.conf": keyd_config.parse(
                "[ids]\nk:8089:0019\n[main]\nenter = noop\n")}
        assert keyd_config.find_id_conflicts(configs) != []

    def test_a_wildcard_config_conflicts_with_an_explicit_keyboard(
            self) -> None:
        configs = {
            "all.conf": keyd_config.parse(
                "[ids]\n*\n[main]\nenter = noop\n"),
            "ours.conf": keyd_config.parse(
                "[ids]\nk:8089:0019\n[main]\nenter = noop\n")}
        assert keyd_config.find_id_conflicts(configs) != []

    def test_a_wildcard_that_excludes_us_does_not_conflict(self) -> None:
        configs = {
            "all.conf": keyd_config.parse(
                "[ids]\n*\n-8089:0019\n[main]\nenter = noop\n"),
            "ours.conf": keyd_config.parse(
                "[ids]\nk:8089:0019\n[main]\nenter = noop\n")}
        assert keyd_config.find_id_conflicts(configs) == []

    def test_a_single_config_never_conflicts_with_itself(self) -> None:
        configs = {"a.conf": keyd_config.parse(MINIMAL)}
        assert keyd_config.find_id_conflicts(configs) == []

    def test_no_configs_at_all(self) -> None:
        assert keyd_config.find_id_conflicts({}) == []


class TestShippedConfigText:
    """Checks that need no implementation, only the file."""

    def test_the_artifact_exists(self) -> None:
        assert SHIPPED.is_file()

    def test_it_keeps_the_f24_caveat(self) -> None:
        """If the xkb note goes, someone will enable f24 and lose a day."""
        text = SHIPPED.read_text()
        assert "fkeys(basic_13-24)" in text

    def test_the_f24_lines_stay_commented_out(self) -> None:
        for line in SHIPPED.read_text().splitlines():
            if "f24" in line:
                assert line.lstrip().startswith("#"), line

    def test_it_points_at_the_documentation(self) -> None:
        assert "docs/big-green-button.md" in SHIPPED.read_text()


class TestShippedConfig:
    """The anti-rot tests: the artifact we install, validated."""

    def _cfg(self) -> KeydConfig:
        return keyd_config.parse(SHIPPED.read_text())

    def test_it_parses(self) -> None:
        assert self._cfg().ids != ()

    def test_the_validator_is_happy_with_it(self) -> None:
        assert keyd_config.validate(self._cfg()) == []

    def test_it_claims_the_buttons_keyboard_interface(self) -> None:
        assert self._cfg().claims(
            button.VENDOR, button.PRODUCT, is_keyboard=True) is True

    def test_it_leaves_the_buttons_mouse_interface_alone(self) -> None:
        """8089:0019 is also js0; keyd calls mouse support experimental."""
        assert self._cfg().claims(
            button.VENDOR, button.PRODUCT, is_keyboard=False) is False

    def test_it_does_not_claim_the_laptops_internal_keyboard(self) -> None:
        """Getting this wrong locks the operator out of their own machine."""
        assert self._cfg().claims(
            "0001", "0001", is_keyboard=True) is False

    def test_it_uses_the_id_button_py_declares(self) -> None:
        assert [str(i) for i in self._cfg().ids] == [button.KEYD_ID]

    def test_it_binds_exactly_the_keys_the_button_sends(self) -> None:
        bound = {b.key for b in self._cfg().bindings("main")}
        assert bound == set(button.KEYS)

    def test_every_binding_runs_the_declared_hook(self) -> None:
        for b in self._cfg().bindings("main"):
            assert b.action_name == "command"
            assert b.action_arg == button.HOOK_PATH

    def test_it_names_one_hook(self) -> None:
        assert self._cfg().hook_paths() == (button.HOOK_PATH,)

    def test_it_does_not_conflict_with_itself(self) -> None:
        assert keyd_config.find_id_conflicts(
            {button.KEYD_CONFIG_NAME: self._cfg()}) == []


class TestShippedHookFile:
    """Checks that need no implementation, only the file."""

    def test_the_hook_exists(self) -> None:
        assert SHIPPED_HOOK.is_file()

    def test_the_repo_copy_has_its_executable_bit(self) -> None:
        """git tracks the mode, so install -m 0755 has something to copy."""
        assert os.access(SHIPPED_HOOK, os.X_OK)

    def test_the_hook_is_a_shell_script(self) -> None:
        assert SHIPPED_HOOK.read_text().startswith("#!/bin/sh")

    def test_the_hook_marks_the_line_to_edit(self) -> None:
        """OPERATOR_CMD is the one line the operator has to fill in."""
        assert "OPERATOR_CMD" in SHIPPED_HOOK.read_text()


class TestShippedHook:

    def test_the_repo_copy_is_executable_and_not_group_writable(self) -> None:
        """Only the hook's own mode is checked here.

        Not its ownership: the repo copy belongs to the operator and
        only the installed copy under /usr/local/bin must be root's.
        Not its parent directories either -- this checkout is group
        writable, which is a fact about the checkout and not a defect
        in the hook.
        """
        problems = [p for p in
                    keyd_config.check_hook_permissions(str(SHIPPED_HOOK))
                    if not p.startswith("the directory ")]
        assert not any(" is not executable" in p for p in problems)
        assert not any(" is writable by group or other" in p
                       for p in problems)

    def test_the_installed_hook_is_safe_if_it_is_there(self) -> None:
        """Skips on a machine where nobody has run the install yet."""
        if not Path(button.HOOK_PATH).exists():
            pytest.skip("hook not installed")
        assert keyd_config.check_hook_permissions(button.HOOK_PATH) == []
