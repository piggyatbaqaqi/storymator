"""Tests for ``hook/big-green-button-press``.

Named for the artifact rather than a module, because the hook is a
shell script: there is no ``hook.py``.  The tests run it for real, with
OPERATOR_CMD and LOG pointed at a tmpdir, because the interesting part
is the environment it hands its child -- keyd gives it root's
environment, which has no X authority, no bus and no HOME, and getting
that wrong means the button fires and nothing visible happens.

These run as the operator, so the setpriv branch is not exercised.
That path needs root and the real button; ``docs/big-green-button.md``
has the manual check.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "hook" / "big-green-button-press"
RUNTIME = Path(f"/run/user/{os.getuid()}")


def _code_lines() -> list[str]:
    """The hook's lines with whole-line comments and blanks dropped."""
    return [line for line in HOOK.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def _session_environment() -> dict[str, str]:
    """What the operator's systemd user manager is handing out.

    The hook's source of truth, so the tests compare against it rather
    than against values of their own.
    """
    try:
        done = subprocess.run(
            ["systemctl", "--user", "show-environment"],
            capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return {}
    if done.returncode != 0:
        return {}
    return dict(
        line.split("=", 1) for line in done.stdout.splitlines()
        if "=" in line)


def _run(tmp_path: Path, command: str,
         log: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ,
               OPERATOR_CMD=command,
               LOG=str(log if log is not None else tmp_path / "press.log"))
    return subprocess.run([str(HOOK)], env=env, capture_output=True,
                          text=True, timeout=30, check=False)


class TestItRuns:

    def test_the_hook_is_executable(self) -> None:
        assert os.access(HOOK, os.X_OK)

    def test_it_runs_the_operator_command(self, tmp_path: Path) -> None:
        marker = tmp_path / "fired"
        done = _run(tmp_path, f"touch {marker}")
        assert done.returncode == 0, done.stderr
        assert marker.exists()

    def test_it_logs_the_press(self, tmp_path: Path) -> None:
        log = tmp_path / "press.log"
        _run(tmp_path, "true", log=log)
        assert "press" in log.read_text()

    def test_it_appends_rather_than_truncating(self, tmp_path: Path) -> None:
        log = tmp_path / "press.log"
        _run(tmp_path, "true", log=log)
        _run(tmp_path, "true", log=log)
        assert len(log.read_text().splitlines()) == 2

    def test_an_unwritable_log_does_not_stop_the_command(
            self, tmp_path: Path) -> None:
        """A full disk must not cost the operator their button."""
        marker = tmp_path / "fired"
        done = _run(tmp_path, f"touch {marker}",
                    log=Path("/proc/nonexistent/press.log"))
        assert done.returncode == 0, done.stderr
        assert marker.exists()

    def test_it_says_nothing_on_stderr_when_the_log_is_unwritable(
            self, tmp_path: Path) -> None:
        """keyd sends stdio to /dev/null, but a hand test should be quiet."""
        done = _run(tmp_path, "true",
                    log=Path("/proc/nonexistent/press.log"))
        assert done.stderr == ""

    def test_a_failing_command_is_reported_in_the_exit_status(
            self, tmp_path: Path) -> None:
        assert _run(tmp_path, "exit 3").returncode == 3


class TestTheChildEnvironment:
    """What the operator's command actually inherits."""

    def _env_of_child(self, tmp_path: Path, names: str) -> list[str]:
        out = tmp_path / "env.txt"
        done = _run(tmp_path, f"printenv {names} > {out}")
        assert done.returncode == 0, done.stderr
        return out.read_text().splitlines()

    def test_display_is_set(self, tmp_path: Path) -> None:
        assert self._env_of_child(tmp_path, "DISPLAY") == [":0"]

    def test_xdg_runtime_dir_points_at_our_own(self, tmp_path: Path) -> None:
        assert self._env_of_child(
            tmp_path, "XDG_RUNTIME_DIR") == [str(RUNTIME)]

    def test_the_dbus_address_is_under_the_runtime_dir(
            self, tmp_path: Path) -> None:
        got = self._env_of_child(tmp_path, "DBUS_SESSION_BUS_ADDRESS")
        assert got == [f"unix:path={RUNTIME}/bus"]

    def test_home_is_the_operators_home(self, tmp_path: Path) -> None:
        assert self._env_of_child(tmp_path, "HOME") == [
            os.path.expanduser("~")]

    def test_wayland_display_is_set(self, tmp_path: Path) -> None:
        """A Wayland-native command needs this, not just DISPLAY."""
        if "WAYLAND_DISPLAY" not in _session_environment():
            pytest.skip("no WAYLAND_DISPLAY in the session")
        assert self._env_of_child(tmp_path, "WAYLAND_DISPLAY") == [
            _session_environment()["WAYLAND_DISPLAY"]]

    def test_xauthority_names_a_file_that_exists(self, tmp_path: Path) -> None:
        """The whole point: XWayland refuses a client with no authority."""
        if "XAUTHORITY" not in _session_environment():
            pytest.skip("no XAUTHORITY in the session")
        got = self._env_of_child(tmp_path, "XAUTHORITY")
        assert got and Path(got[0]).is_file()

    def test_the_values_come_from_the_live_session(
            self, tmp_path: Path) -> None:
        """Not from a guess.  DISPLAY and the auth cookie's filename both
        change between logins, so the hook must read them rather than
        remember them."""
        session = _session_environment()
        wanted = [k for k in ("DISPLAY", "XAUTHORITY") if k in session]
        if not wanted:
            pytest.skip("no graphical session to compare against")
        got = self._env_of_child(tmp_path, " ".join(wanted))
        assert got == [session[k] for k in wanted]


class TestHowItFindsTheSession:
    """Read rather than run: the mechanism, and its fallback."""

    def test_it_asks_the_systemd_user_manager(self) -> None:
        assert "systemctl --user show-environment" in HOOK.read_text()

    def test_it_never_evals_those_values(self) -> None:
        """show-environment is KEY=value; eval would make a value code.

        Checks the code lines only.  The hook's own comments say the
        word, and matching those is the same trap that made three
        hook-permission tests pass vacuously in keyd_config_test.py.
        """
        assert not any("eval" in line for line in _code_lines())

    def test_it_passes_them_as_whole_argv_entries(self) -> None:
        assert 'set -- "$@" "$line"' in HOOK.read_text()

    def test_it_keeps_the_glob_as_a_fallback(self) -> None:
        """For a press with no systemd user manager to ask."""
        assert ".mutter-Xwaylandauth.*" in HOOK.read_text()

    def test_it_does_not_hardcode_a_display_outside_the_fallback(
            self) -> None:
        """:0 may appear in the fallback and in OPERATOR_CMD, but the hook
        must not assign DISPLAY_NAME=:0 and use it unconditionally."""
        assert "DISPLAY_NAME" not in HOOK.read_text()


class TestTheDroppedGuard:

    def test_dropped_skips_the_logging(self, tmp_path: Path) -> None:
        """The re-exec must not log the same press a second time."""
        log = tmp_path / "press.log"
        env = dict(os.environ, OPERATOR_CMD="true", LOG=str(log))
        subprocess.run([str(HOOK), "--dropped"], env=env, check=True,
                       capture_output=True, timeout=30)
        assert not log.exists()

    def test_dropped_still_runs_the_command(self, tmp_path: Path) -> None:
        marker = tmp_path / "fired"
        env = dict(os.environ, OPERATOR_CMD=f"touch {marker}",
                   LOG=str(tmp_path / "press.log"))
        subprocess.run([str(HOOK), "--dropped"], env=env, check=True,
                       capture_output=True, timeout=30)
        assert marker.exists()


class TestTheRootBranch:
    """Read rather than run: these tests are not root."""

    def test_it_drops_privilege_with_setpriv(self) -> None:
        assert "setpriv --reuid" in HOOK.read_text()

    def test_setpriv_is_installed(self) -> None:
        assert shutil.which("setpriv") is not None

    def test_it_initialises_the_supplementary_groups(self) -> None:
        """Without --init-groups the command keeps root's group list."""
        assert "--init-groups" in HOOK.read_text()

    def test_it_only_drops_when_it_is_actually_root(self) -> None:
        assert '[ "$(id -u)" -eq 0 ]' in HOOK.read_text()

    def test_it_records_why_repeats_do_not_re_fire_it(self) -> None:
        """The 28-repeats-per-hold measurement is the reason this is safe."""
        assert "Ignore repeat events" in HOOK.read_text()
