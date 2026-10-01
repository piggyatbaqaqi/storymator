"""Tests for ``bin/big-green-button``.

The script is hyphenated and extensionless, so it is loaded by path
rather than imported by name -- the same trick as
``collect_captures_test.py``.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import types
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from big_green_button import keyd_config                      # noqa: E402
from big_green_button.input_devices import InputDevice        # noqa: E402


def _load() -> types.ModuleType:
    path = str(_HERE / "big-green-button")
    spec = importlib.util.spec_from_loader(
        "big_green_button_cli",
        importlib.machinery.SourceFileLoader("big_green_button_cli", path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before executing: ``@dataclass`` resolves its annotations
    # through ``sys.modules[cls.__module__]``, which is None for a module
    # that was only ever handed to exec_module.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bgb = _load()

NEEDS_IMPL = pytest.mark.xfail(raises=NotImplementedError, strict=True,
                               reason="skeleton; implementation to follow")

KBD = InputDevice(
    name="LinTx USB Keyboard", vendor="8089", product="0019",
    uniq="BEC8023D", handlers=("sysrq", "kbd", "event24", "leds"))
MOUSE = InputDevice(
    name="LinTx USB Keyboard Mouse", vendor="8089", product="0019",
    uniq="BEC8023D", handlers=("mouse2", "event25", "js0"))

OURS = "[ids]\nk:8089:0019\n[main]\nenter = command(/usr/local/bin/x)\n"
BARE = "[ids]\n8089:0019\n[main]\nenter = command(/usr/local/bin/x)\n"


class TestEnvDefault:
    """CLI --flag, then BIG_GREEN_BUTTON_FLAG, then the default."""

    def test_returns_the_default_when_the_environment_is_quiet(
            self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("BIG_GREEN_BUTTON_KEYD_DIR", raising=False)
        assert bgb.env_default("keyd-dir", "/etc/keyd") == "/etc/keyd"

    def test_the_environment_beats_the_default(
            self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BIG_GREEN_BUTTON_KEYD_DIR", "/tmp/keyd")
        assert bgb.env_default("keyd-dir", "/etc/keyd") == "/tmp/keyd"

    def test_hyphens_become_underscores(
            self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BIG_GREEN_BUTTON_KEYD_DIR", "/tmp/keyd")
        assert bgb.env_default("keyd-dir", "/x") == "/tmp/keyd"

    def test_an_empty_variable_is_honoured_not_ignored(
            self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Setting it to nothing is a choice; argparse will complain."""
        monkeypatch.setenv("BIG_GREEN_BUTTON_KEYD_DIR", "")
        assert bgb.env_default("keyd-dir", "/etc/keyd") == ""

    def test_the_prefix_is_the_documented_one(self) -> None:
        assert bgb.ENV_PREFIX == "BIG_GREEN_BUTTON_"


class TestShippedConfigConstant:

    def test_points_at_the_artifact_in_the_repo(self) -> None:
        assert bgb.SHIPPED_CONFIG.is_file()
        assert bgb.SHIPPED_CONFIG.name == "big-green-button.conf"

    def test_the_default_keyd_dir_is_etc_keyd(self) -> None:
        assert bgb.DEFAULT_KEYD_DIR == "/etc/keyd"


