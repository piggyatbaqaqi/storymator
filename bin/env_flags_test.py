"""Tests for ``bin/env_flags.py`` and each tool's use of it."""

from __future__ import annotations

import argparse
import functools
import importlib.machinery
import importlib.util
import os
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from env_flags import apply_env

_HERE = os.path.dirname(os.path.abspath(__file__))
# Each tool leaves this set in its own commit.
MIGRATING = {"collect-captures", "colour-dropout"}


def tool_marks(name: str) -> list[Any]:
    """Strict xfail for a tool until it has been migrated."""
    if name not in MIGRATING:
        return []
    return [pytest.mark.xfail(strict=True,
                              reason="tool not migrated to apply_env yet")]


def parser_with_flags() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("frame", nargs="?")
    ap.add_argument("--name", default="fallback")
    ap.add_argument("--box-size", type=int, default=400)
    ap.add_argument("--dpi", type=float, default=600.0)
    ap.add_argument("--csv", type=Path, default=None)
    ap.add_argument("--invert", action="store_true")
    ap.add_argument("--mode", choices=["fast", "slow"], default="fast")
    return ap


def applied() -> argparse.ArgumentParser:
    ap = parser_with_flags()
    apply_env(ap, "TOOL")
    return ap


def test_no_environment_leaves_the_hardcoded_defaults() -> None:
    args = applied().parse_args([])
    assert (args.name, args.box_size, args.dpi, args.csv, args.invert,
            args.mode) == ("fallback", 400, 600.0, None, False, "fast")


@pytest.mark.parametrize("variable, text, dest, value", [
    ("TOOL_NAME", "from env", "name", "from env"),
    ("TOOL_BOX_SIZE", "12", "box_size", 12),
    ("TOOL_DPI", "1200.5", "dpi", 1200.5),
    ("TOOL_CSV", "out.csv", "csv", Path("out.csv")),
    ("TOOL_MODE", "slow", "mode", "slow"),
])
def test_environment_supplies_a_converted_value(
        monkeypatch: pytest.MonkeyPatch, variable: str, text: str,
        dest: str, value: Any) -> None:
    monkeypatch.setenv(variable, text)
    assert getattr(applied().parse_args([]), dest) == value


@pytest.mark.parametrize("text, value", [
    ("1", True), ("true", True), ("YES", True), ("on", True),
    ("0", False), ("false", False), ("No", False), ("OFF", False),
])
def test_boolean_flags_read_words(monkeypatch: pytest.MonkeyPatch,
                                  text: str, value: bool) -> None:
    monkeypatch.setenv("TOOL_INVERT", text)
    assert applied().parse_args([]).invert is value


