"""The acceptance threshold has to come from the punch, not a round number.

`max_residual_px = 1.5` is in **raster** pixels, and the raster is
11.63 px/mm, so the default is **129 microns**. The operator measured
punch geometry from 95 flatbed scans and found a punch-to-edge
standard deviation of **268 microns**. The threshold is therefore
below the tolerance of the thing being measured: no real sheet can
pass it, however well the fit is done, and every frame in the corpus
is refused with `residual_too_high` regardless of its merits.

A threshold in pixels is also the wrong unit. Raster pixels per
millimetre is an output-resolution choice; changing it silently
changes what counts as a good fit.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from .fit import default_residual_mm, fit_pose
from .model import Calibration, SheetModel

_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", ".."))


def _rig(name: str = "v4k_01_blue_84001.json") -> Calibration:
    path = os.path.join(_ROOT, "data", "calibration", "distortion",
                        "v4k_01", name)
    if not os.path.exists(path):
        pytest.skip("the rig calibration is not in the working tree")
    with open(path) as handle:
        return Calibration.from_dict(json.load(handle))


def _frame(stem: str):
    path = os.path.join(_ROOT, "data", "captures", stem + ".png")
    if not os.path.exists(path):
        pytest.skip(f"{stem} is not in the working tree")
    from PIL import Image
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=float)
    return rgb, (rgb @ np.array([0.2126, 0.7152, 0.0722])) / 255.0


# --- 1. the tolerance is a property of the punch ---------------------

def test_the_sheet_model_carries_the_punch_tolerance():
    """Measured, not assumed: 0.268 mm from 95 flatbed scans."""
    sheet = SheetModel()
    assert hasattr(sheet, "punch_tolerance_mm")
    assert 0.1 < sheet.punch_tolerance_mm < 1.0


def test_the_default_threshold_is_derived_from_it():
    """Three standard deviations, so a sound sheet is not refused.

    At one sigma a third of good sheets would fail; at three, the
    threshold admits punch tolerance and still catches a fit that has
    gone somewhere else entirely.
    """
    sheet = SheetModel()
    assert np.isclose(default_residual_mm(sheet),
                      3.0 * sheet.punch_tolerance_mm)


def test_the_default_is_reachable_by_a_real_sheet():
    """The whole complaint: 129 microns is below the punch's own scatter."""
    assert default_residual_mm(SheetModel()) > SheetModel().punch_tolerance_mm


def test_a_tighter_punch_gives_a_tighter_threshold():
    """So a better-punched stock is held to a better standard."""
    from dataclasses import replace
    loose = SheetModel()
    tight = replace(loose, punch_tolerance_mm=loose.punch_tolerance_mm / 4)
    assert default_residual_mm(tight) < default_residual_mm(loose)


# --- 2. and the fit is judged in millimetres -------------------------

def test_the_threshold_is_stated_in_millimetres():
    """Raster pixels per millimetre is an output-resolution choice.

    Judging a fit in them means changing the output size silently
    changes what counts as a good fit.
    """
    import inspect
    assert "max_residual_mm" in inspect.signature(fit_pose).parameters


def test_the_verdict_does_not_move_with_the_output_resolution():
    from dataclasses import replace
    from .model import FieldSpec
    cal = _rig()
    rgb, gray = _frame("repaint/repaint_001")
    verdicts = []
    for px_per_mm in (4.0, 11.63, 40.0):
        spec = FieldSpec.for_sheet(cal.sheet, px_per_mm=px_per_mm)
        pose = fit_pose(gray, replace(cal, field_spec=spec), rgb=rgb,
                        max_residual_mm=2.5)
        verdicts.append(pose.accepted)
    assert len(set(verdicts)) == 1, (
        f"the same frame was accepted at one output size and refused "
        f"at another: {verdicts}")


def test_the_reason_names_millimetres():
    cal = _rig()
    rgb, gray = _frame("repaint/repaint_001")
    pose = fit_pose(gray, cal, rgb=rgb, max_residual_mm=0.05)
    assert not pose.accepted
    assert "mm" in pose.reason
    assert "residual_too_high" in pose.reason


# --- 3. it must still refuse a fit that is genuinely wrong -----------

def test_a_wildly_wrong_fit_is_still_refused():
    """Loosening the threshold must not make it useless.

    The artwork frames were the motivating failure: a trio made of a
    letter, a drawn figure and one real peg, reported confidently.
    """
    cal = _rig()
    rgb, gray = _frame("repaint/repaint_001")
    pose = fit_pose(gray, cal, rgb=rgb, max_residual_mm=1e-6)
    assert not pose.accepted


def test_the_measured_frames_land_either_side_of_the_default():
    """Where the corpus actually sits, so the default is not a guess.

    Peg residuals with the landmark heights corrected run 1.15 to 2.23
    mm; the default is 0.80 mm. Every frame is still refused, and that
    is the honest state of the rig -- the remaining error is the sheet
    outline, whose own residual is 3.6 to 4.1 mm on paper that bows by
    3 to 12. The threshold is now a number that *could* be met rather
    than one that could not.
    """
    cal = _rig()
    rgb, gray = _frame("repaint/repaint_001")
    pose = fit_pose(gray, cal, rgb=rgb, max_residual_mm=1e9)
    residual = pose.peg_residual_px / cal.raster.px_per_mm
    assert 0.5 < residual < 4.0
    assert residual > default_residual_mm(cal.sheet)
