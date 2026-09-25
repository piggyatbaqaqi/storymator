"""The registered frame must not come out mirrored.

It does. `FieldSpec.matrix()` has determinant -135.3 when `flip_y` is
true, so the millimetres-to-output stage reflects, while `fit_pose`
rejects any homography whose linear part has a negative determinant --
on the grounds that it describes a sheet seen from behind. The
reflection is therefore introduced by the raster, immediately after a
fit that went to some trouble to avoid one.

Measured on `hamster_centered_001`:

    det(image -> mm)         +0.01014
    det(raster mm -> out px) -135.3
    det(image -> output px)  -1.39910

Both the captured frame and the output raster are y-down rasters of
the same scene, photographed from one side. Nothing physical happens
between them, so the composition must be orientation-preserving.

`flip_y` exists for a real reason -- the bar is below, image rows
increase downward, and the punched edge should come out at the bottom
of the output -- but a flip in y alone is not what achieves that. In
the captured frame +x along the bar points *left* and +y into the
sheet points *up*, so the peg frame is a 180 degree rotation of the
image frame. Undoing it needs both axes negated, which is a rotation,
not a reflection.

A round trip -- warp to the raster, warp back, compare -- would *not*
catch this. A reflection applied and then inverted returns the
original. The test has to look at chirality.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from .fit import fit_pose
from .geometry import apply_homography
from .model import Calibration, FieldSpec, SheetModel

_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", ".."))

FRAMES = (
    ("hamster_centered/hamster_centered_001", "v4k_01_blue_84001.json"),
    ("first_hamster/first_hamster_004", "v4k_01_blue_84001.json"),
    ("repaint/repaint_001", "v4k_01_blue_84001.json"),
)


def _load(stem: str, name: str):
    path = os.path.join(_ROOT, "data", "captures", stem + ".png")
    cal_path = os.path.join(_ROOT, "data", "calibration", "distortion",
                            "v4k_01", name)
    if not (os.path.exists(path) and os.path.exists(cal_path)):
        pytest.skip("corpus frame or rig calibration absent")
    from PIL import Image
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=float)
    with open(cal_path) as handle:
        cal = Calibration.from_dict(json.load(handle))
    return rgb, (rgb @ np.array([0.2126, 0.7152, 0.0722])) / 255.0, cal


# --- 1. the raster stage, on its own ---------------------------------

@pytest.mark.parametrize("where", ["below", "above"])
def test_the_raster_never_reflects(where: str):
    """Whichever side of the sheet the bar is on.

    A raster is a choice of output pixels. No choice about where to
    put the origin should turn the picture over.
    """
    sheet = SheetModel(bar_position=where)
    spec = FieldSpec.for_sheet(sheet)
    assert np.linalg.det(spec.matrix()[:2, :2]) > 0


def test_a_bar_below_still_rotates_the_output():
    """The reason flip_y was there in the first place.

    With the bar below, the peg frame's +y runs away from the punched
    edge, and the output wants that edge at the bottom. So increasing
    peg y must give a *decreasing* output row -- a rotation, since the
    x axis turns with it, not a reflection.
    """
    sheet = SheetModel(bar_position="below")
    matrix = FieldSpec.for_sheet(sheet).matrix()
    near = apply_homography(matrix, np.array([[0.0, 0.0]]))[0]
    far = apply_homography(matrix, np.array([[0.0, 100.0]]))[0]
    assert far[1] < near[1]
    assert np.linalg.det(matrix[:2, :2]) > 0


def test_a_bar_above_does_not_rotate():
    sheet = SheetModel(bar_position="above")
    matrix = FieldSpec.for_sheet(sheet).matrix()
    near = apply_homography(matrix, np.array([[0.0, 0.0]]))[0]
    far = apply_homography(matrix, np.array([[0.0, 100.0]]))[0]
    assert far[1] > near[1]
    assert np.linalg.det(matrix[:2, :2]) > 0


@pytest.mark.parametrize("where", ["below", "above"])
def test_the_sheet_still_fits_the_raster(where: str):
    """Rotating must not push the sheet off the page."""
    sheet = SheetModel(bar_position=where)
    spec = FieldSpec.for_sheet(sheet)
    width, height = spec.size_px
    corners = apply_homography(spec.matrix(), sheet.corners())
    assert corners[:, 0].min() > -1.0
    assert corners[:, 1].min() > -1.0
    assert corners[:, 0].max() < width + 1.0
    assert corners[:, 1].max() < height + 1.0
    Calibration(sheet=sheet, field_spec=spec).check_raster()


# --- 2. the whole chain, on real frames ------------------------------

@pytest.mark.parametrize("stem,name", FRAMES)
def test_the_registered_frame_is_not_mirrored(stem: str, name: str):
    """Image and output are y-down rasters of the same scene.

    Nothing physical happens between them, so the composition must
    preserve orientation. This is the assertion the whole file is for.
    """
    rgb, gray, cal = _load(stem, name)
    pose = fit_pose(gray, cal, rgb=rgb, max_residual_mm=1e9)
    assert pose.transform is not None
    total = cal.raster.matrix() @ pose.transform
    assert np.linalg.det(total[:2, :2]) > 0


@pytest.mark.parametrize("stem,name", FRAMES)
def test_a_chiral_mark_keeps_its_handedness(stem: str, name: str):
    """Chirality, not a round trip.

    Warping to the raster and back returns the original whether or not
    a reflection was applied, because a reflection is its own inverse.
    Three points that turn one way in the frame must still turn that
    way in the output.
    """
    rgb, gray, cal = _load(stem, name)
    pose = fit_pose(gray, cal, rgb=rgb, max_residual_mm=1e9)
    total = cal.raster.matrix() @ pose.transform
    triangle = np.array([[100.0, 100.0], [900.0, 150.0], [200.0, 800.0]])
    out = apply_homography(total, triangle)

    def turn(p):
        a, b, c = p
        return np.sign((b[0] - a[0]) * (c[1] - a[1])
                       - (b[1] - a[1]) * (c[0] - a[0]))

    assert turn(out) == turn(triangle)


@pytest.mark.parametrize("stem,name", FRAMES)
def test_the_pegs_come_out_along_the_bottom(stem: str, name: str):
    """Bar below means the punched edge is nearest the operator.

    An output with the bar along the top is upside down even if it is
    not mirrored, and the two faults are easy to confuse by eye.
    """
    _, _, cal = _load(stem, name)
    _, height = cal.raster.size_px
    pegs = apply_homography(cal.raster.matrix(), cal.peg.positions())
    assert pegs[:, 1].min() > 0.6 * height


@pytest.mark.parametrize("stem,name", FRAMES)
def test_the_bar_runs_across_the_output_not_down_it(stem: str, name: str):
    """The three pegs are collinear; that line should be horizontal."""
    _, _, cal = _load(stem, name)
    pegs = apply_homography(cal.raster.matrix(), cal.peg.positions())
    spread = pegs.max(axis=0) - pegs.min(axis=0)
    assert spread[0] > 10 * max(spread[1], 1.0)
