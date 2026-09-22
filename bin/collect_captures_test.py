"""Tests for ``bin/collect-captures``.

The script is hyphenated and extensionless, so it is loaded by path
rather than imported by name.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import types
from typing import Tuple

import numpy as np
import pytest
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load() -> types.ModuleType:
    path = os.path.join(_HERE, "collect-captures")
    spec = importlib.util.spec_from_loader(
        "collect_captures",
        importlib.machinery.SourceFileLoader("collect_captures", path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cc = _load()


def _capture(path: str, seed: int, size: Tuple[int, int] = (64, 48)) -> None:
    """A frame `classify` will call a capture: coloured, no banner."""
    rng = np.random.default_rng(seed)
    rgb = rng.integers(40, 220, size=(size[1], size[0], 3), dtype=np.uint8)
    rgb[..., 2] = np.clip(rgb[..., 2].astype(int) - 30, 0, 255)
    Image.fromarray(rgb).save(path)


@pytest.fixture()
def rig(tmp_path):
    temp = tmp_path / "temp"
    out = tmp_path / "captures"
    temp.mkdir()
    out.mkdir()
    return temp, out


def _files(session_dir) -> list:
    return sorted(p.name for p in session_dir.iterdir()
                  if p.suffix == ".png")


def _manifest(session_dir) -> dict:
    with open(session_dir / "manifest.json") as fh:
        return json.load(fh)


# --- the bug that lost two frames of the blue_hamster session ---------

def test_second_collect_does_not_overwrite_the_first(rig):
    """A second run into a live session must not reuse 001.

    `collect` numbers frames from 1 every time, so the second run
    writes over whatever the first run left at the same stems. The two
    720x260 diagnostics of `blue_hamster` were destroyed this way; the
    manifest still carries their hashes.
    """
    temp, out = rig
    _capture(str(temp / "a.png"), seed=1)
    cc.collect(str(temp), str(out), "s", "", ["capture"], None, False)
    first = (out / "s" / "s_001.png").read_bytes()

    for p in temp.iterdir():
        p.unlink()
    _capture(str(temp / "b.png"), seed=2)
    cc.collect(str(temp), str(out), "s", "", ["capture"], None, False)

    assert (out / "s" / "s_001.png").read_bytes() == first
    assert _files(out / "s") == ["s_001.png", "s_002.png"]


def test_second_collect_appends_to_the_manifest(rig):
    """The manifest describes the directory, so it grows too."""
    temp, out = rig
    _capture(str(temp / "a.png"), seed=1)
    cc.collect(str(temp), str(out), "s", "first", ["capture"], None, False)

    for p in temp.iterdir():
        p.unlink()
    _capture(str(temp / "b.png"), seed=2)
    cc.collect(str(temp), str(out), "s", "second", ["capture"], None, False)

    data = _manifest(out / "s")
    names = [f["file"] for f in data["frames"]]
    assert names == ["s_001.png", "s_002.png"]
    assert len(names) == len(set(names))


def test_every_manifest_entry_names_a_file_with_that_hash(rig):
    """The manifest may not describe a frame that is not on disk."""
    temp, out = rig
    for i, name in enumerate(["a.png", "b.png"]):
        _capture(str(temp / name), seed=i)
    cc.collect(str(temp), str(out), "s", "", ["capture"], None, False)
    for p in temp.iterdir():
        p.unlink()
    _capture(str(temp / "c.png"), seed=9)
    cc.collect(str(temp), str(out), "s", "", ["capture"], None, False)

    for frame in _manifest(out / "s")["frames"]:
        blob = (out / "s" / frame["file"]).read_bytes()
        assert hashlib.sha256(blob).hexdigest()[:16] == frame["sha256_16"]


def test_numbering_survives_a_gap(rig):
    """Deleting a frame by hand must not make the next run reuse it."""
    temp, out = rig
    for i, name in enumerate(["a.png", "b.png", "c.png"]):
        _capture(str(temp / name), seed=i)
    cc.collect(str(temp), str(out), "s", "", ["capture"], None, False)
    (out / "s" / "s_002.png").unlink()

    for p in temp.iterdir():
        p.unlink()
    _capture(str(temp / "d.png"), seed=7)
    cc.collect(str(temp), str(out), "s", "", ["capture"], None, False)

    assert (out / "s" / "s_004.png").exists()
    assert not (out / "s" / "s_002.png").exists()


def test_dry_run_still_reports_the_numbers_it_would_use(rig, capsys):
    """--dry-run is a preview, so it must preview the real stems."""
    temp, out = rig
    _capture(str(temp / "a.png"), seed=1)
    cc.collect(str(temp), str(out), "s", "", ["capture"], None, False)
    capsys.readouterr()          # the setup run's own output, not the subject

    for p in temp.iterdir():
        p.unlink()
    _capture(str(temp / "b.png"), seed=2)
    cc.collect(str(temp), str(out), "s", "", ["capture"], None, True)

    out_text = capsys.readouterr().out
    assert "s_002.png" in out_text
    assert "s_001.png" not in out_text
