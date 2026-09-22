"""Tests for ``bin/measure-ink``.

The arithmetic is :mod:`acme.ink`'s and is tested there; what is left
here is the command-line contract.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import types

import numpy as np
import pytest
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load() -> types.ModuleType:
    path = os.path.join(_HERE, "measure-ink")
    loader = importlib.machinery.SourceFileLoader("measure_ink", path)
    spec = importlib.util.spec_from_loader("measure_ink", loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


mi = _load()

PAPER = np.array([231, 194, 165], dtype=np.uint8)
INK = np.array([26, 30, 58], dtype=np.uint8)
PEGS = ((60, 60), (160, 60), (260, 60))


@pytest.fixture()
def frame(tmp_path):
    img = np.zeros((120, 320, 3), dtype=np.uint8)
    img[:, :] = PAPER
    for cx, cy in PEGS:
        img[cy - 8:cy + 8, cx - 20:cx + 20] = INK
    path = tmp_path / "shot.png"
    Image.fromarray(img).save(path)
    return str(path)


def test_it_prints_a_block_a_calibration_can_take(frame, capsys):
    argv = [frame, "--peg", "60,60", "--peg", "160,60", "--peg",
            "260,60", "--name", "test", "--radius", "30"]
    assert mi.main(argv) == 0
    block = json.loads(capsys.readouterr().out)["ink"]
    assert set(block) == {"direction_deg", "tolerance_deg",
                          "min_chroma", "name"}
    assert block["name"] == "test"

    from acme.model import InkSignature
    assert InkSignature(**block).name == "test"


def test_into_writes_the_block_and_keeps_the_rest(frame, tmp_path, capsys):
    target = tmp_path / "calibration.json"
    target.write_text(json.dumps({"peg": {"round_diameter_mm": 6.44}}))
    assert mi.main([frame, "--peg", "60,60", "--peg", "160,60",
                    "--peg", "260,60", "--radius", "30",
                    "--into", str(target)]) == 0
    data = json.loads(target.read_text())
    assert data["peg"]["round_diameter_mm"] == 6.44
    assert data["ink"]["direction_deg"] == pytest.approx(
        json.loads(capsys.readouterr().out)["ink"]["direction_deg"])


def test_a_malformed_peg_is_rejected(frame):
    with pytest.raises(SystemExit):
        mi.main([frame, "--peg", "sixty"])


def test_windows_with_no_ink_fail_rather_than_inventing_a_colour(
        tmp_path, capsys):
    flat = np.zeros((120, 320, 3), dtype=np.uint8)
    flat[:, :] = PAPER
    path = tmp_path / "blank.png"
    Image.fromarray(flat).save(path)
    assert mi.main([str(path), "--peg", "60,60", "--radius", "30"]) == 1
    assert "no ink found" in capsys.readouterr().err
