"""The output raster has to contain the thing it is registering to.

`AcmeRegister.registered` came back all white with no pegs in it, and
nothing was wrong with the fit. The calibration carried the bare
`FieldSpec()` default -- 1024 x 1024 px at origin (0, 0) -- which in
the peg frame is an 88 x 88 mm square starting *at* the round peg and
running up and to the right into blank paper. The sheet spans
x -141.7 to 141.7 and y -14 to 205.9, so the operator was looking at a
patch of the middle of the page.

`Calibration.__post_init__` derives a raster from the sheet, but only
when there is not one already, and `from_dict` always supplies one. So
a default that found its way into a JSON file stayed there, silently,
and every registered frame came out wrong in a way that looks like
blank paper rather than like an error.

A raster that does not contain the pegs is never what anyone means.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from .model import Calibration, FieldSpec, SheetModel

_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", ".."))
_CALIBRATIONS = ("v4k_01.json", "v4k_01_steel_blue.json",
                 "v4k_01_blue_84001.json")


def _peg_pixels(calibration: Calibration) -> np.ndarray:
    matrix = calibration.raster.matrix()
    pegs = calibration.peg.positions()
    hom = np.column_stack([pegs, np.ones(len(pegs))]) @ matrix.T
    return hom[:, :2] / hom[:, 2:3]


@pytest.mark.xfail(strict=True, reason="Calibration has no check_raster")
def test_a_raster_that_misses_the_pegs_is_rejected():
    """The check itself, on the spec that caused this."""
    bad = FieldSpec()          # 1024x1024 at the origin: x and y 0 to 88 mm
    with pytest.raises(ValueError, match="raster"):
        Calibration(field_spec=bad).check_raster()


@pytest.mark.xfail(strict=True, reason="Calibration has no check_raster")
def test_a_raster_derived_from_the_sheet_passes():
    sheet = SheetModel()
    Calibration(sheet=sheet,
                field_spec=FieldSpec.for_sheet(sheet)).check_raster()


@pytest.mark.xfail(strict=True, reason="Calibration has no check_raster")
def test_the_complaint_names_what_is_missing():
    """A refusal that does not say which way to move is not much use."""
    with pytest.raises(ValueError) as caught:
        Calibration(field_spec=FieldSpec()).check_raster()
    message = str(caught.value)
    assert "peg" in message
    assert "mm" in message


@pytest.mark.xfail(strict=True, reason="Calibration has no check_raster")
def test_a_raster_that_holds_the_pegs_but_not_the_sheet_is_allowed():
    """Cropping to the pegs is a choice, not an error.

    Someone may legitimately want a raster around the punched edge
    alone. The guard is about the landmarks the registration is
    defined by, not about seeing the whole page.
    """
    sheet = SheetModel()
    tight = FieldSpec(px_per_mm=4.0, origin_mm=(-120.0, 20.0),
                      size_px=(960, 160), flip_y=True)
    Calibration(sheet=sheet, field_spec=tight).check_raster()


# --- and the rig's own files, which is where this came from ----------

@pytest.mark.parametrize("name", _CALIBRATIONS)
@pytest.mark.xfail(strict=True, reason="Calibration has no check_raster")
def test_the_rig_calibrations_register_the_pegs(name: str):
    path = os.path.join(_ROOT, "data", "calibration", "distortion",
                        "v4k_01", name)
    if not os.path.exists(path):
        pytest.skip(f"{name} is not in the working tree")
    with open(path) as handle:
        calibration = Calibration.from_dict(json.load(handle))
    calibration.check_raster()
    width, height = calibration.raster.size_px
    for x, y in _peg_pixels(calibration):
        assert 0 <= x < width and 0 <= y < height


@pytest.mark.parametrize("name", _CALIBRATIONS)
def test_the_rig_calibrations_register_the_whole_sheet(name: str):
    """Not required by the guard, but it is what these files are for."""
    path = os.path.join(_ROOT, "data", "calibration", "distortion",
                        "v4k_01", name)
    if not os.path.exists(path):
        pytest.skip(f"{name} is not in the working tree")
    with open(path) as handle:
        calibration = Calibration.from_dict(json.load(handle))
    matrix = calibration.raster.matrix()
    corners = calibration.sheet.corners()
    hom = np.column_stack([corners, np.ones(len(corners))]) @ matrix.T
    px = hom[:, :2] / hom[:, 2:3]
    width, height = calibration.raster.size_px
    for x, y in px:
        assert -1 <= x <= width + 1 and -1 <= y <= height + 1


@pytest.mark.xfail(strict=True, reason="Calibration has no check_raster")
def test_round_tripping_a_calibration_keeps_its_raster():
    """The bug was a default surviving a round trip. It must not again."""
    sheet = SheetModel()
    original = Calibration(sheet=sheet,
                           field_spec=FieldSpec.for_sheet(sheet))
    revived = Calibration.from_dict(original.to_dict())
    assert revived.raster == original.raster
    revived.check_raster()


@pytest.mark.xfail(strict=True, reason="Calibration has no check_raster")
def test_a_bar_above_sheet_still_holds_its_pegs():
    """`with_bar_position` rebuilds the raster; it must stay valid."""
    flipped = Calibration().with_bar_position("above")
    flipped.check_raster()
    assert flipped.raster.flip_y is False
