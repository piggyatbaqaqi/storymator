"""Where the pegs are, named the way the industry names it.

Two fields said the same thing in two vocabularies, neither of them
the trade's. `SheetModel.bar_position` was `"below"` or `"above"`, and
`FieldSpec.flip_y` was a boolean that meant the same fact -- and, after
the mirroring fix, no longer described what it did, since it turns the
output through 180 degrees rather than flipping an axis.

Animation calls these **top pegs** and **bottom pegs**. So both fields
become `peg_position`, with values `"top"` and `"bottom"`.

The old spellings have to keep loading: three calibrations on disk
carry them, and a file that stops opening is a worse bug than a badly
named field.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from .geometry import apply_homography
from .model import Calibration, FieldSpec, SheetModel

_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", ".."))
_CALIBRATIONS = ("v4k_01.json", "v4k_01_steel_blue.json",
                 "v4k_01_blue_84001.json")


# --- 1. the field exists and says what it means ----------------------

def test_a_sheet_has_bottom_pegs_by_default():
    assert SheetModel().peg_position == "bottom"


def test_a_sheet_can_have_top_pegs():
    assert SheetModel(peg_position="top").peg_position == "top"


@pytest.mark.parametrize("bad", ["below", "above", "up", "", "Bottom"])
def test_a_sheet_refuses_anything_else(bad: str):
    """Including the old spellings, which mean something now.

    Silently accepting "below" would leave a field that reads like the
    old vocabulary and behaves like the new one.
    """
    with pytest.raises(ValueError, match="peg_position"):
        SheetModel(peg_position=bad)


def test_a_raster_carries_it_too():
    assert FieldSpec().peg_position == "top"
    assert FieldSpec.for_sheet(SheetModel()).peg_position == "bottom"
    assert FieldSpec.for_sheet(
        SheetModel(peg_position="top")).peg_position == "top"


@pytest.mark.parametrize("bad", ["below", "above", True, False])
def test_a_raster_refuses_anything_else(bad):
    with pytest.raises(ValueError, match="peg_position"):
        FieldSpec(peg_position=bad)


# --- 2. it still does what flip_y did --------------------------------

def test_bottom_pegs_turn_the_output_through_180_degrees():
    matrix = FieldSpec.for_sheet(SheetModel(peg_position="bottom")).matrix()
    near = apply_homography(matrix, np.array([[0.0, 0.0]]))[0]
    far = apply_homography(matrix, np.array([[0.0, 100.0]]))[0]
    assert far[1] < near[1]
    assert np.linalg.det(matrix[:2, :2]) > 0


def test_top_pegs_do_not_turn_it():
    matrix = FieldSpec.for_sheet(SheetModel(peg_position="top")).matrix()
    near = apply_homography(matrix, np.array([[0.0, 0.0]]))[0]
    far = apply_homography(matrix, np.array([[0.0, 100.0]]))[0]
    assert far[1] > near[1]
    assert np.linalg.det(matrix[:2, :2]) > 0


def test_with_peg_position_rebuilds_the_raster():
    moved = Calibration().with_peg_position("top")
    assert moved.sheet.peg_position == "top"
    assert moved.raster.peg_position == "top"
    moved.check_raster()


def test_with_peg_position_refuses_the_old_words():
    with pytest.raises(ValueError, match="peg_position"):
        Calibration().with_peg_position("above")


# --- 3. files written before the rename must still open --------------

def test_a_legacy_dict_still_loads():
    """`bar_position: below` and `flip_y: true` are bottom pegs."""
    base = Calibration().to_dict()
    legacy = json.loads(json.dumps(base))
    legacy["sheet"].pop("peg_position")
    legacy["sheet"]["bar_position"] = "below"
    legacy["field_spec"].pop("peg_position")
    legacy["field_spec"]["flip_y"] = True
    revived = Calibration.from_dict(legacy)
    assert revived.sheet.peg_position == "bottom"
    assert revived.raster.peg_position == "bottom"


def test_the_other_legacy_spelling_loads_too():
    base = Calibration().to_dict()
    legacy = json.loads(json.dumps(base))
    legacy["sheet"].pop("peg_position")
    legacy["sheet"]["bar_position"] = "above"
    legacy["field_spec"].pop("peg_position")
    legacy["field_spec"]["flip_y"] = False
    revived = Calibration.from_dict(legacy)
    assert revived.sheet.peg_position == "top"
    assert revived.raster.peg_position == "top"


def test_a_legacy_file_registers_the_same_way_it_used_to():
    """The rename must not move a single pixel.

    A legacy calibration and its modern equivalent have to produce the
    same raster matrix, or every frame registered before the rename
    disagrees with every frame after it.
    """
    modern = Calibration()
    legacy = json.loads(json.dumps(modern.to_dict()))
    legacy["sheet"].pop("peg_position")
    legacy["sheet"]["bar_position"] = "below"
    legacy["field_spec"].pop("peg_position")
    legacy["field_spec"]["flip_y"] = True
    assert np.allclose(Calibration.from_dict(legacy).raster.matrix(),
                       modern.raster.matrix())


# --- 4. what gets written from now on --------------------------------

def test_new_files_use_the_new_spelling():
    written = Calibration().to_dict()
    assert written["sheet"]["peg_position"] == "bottom"
    assert written["field_spec"]["peg_position"] == "bottom"
    assert "bar_position" not in written["sheet"]
    assert "flip_y" not in written["field_spec"]


def test_a_calibration_survives_a_round_trip():
    original = Calibration().with_peg_position("top")
    revived = Calibration.from_dict(original.to_dict())
    assert revived.sheet.peg_position == "top"
    assert revived.raster == original.raster


@pytest.mark.parametrize("name", _CALIBRATIONS)
def test_the_rig_calibrations_load_and_have_bottom_pegs(name: str):
    path = os.path.join(_ROOT, "data", "calibration", "distortion",
                        "v4k_01", name)
    if not os.path.exists(path):
        pytest.skip(f"{name} is not in the working tree")
    with open(path) as handle:
        cal = Calibration.from_dict(json.load(handle))
    assert cal.sheet.peg_position == "bottom"
    assert cal.raster.peg_position == "bottom"
    cal.check_raster()
