"""Tests for ``fixes/prune-duplicate-captures``.

Every test runs against a throwaway ``ROOT``.  The autouse fixture is
what keeps a test from touching the real ``data/captures``.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import types
from pathlib import Path
from typing import Any

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load() -> types.ModuleType:
    path = os.path.join(_HERE, "prune-duplicate-captures")
    loader = importlib.machinery.SourceFileLoader("prune_duplicates", path)
    spec = importlib.util.spec_from_loader("prune_duplicates", loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


pd = _load()


def session(root: Path, name: str, at: str,
            frames: list[dict[str, Any]]) -> Path:
    directory = root / name
    directory.mkdir()
    for frame in frames:
        (directory / frame["file"]).write_bytes(b"frame")
    manifest = directory / "manifest.json"
    manifest.write_text(json.dumps({"notes": [{"at": at}], "frames": frames}))
    return directory


@pytest.fixture(autouse=True)
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(pd, "ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def pair(root: Path) -> tuple[Path, Path]:
    """B was collected second and re-copied A's frame."""
    annotated = {"file": "a.png", "sha256_16": "aaaa", "lights": "by hand"}
    later = {"file": "copy.png", "sha256_16": "aaaa"}
    own = {"file": "b.png", "sha256_16": "bbbb"}
    return (session(root, "A", "2026-09-01", [annotated]),
            session(root, "B", "2026-09-02", [later, own]))


def frames_in(directory: Path) -> list[dict[str, Any]]:
    manifest = json.loads((directory / "manifest.json").read_text())
    frames: list[dict[str, Any]] = manifest["frames"]
    return frames


def test_later_copy_is_removed_from_disk_and_manifest(
        pair: tuple[Path, Path]) -> None:
    _, later = pair
    assert pd.main([]) == 0
    assert not (later / "copy.png").exists()
    assert (later / "b.png").exists()
    assert [f["file"] for f in frames_in(later)] == ["b.png"]


def test_earliest_session_keeps_its_frame_and_per_frame_keys(
        pair: tuple[Path, Path]) -> None:
    earliest, _ = pair
    assert pd.main([]) == 0
    assert (earliest / "a.png").exists()
    assert frames_in(earliest)[0]["lights"] == "by hand"


def test_dry_run_changes_nothing(pair: tuple[Path, Path],
                                 capsys: pytest.CaptureFixture[str]) -> None:
    _, later = pair
    before = (later / "manifest.json").read_text()
    assert pd.main(["--dry-run"]) == 0
    assert (later / "copy.png").exists()
    assert (later / "manifest.json").read_text() == before
    assert "nothing changed" in capsys.readouterr().out


@pytest.mark.parametrize("flag", ["--dry-rn", "--dryrun", "-n"])
def test_mistyped_flag_is_rejected_and_nothing_is_removed(
        pair: tuple[Path, Path], flag: str) -> None:
    """The reason for the change: a typo must not mean a live run."""
    _, later = pair
    with pytest.raises(SystemExit) as caught:
        pd.main([flag])
    assert caught.value.code == 2
    assert (later / "copy.png").exists()