@NEEDS_IMPL
class TestBuildParser:

    def test_accepts_the_three_subcommands(self) -> None:
        for sub in ("check", "render", "devices"):
            assert bgb.build_parser().parse_args([sub]).func is not None

    def test_check_takes_a_keyd_dir(self) -> None:
        args = bgb.build_parser().parse_args(["check", "--keyd-dir", "/tmp"])
        assert args.keyd_dir == "/tmp"

    def test_the_keyd_dir_default_comes_from_the_environment(
            self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BIG_GREEN_BUTTON_KEYD_DIR", "/tmp/keyd")
        args = bgb.build_parser().parse_args(["check"])
        assert args.keyd_dir == "/tmp/keyd"

    def test_the_flag_beats_the_environment(
            self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BIG_GREEN_BUTTON_KEYD_DIR", "/tmp/keyd")
        args = bgb.build_parser().parse_args(["check", "--keyd-dir", "/srv"])
        assert args.keyd_dir == "/srv"

    def test_rejects_an_unknown_flag(self) -> None:
        """The whole point of parse_args over parse_known_args."""
        with pytest.raises(SystemExit):
            bgb.build_parser().parse_args(["check", "--keyd-dirr", "/tmp"])

    def test_rejects_an_unknown_subcommand(self) -> None:
        with pytest.raises(SystemExit):
            bgb.build_parser().parse_args(["frobnicate"])

    def test_requires_a_subcommand(self) -> None:
        with pytest.raises(SystemExit):
            bgb.build_parser().parse_args([])


@NEEDS_IMPL
class TestLoadKeydDir:

    def test_reads_every_conf_file(self, tmp_path: Path) -> None:
        (tmp_path / "a.conf").write_text(OURS)
        (tmp_path / "b.conf").write_text(
            "[ids]\nk:048d:c197\n[main]\nenter = noop\n")
        configs, problems = bgb.load_keyd_dir(str(tmp_path))
        assert set(configs) == {"a.conf", "b.conf"}
        assert problems == []

    def test_ignores_files_that_are_not_conf(self, tmp_path: Path) -> None:
        """keyd loads only *.conf, so neither should we."""
        (tmp_path / "a.conf").write_text(OURS)
        (tmp_path / "notes.txt").write_text("garbage")
        (tmp_path / "a.conf.bak").write_text("garbage")
        configs, problems = bgb.load_keyd_dir(str(tmp_path))
        assert set(configs) == {"a.conf"}
        assert problems == []

    def test_a_broken_file_is_a_problem_not_an_exception(
            self, tmp_path: Path) -> None:
        """One bad file must not hide the rest of the directory."""
        (tmp_path / "a.conf").write_text(OURS)
        (tmp_path / "bad.conf").write_text("[main]\nenter = noop\n")
        configs, problems = bgb.load_keyd_dir(str(tmp_path))
        assert set(configs) == {"a.conf"}
        assert any("bad.conf" in p for p in problems)

    def test_an_empty_directory(self, tmp_path: Path) -> None:
        assert bgb.load_keyd_dir(str(tmp_path)) == ({}, [])

    def test_a_missing_directory_is_a_problem(self, tmp_path: Path) -> None:
        configs, problems = bgb.load_keyd_dir(str(tmp_path / "absent"))
        assert configs == {}
        assert problems != []


@NEEDS_IMPL
class TestBuildReport:

    def _ours(self) -> dict[str, keyd_config.KeydConfig]:
        return {"big-green-button.conf": keyd_config.parse(OURS)}

    def test_a_healthy_rig_has_no_problems(self) -> None:
        report = bgb.build_report(self._ours(), [KBD, MOUSE],
                                  check_hooks=False)
        assert report.problems == ()

    def test_it_says_something_for_the_operator_to_read(self) -> None:
        report = bgb.build_report(self._ours(), [KBD, MOUSE],
                                  check_hooks=False)
        assert any("8089:0019" in ln for ln in report.lines)

    def test_names_the_config_that_claims_the_button(self) -> None:
        report = bgb.build_report(self._ours(), [KBD], check_hooks=False)
        assert any("big-green-button.conf" in ln for ln in report.lines)

    def test_an_unplugged_button_is_a_problem(self) -> None:
        report = bgb.build_report(self._ours(), [], check_hooks=False)
        assert any("attach" in p or "plug" in p for p in report.problems)

    def test_no_config_claiming_the_button_is_a_problem(self) -> None:
        """This is the failure that leaves the button typing Return."""
        report = bgb.build_report({}, [KBD, MOUSE], check_hooks=False)
        assert report.problems != ()

    def test_a_config_claiming_the_mouse_interface_is_a_problem(self) -> None:
        configs = {"bare.conf": keyd_config.parse(BARE)}
        report = bgb.build_report(configs, [KBD, MOUSE], check_hooks=False)
        assert any("mouse" in p or "js0" in p for p in report.problems)

    def test_an_invalid_config_is_a_problem(self) -> None:
        configs = {"ours.conf": keyd_config.parse(
            "[ids]\nk:8089:0019\n[main]\nentre = noop\n")}
        report = bgb.build_report(configs, [KBD], check_hooks=False)
        assert any("entre" in p for p in report.problems)

    def test_two_configs_claiming_the_button_is_a_problem(self) -> None:
        configs = {"a.conf": keyd_config.parse(OURS),
                   "b.conf": keyd_config.parse(OURS)}
        report = bgb.build_report(configs, [KBD], check_hooks=False)
        assert report.problems != ()

    def test_drift_from_the_repo_copy_is_a_problem(self) -> None:
        shipped = keyd_config.parse(
            bgb.SHIPPED_CONFIG.read_text())
        report = bgb.build_report(self._ours(), [KBD], shipped=shipped,
                                  check_hooks=False)
        assert any("repo" in p or "match" in p for p in report.problems)

    def test_an_identical_installed_copy_does_not_drift(self) -> None:
        """Comments differ between repo and /etc all the time; ignore them."""
        shipped = keyd_config.parse(bgb.SHIPPED_CONFIG.read_text())
        configs = {"big-green-button.conf": shipped}
        report = bgb.build_report(configs, [KBD], shipped=shipped,
                                  check_hooks=False)
        assert report.problems == ()

    def test_check_hooks_looks_at_the_hook(self) -> None:
        """/usr/local/bin/x does not exist, so this must be noticed."""
        report = bgb.build_report(self._ours(), [KBD], check_hooks=True)
        assert any("/usr/local/bin/x" in p for p in report.problems)

    def test_every_line_and_problem_is_a_plain_string(self) -> None:
        report = bgb.build_report({}, [], check_hooks=False)
        assert all(isinstance(x, str)
                   for x in (*report.lines, *report.problems))


@NEEDS_IMPL
class TestCmdRender:

    def test_prints_the_shipped_config(
            self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = bgb.cmd_render(bgb.build_parser().parse_args(["render"]))
        out = capsys.readouterr().out
        assert rc == 0
        assert "k:8089:0019" in out

    def test_what_it_prints_parses(
            self, capsys: pytest.CaptureFixture[str]) -> None:
        """It is meant to be piped into `sudo tee /etc/keyd/...`."""
        bgb.cmd_render(bgb.build_parser().parse_args(["render"]))
        out = capsys.readouterr().out
        assert keyd_config.validate(keyd_config.parse(out)) == []


@NEEDS_IMPL
class TestCmdDevices:

    def test_prints_a_line_about_the_bus(
            self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = bgb.cmd_devices(bgb.build_parser().parse_args(["devices"]))
        assert rc in (0, 1)
        assert capsys.readouterr().out.strip() != ""


@NEEDS_IMPL
class TestCmdCheck:

    def test_zero_when_everything_is_in_order(
            self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (tmp_path / "big-green-button.conf").write_text(
            bgb.SHIPPED_CONFIG.read_text())
        rc = bgb.cmd_check(bgb.build_parser().parse_args(
            ["check", "--keyd-dir", str(tmp_path)]))
        problems = [ln for ln in capsys.readouterr().out.splitlines()
                    if ln.startswith("problem")]
        # Zero only if the button is attached and the hook installed;
        # otherwise the problems must say which, not crash.
        assert rc in (0, 1)
        assert rc == 0 or problems != []

    def test_nonzero_on_an_empty_keyd_directory(
            self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        rc = bgb.cmd_check(bgb.build_parser().parse_args(
            ["check", "--keyd-dir", str(tmp_path)]))
        assert rc == 1
        assert capsys.readouterr().out.strip() != ""

    def test_does_not_raise_on_a_broken_config(
            self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (tmp_path / "bad.conf").write_text("[main]\nenter = noop\n")
        rc = bgb.cmd_check(bgb.build_parser().parse_args(
            ["check", "--keyd-dir", str(tmp_path)]))
        assert rc == 1
        assert "bad.conf" in capsys.readouterr().out


@NEEDS_IMPL
class TestMain:

    def test_dispatches_to_the_subcommand(
            self, capsys: pytest.CaptureFixture[str]) -> None:
        assert bgb.main(["render"]) == 0
        assert "k:8089:0019" in capsys.readouterr().out

    def test_returns_the_subcommands_exit_code(self, tmp_path: Path) -> None:
        assert bgb.main(["check", "--keyd-dir", str(tmp_path)]) == 1

    def test_an_unknown_flag_exits_two(self) -> None:
        with pytest.raises(SystemExit) as caught:
            bgb.main(["check", "--nope"])
        assert caught.value.code == 2

    def test_reads_argv_when_given_nothing(
            self, monkeypatch: pytest.MonkeyPatch,
            capsys: pytest.CaptureFixture[str]) -> None:
        monkeypatch.setattr(sys, "argv", ["big-green-button", "render"])
        assert bgb.main() == 0
        assert capsys.readouterr().out != ""
