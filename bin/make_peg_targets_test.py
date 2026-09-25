"""Tests for ``bin/make-peg-targets``.

The sheet is a physical artefact: it gets printed, cut up and glued
down, and a mistake in it is discovered after the glue has set. So the
tests measure the rendered pixels rather than trusting the arithmetic,
and they run a real detector over the result at the scale the rig
actually sees.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import types

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load() -> types.ModuleType:
    path = os.path.join(_HERE, "make-peg-targets")
    loader = importlib.machinery.SourceFileLoader("make_peg_targets", path)
    spec = importlib.util.spec_from_loader("make_peg_targets", loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


mt = _load()

SQUARES, SQUARE_MM, MARKER_MM = 3, 12.5, 9.0
SHEET = (215.9, 279.4)
PPM = 20.0


def _sheet(count: int = 4, **kw):
    args = dict(squares=SQUARES, square_mm=SQUARE_MM, marker_mm=MARKER_MM,
                count=count, sheet_mm=SHEET, px_per_mm=PPM,
                margin_mm=8.0, dictionary="DICT_6X6_250")
    args.update(kw)
    return mt.render(**args)


# --- 1. the pieces must be distinguishable once they are on the disc --

@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_each_board_gets_its_own_ids():
    ranges = mt.marker_ids(4, per_board=4)
    assert len(ranges) == 4
    seen = set()
    for block in ranges:
        assert len(block) == 4
        assert not seen & set(int(v) for v in block)
        seen |= set(int(v) for v in block)


@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_the_ids_start_where_they_are_told_to():
    ranges = mt.marker_ids(2, per_board=4, first=40)
    assert sorted(int(v) for v in ranges[0]) == [40, 41, 42, 43]
    assert sorted(int(v) for v in ranges[1]) == [44, 45, 46, 47]


@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_running_out_of_dictionary_is_an_error():
    with pytest.raises(ValueError, match="dictionary|ids"):
        _sheet(count=80)


# --- 2. what the detector sees, at the scale the rig sees it ---------

@pytest.mark.parametrize("index", range(4))
@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_every_board_is_found_at_rig_scale(index: int):
    """Rendered at 508 dpi, resampled to 9 px/mm, with sensor noise.

    Detecting the board in the file it was written from would prove
    very little. The question is whether a 12.5 mm square survives the
    camera, and 9 px/mm is what the rig measures.
    """
    sheet = _sheet()
    small = cv2.resize(sheet, None, fx=9.0 / PPM, fy=9.0 / PPM,
                       interpolation=cv2.INTER_AREA)
    rng = np.random.default_rng(index)
    noisy = np.clip(small + rng.normal(0.0, 3.0, small.shape),
                    0, 255).astype(np.uint8)

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    ids = mt.marker_ids(4, per_board=4)[index]
    board = cv2.aruco.CharucoBoard((SQUARES, SQUARES), SQUARE_MM,
                                   MARKER_MM, dictionary, ids)
    corners, _, markers, marker_ids = cv2.aruco.CharucoDetector(
        board).detectBoard(noisy)
    assert marker_ids is not None
    assert set(int(v) for v in ids) <= set(int(v) for v in marker_ids.ravel())
    assert corners is not None and len(corners) == 4


@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_a_board_is_not_confused_with_its_neighbours():
    """Disjoint ids are only useful if the detector honours them."""
    sheet = _sheet()
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    centres = []
    for ids in mt.marker_ids(4, per_board=4):
        board = cv2.aruco.CharucoBoard((SQUARES, SQUARES), SQUARE_MM,
                                       MARKER_MM, dictionary, ids)
        corners, _, _, _ = cv2.aruco.CharucoDetector(board).detectBoard(sheet)
        assert corners is not None and len(corners) == 4
        centres.append(np.asarray(corners).reshape(-1, 2).mean(axis=0))
    for i in range(len(centres)):
        for j in range(i + 1, len(centres)):
            apart = float(np.hypot(*(centres[i] - centres[j])))
            assert apart > 20 * PPM, (
                "two boards resolved to nearly the same place, so the "
                "detector is matching the wrong piece")


# --- 3. the sheet is the size it says it is --------------------------

@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_the_sheet_is_the_requested_size():
    sheet = _sheet()
    assert sheet.shape == (int(round(SHEET[1] * PPM)),
                           int(round(SHEET[0] * PPM)))
    assert sheet.dtype == np.uint8


@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_the_squares_are_the_requested_size_in_millimetres():
    """Measured off the pixels, not taken from the arithmetic.

    This is the number that gets printed, mismeasured and glued down.
    """
    sheet = _sheet()
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    ids = mt.marker_ids(4, per_board=4)[0]
    board = cv2.aruco.CharucoBoard((SQUARES, SQUARES), SQUARE_MM,
                                   MARKER_MM, dictionary, ids)
    corners, _, _, _ = cv2.aruco.CharucoDetector(board).detectBoard(sheet)
    pts = np.asarray(corners).reshape(-1, 2)
    spacings = [float(np.hypot(*(a - b)))
                for i, a in enumerate(pts) for b in pts[i + 1:]]
    nearest = sorted(spacings)[:4]          # the four side-adjacent pairs
    for gap in nearest:
        assert abs(gap / PPM - SQUARE_MM) < 0.1


@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_the_scale_bar_is_the_length_it_claims():
    """It exists to catch the print's scale error, so it must be true."""
    sheet = _sheet()
    assert mt.scale_bar_mm(sheet, PPM) == pytest.approx(100.0, abs=0.2)


# --- 4. refuse rather than clip --------------------------------------

@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_a_sheet_too_small_for_the_boards_is_refused():
    with pytest.raises(ValueError, match="fit|room|sheet"):
        _sheet(count=4, sheet_mm=(60.0, 60.0))


@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_the_boards_do_not_overlap_their_cut_margins():
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    centres = mt.layout(4, side, 8.0, SHEET)
    assert len(centres) == 4
    box = side + 2 * 8.0
    for i, a in enumerate(centres):
        for b in centres[i + 1:]:
            assert (abs(a[0] - b[0]) >= box or abs(a[1] - b[1]) >= box), (
                "two cut boxes overlap, so cutting one damages another")


@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_every_board_lies_wholly_on_the_sheet():
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    half = side / 2 + 8.0
    for x, y in mt.layout(4, side, 8.0, SHEET):
        assert half <= x <= SHEET[0] - half
        assert half <= y <= SHEET[1] - half


@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_board_side_is_squares_times_square():
    assert mt.board_side_mm(3, 12.5) == pytest.approx(37.5)
    assert mt.board_side_mm(4, 10.0) == pytest.approx(40.0)


# --- 5. the command line ---------------------------------------------

@pytest.mark.xfail(strict=True, reason="make-peg-targets is a skeleton")
def test_it_writes_a_png_with_the_dpi_in_it(tmp_path):
    out = tmp_path / "targets.png"
    assert mt.main(["--out", str(out)]) == 0
    from PIL import Image
    with Image.open(out) as img:
        assert img.size == (int(round(SHEET[0] * PPM)),
                            int(round(SHEET[1] * PPM)))
        dpi = img.info.get("dpi")
        assert dpi is not None
        assert abs(dpi[0] - PPM * 25.4) < 1.0


def test_a_malformed_sheet_size_is_rejected(tmp_path):
    assert mt.main(["--out", str(tmp_path / "x.png"),
                    "--sheet-mm", "letter"]) == 2
