"""Every Python tool in ``bin/`` and ``fixes/`` parses strictly.

See ``docs/bin-argparse-strict.md``.  The behavioral guard refuses to
launch a tool that does not call argparse, because a lenient tool handed
a bogus flag runs for real -- and some of these delete things.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
PRAGMA = "pragma: argparse-passthrough"


def discover() -> list[Path]:
    """Python tools, by shebang: they are extensionless and hyphenated."""
    found = []
    for directory in (ROOT / "bin", ROOT / "fixes"):
        for path in sorted(directory.iterdir()):
            if not path.is_file() or path.name.endswith("_test.py"):
                continue
            with path.open("rb") as handle:
                first = handle.readline()
            if first.startswith(b"#!") and b"python" in first:
                found.append(path)
    return found


def unpragmaed_calls(source: str) -> list[int]:
    """Lines calling parse_known_args without the pragma on or above."""
    lines = source.splitlines()
    bad = []
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "parse_known_args"):
            nearby = lines[max(node.lineno - 2, 0):node.lineno]
            if not any(PRAGMA in line for line in nearby):
                bad.append(node.lineno)
    return bad


def calls_apply_env(source: str) -> bool:
    """True when the source calls env_flags.apply_env."""
    return any(isinstance(node, ast.Call)
               and isinstance(node.func, ast.Name)
               and node.func.id == "apply_env"
               for node in ast.walk(ast.parse(source)))


def uses_argparse(source: str) -> bool:
    """True when the source calls parse_args or a marked passthrough."""
    return any(isinstance(node, ast.Call)
               and isinstance(node.func, ast.Attribute)
               and node.func.attr in ("parse_args", "parse_known_args")
               for node in ast.walk(ast.parse(source)))


TOOLS = [pytest.param(path, id=path.name) for path in discover()]
# Exempt from the environment layer: see docs/bin-argparse-strict.md.
NO_ENV_LAYER = {"prune-duplicate-captures"}
# Still to migrate to apply_env.
ENV_PENDING = {"big-green-button"}


def env_cases() -> list[Any]:
    """Tools owing an environment layer, strict xfail where pending."""
    cases = []
    for path in discover():
        if path.name in NO_ENV_LAYER:
            continue
        marks = []
        if path.name in ENV_PENDING:
            marks = [pytest.mark.xfail(strict=True,
                                       reason="not migrated to apply_env")]
        cases.append(pytest.param(path, id=path.name, marks=marks))
    return cases


def test_discovery_finds_both_directories_and_skips_bash() -> None:
    names = {path.name for path in discover()}
    assert {"colour-dropout", "prune-duplicate-captures"} <= names
    assert "backup-storymator" not in names
    assert "colour_dropout_test.py" not in names


def test_guard_catches_an_unmarked_call() -> None:
    assert unpragmaed_calls("a, b = p.parse_known_args()\n") == [1]


@pytest.mark.parametrize("source", [
    f"# {PRAGMA} -- forwards extras\na, b = p.parse_known_args()\n",
    f"a, b = p.parse_known_args()  # {PRAGMA} -- forwards extras\n",
    "# parse_known_args() is only mentioned here\n",
])
def test_guard_allows_marked_calls_and_ignores_comments(source: str) -> None:
    assert unpragmaed_calls(source) == []


def test_argparse_detection_sees_through_hand_rolled_checks() -> None:
    assert uses_argparse("args = ap.parse_args(argv)\n")
    assert not uses_argparse('dry = "--dry-run" in argv\n')


def test_apply_env_detection() -> None:
    assert calls_apply_env('apply_env(ap, "TOOL")\n')
    assert not calls_apply_env("# apply_env is only mentioned here\n")


@pytest.mark.parametrize("path", env_cases())
def test_tool_has_an_environment_layer(path: Path) -> None:
    assert calls_apply_env(path.read_text())


@pytest.mark.parametrize("path", TOOLS)
def test_no_unpragmaed_parse_known_args(path: Path) -> None:
    assert unpragmaed_calls(path.read_text()) == []


@pytest.mark.parametrize("path", TOOLS)
def test_tool_parses_with_argparse(path: Path) -> None:
    assert uses_argparse(path.read_text())


@pytest.mark.parametrize("path", TOOLS)
def test_cli_rejects_unknown_flag(path: Path, tmp_path: Path) -> None:
    assert uses_argparse(path.read_text()), (
        f"not launching {path.name}: without argparse it would run for real")
    done = subprocess.run(
        [sys.executable, str(path), "--no-such-flag-xyz"], cwd=tmp_path,
        capture_output=True, text=True, timeout=120, check=False)
    assert done.returncode == 2, done.stderr