def test_command_line_beats_environment(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOOL_BOX_SIZE", "12")
    assert applied().parse_args(["--box-size", "99"]).box_size == 99


def test_command_line_means_a_bad_environment_value_is_never_read(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOOL_BOX_SIZE", "not a number")
    assert applied().parse_args(["--box-size", "99"]).box_size == 99


def test_store_true_on_the_command_line_beats_a_false_environment(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOOL_INVERT", "0")
    assert applied().parse_args(["--invert"]).invert is True


@pytest.mark.parametrize("variable, text", [
    ("TOOL_BOX_SIZE", "not a number"),
    ("TOOL_DPI", "wide"),
    ("TOOL_MODE", "medium"),
    ("TOOL_INVERT", "maybe"),
])
def test_bad_value_exits_2_and_names_the_variable(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        variable: str, text: str) -> None:
    monkeypatch.setenv(variable, text)
    with pytest.raises(SystemExit) as caught:
        applied().parse_args([])
    assert caught.value.code == 2
    assert variable in capsys.readouterr().err


def test_empty_value_counts_as_unset(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """So that ``TOOL_BOX_SIZE= tool`` turns a setting off for one run."""
    monkeypatch.setenv("TOOL_BOX_SIZE", "")
    assert applied().parse_args([]).box_size == 400


def test_positionals_and_help_are_left_alone(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOOL_FRAME", "from env")
    monkeypatch.setenv("TOOL_HELP", "1")
    assert applied().parse_args([]).frame is None


def test_environment_satisfies_a_required_flag(
        monkeypatch: pytest.MonkeyPatch) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    monkeypatch.setenv("TOOL_DEST", "there")
    apply_env(ap, "TOOL")
    assert ap.parse_args([]).dest == "there"


def test_required_flag_is_still_required_without_the_environment() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    apply_env(ap, "TOOL")
    with pytest.raises(SystemExit):
        ap.parse_args([])


def test_subcommand_flags_are_covered(
        monkeypatch: pytest.MonkeyPatch) -> None:
    ap = argparse.ArgumentParser()
    subs = ap.add_subparsers(dest="command", required=True)
    subs.add_parser("check").add_argument("--keyd-dir", default="/etc")
    monkeypatch.setenv("TOOL_KEYD_DIR", "/tmp/keyd")
    apply_env(ap, "TOOL")
    assert ap.parse_args(["check"]).keyd_dir == "/tmp/keyd"


@pytest.mark.parametrize("kwargs", [
    {"action": "append"},
    {"nargs": "+"},
    {"action": "count"},
])
def test_unsupported_flag_must_be_exempted_by_name(
        kwargs: dict[str, Any]) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peg", **kwargs)
    with pytest.raises(ValueError, match="--peg"):
        apply_env(ap, "TOOL")


def test_exempt_flags_ignore_the_environment(
        monkeypatch: pytest.MonkeyPatch) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peg", action="append")
    ap.add_argument("--dry-run", action="store_true")
    monkeypatch.setenv("TOOL_PEG", "1,2")
    monkeypatch.setenv("TOOL_DRY_RUN", "1")
    apply_env(ap, "TOOL", exempt={"peg", "dry_run"})
    args = ap.parse_args([])
    assert args.peg is None
    assert args.dry_run is False


def test_exempting_a_flag_that_does_not_exist_is_an_error() -> None:
    """A typo here would quietly un-exempt the real flag."""
    with pytest.raises(ValueError, match="dry_rn"):
        apply_env(parser_with_flags(), "TOOL", exempt={"dry_rn"})


@functools.cache
def tool(name: str) -> types.ModuleType:
    path = os.path.join(_HERE, name)
    module_name = name.replace("-", "_") + "_under_env_test"
    loader = importlib.machinery.SourceFileLoader(module_name, path)
    spec = importlib.util.spec_from_loader(module_name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module      # dataclasses look themselves up
    loader.exec_module(module)
    return module


# name, positional arguments, environment prefix
Tool = tuple[str, list[str], str]
PEG: Tool = ("make-peg-targets", [], "MAKE_PEG_TARGETS")
INK: Tool = ("measure-ink", ["f.png"], "MEASURE_INK")
PUNCH: Tool = ("measure-punch-tolerance", [], "MEASURE_PUNCH_TOLERANCE")
FOCUS: Tool = ("score-focus", ["f.png"], "SCORE_FOCUS")
COLLECT: Tool = ("collect-captures", [], "COLLECT_CAPTURES")
DROPOUT: Tool = ("colour-dropout", ["in.png", "out.png"], "COLOUR_DROPOUT")
BUTTON: Tool = ("big-green-button", ["check"], "BIG_GREEN_BUTTON")

# tool, flag's dest, environment value, parsed value
FLAGS: list[tuple[Tool, str, str, Any]] = [
    (PEG, "out", "x.png", "x.png"),
    (PEG, "squares", "5", 5),
    (PEG, "square_mm", "10.5", 10.5),
    (PEG, "marker_mm", "7.5", 7.5),
    (PEG, "count", "2", 2),
    (PEG, "sheet_mm", "100x200", "100x200"),
    (PEG, "px_per_mm", "30", 30.0),
    (PEG, "cut_margin_mm", "4", 4.0),
    (PEG, "dictionary", "DICT_4X4_50", "DICT_4X4_50"),
    (PEG, "serial", "s1", "s1"),
    (PEG, "registry", "r.json", "r.json"),
    (PEG, "first_id", "9", 9),
    (PEG, "caliper_mm", "150", 150.0),
    (INK, "calibration", "c.json", "c.json"),
    (INK, "name", "Dykem", "Dykem"),
    (INK, "radius", "30", 30),
    (INK, "into", "c.json", "c.json"),
    (PUNCH, "dpi", "1200", 1200.0),
    (PUNCH, "invert", "1", True),
    (PUNCH, "csv", "x.csv", Path("x.csv")),
    (FOCUS, "box", "200", 200),
    (COLLECT, "session", "s1", "s1"),
    (COLLECT, "since_minutes", "5", 5.0),
    (DROPOUT, "white_percentile", "80", 80.0),
    (DROPOUT, "white_level", "0.9", 0.9),
    (DROPOUT, "mark_level", "0.7", 0.7),
    (BUTTON, "keyd_dir", "/tmp/keyd", "/tmp/keyd"),
]


def _flag_case(entry: tuple[Tool, str, str, Any]) -> Any:
    (name, positional, prefix), dest, text, value = entry
    return pytest.param(name, positional, f"{prefix}_{dest.upper()}", dest,
                        text, value, id=f"{name}-{dest}",
                        marks=tool_marks(name))


@pytest.mark.parametrize("name, positional, variable, dest, text, value",
                         [_flag_case(entry) for entry in FLAGS])
def test_tool_flag_reads_its_environment_variable(
        monkeypatch: pytest.MonkeyPatch, name: str, positional: list[str],
        variable: str, dest: str, text: str, value: Any) -> None:
    monkeypatch.setenv(variable, text)
    args = tool(name).build_parser().parse_args(positional)
    assert getattr(args, dest) == value


# name, positional arguments, variable, flag's dest, value, default
EXEMPT: list[tuple[str, list[str], str, str, str, Any]] = [
    ("collect-captures", [], "COLLECT_CAPTURES_DRY_RUN", "dry_run", "1",
     False),
    ("collect-captures", [], "COLLECT_CAPTURES_ALLOW_DUPLICATES",
     "allow_duplicates", "1", False),
    ("collect-captures", [], "COLLECT_CAPTURES_KIND", "kind", "capture",
     None),
    ("collect-captures", [], "COLLECT_CAPTURES_NOTE", "note", "stale", ""),
    ("collect-captures", [], "COLLECT_CAPTURES_FRAME_NOTE", "frame_note",
     "stale", ""),
    ("measure-ink", ["f.png"], "MEASURE_INK_PEG", "peg", "1,2", None),
    ("measure-punch-tolerance", [], "MEASURE_PUNCH_TOLERANCE_SELF_TEST",
     "self_test", "1", False),
]


@pytest.mark.parametrize(
    "name, positional, variable, dest, text, absent",
    [pytest.param(*entry, id=f"{entry[0]}-{entry[3]}",
                  marks=tool_marks(entry[0])) for entry in EXEMPT])
def test_tool_exemptions_ignore_the_environment(
        monkeypatch: pytest.MonkeyPatch, name: str, positional: list[str],
        variable: str, dest: str, text: str, absent: Any) -> None:
    monkeypatch.setenv(variable, text)
    args = tool(name).build_parser().parse_args(positional)
    assert getattr(args, dest) == absent


@pytest.mark.parametrize(
    "variable, dest",
    [pytest.param("COMFYUI_TEMP", "temp",
                  marks=tool_marks("collect-captures")),
     pytest.param("CAPTURE_CORPUS", "out",
                  marks=tool_marks("collect-captures"))])
def test_collect_captures_keeps_its_existing_variables(
        monkeypatch: pytest.MonkeyPatch, variable: str, dest: str) -> None:
    monkeypatch.setenv(variable, "/from/env")
    args = tool("collect-captures").build_parser().parse_args([])
    assert getattr(args, dest) == "/from/env"
