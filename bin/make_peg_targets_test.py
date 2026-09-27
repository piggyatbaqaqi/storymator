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
                margin_mm=8.0, dictionary="DICT_6X6_250",
                caliper_mm=None)
    args.update(kw)
    return mt.render(**args)


# --- 1. the pieces must be distinguishable once they are on the disc --

def test_each_board_gets_its_own_ids():
    ranges = mt.marker_ids(4, per_board=4)
    assert len(ranges) == 4
    seen = set()
    for block in ranges:
        assert len(block) == 4
        assert not seen & set(int(v) for v in block)
        seen |= set(int(v) for v in block)


def test_the_ids_start_where_they_are_told_to():
    ranges = mt.marker_ids(2, per_board=4, first=40)
    assert sorted(int(v) for v in ranges[0]) == [40, 41, 42, 43]
    assert sorted(int(v) for v in ranges[1]) == [44, 45, 46, 47]


def test_running_out_of_dictionary_is_an_error():
    with pytest.raises(ValueError, match="dictionary|ids"):
        _sheet(count=80)


# --- 2. what the detector sees, at the scale the rig sees it ---------

@pytest.mark.parametrize("index", range(4))
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

def test_the_sheet_is_the_requested_size():
    sheet = _sheet()
    assert sheet.shape == (int(round(SHEET[1] * PPM)),
                           int(round(SHEET[0] * PPM)))
    assert sheet.dtype == np.uint8


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


# The six scale-bar tests that lived here are gone with the bars.
# docs/planning/measuring-the-printed-target.md has the reasoning: the
# ticks are 0.20 mm wide, so reading them outside-, centre- or
# inside-to-inside gives a 0.40 % spread on a quantity worth 1.27 %,
# which over the peg span is 101 % of the error threshold. The project
# had already found the same fault on the CalibrX board and written
# "never measure a printed bar" in data/calibration/targets/README.md.
#
# What replaces them is below: the sheet advertises corner-to-corner
# distances, which are points where four quadrants meet and have no
# width to argue about.


# --- 4. refuse rather than clip --------------------------------------

def test_a_sheet_too_small_for_the_boards_is_refused():
    with pytest.raises(ValueError, match="fit|room|sheet"):
        _sheet(count=4, sheet_mm=(60.0, 60.0))


def test_the_boards_do_not_overlap_their_cut_margins():
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    centres = mt.layout(4, side, 8.0, SHEET)
    assert len(centres) == 4
    box = side + 2 * 8.0
    for i, a in enumerate(centres):
        for b in centres[i + 1:]:
            assert (abs(a[0] - b[0]) >= box or abs(a[1] - b[1]) >= box), (
                "two cut boxes overlap, so cutting one damages another")


def test_every_board_lies_wholly_on_the_sheet():
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    half = side / 2 + 8.0
    for x, y in mt.layout(4, side, 8.0, SHEET):
        assert half <= x <= SHEET[0] - half
        assert half <= y <= SHEET[1] - half


def test_board_side_is_squares_times_square():
    assert mt.board_side_mm(3, 12.5) == pytest.approx(37.5)
    assert mt.board_side_mm(4, 10.0) == pytest.approx(40.0)


# --- 5. the command line ---------------------------------------------

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


# --- 6. what the operator actually puts the calipers on --------------

CALIPER_MM = 152.71


def test_the_sheet_advertises_its_own_measurements():
    """A nominal to compare a reading against, or the reading is idle."""
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    centres = mt.layout(4, side, 8.0, SHEET, caliper_mm=CALIPER_MM)
    spans = mt.caliper_spans(centres, SQUARES, SQUARE_MM)
    assert set(spans) >= {"across", "down", "diagonal_0_3", "diagonal_1_2"}
    for name, value in spans.items():
        assert value > 0, name


def test_every_advertised_span_fits_the_caliper():
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    centres = mt.layout(4, side, 8.0, SHEET, caliper_mm=CALIPER_MM)
    for name, value in mt.caliper_spans(
            centres, SQUARES, SQUARE_MM).items():
        assert value <= CALIPER_MM, (
            f"{name} is {value:.2f} mm and the caliper reaches "
            f"{CALIPER_MM} mm")


def test_the_two_diagonals_are_nominally_equal():
    """So any measured difference is skew.

    Diagonals do *not* cross-check anisotropy -- under a scaling of sx
    across and sy down both diagonals change by the same factor,
    sqrt((sx^2+sy^2)/2), so an isotropic 1.0134 is indistinguishable
    from an anisotropic 1.0127 by 1.0142. What an inequality between
    them does show is a shear, which nothing else on the sheet catches.
    """
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    spans = mt.caliper_spans(
        mt.layout(4, side, 8.0, SHEET, caliper_mm=CALIPER_MM),
        SQUARES, SQUARE_MM)
    assert spans["diagonal_0_3"] == pytest.approx(spans["diagonal_1_2"],
                                                  abs=0.01)


def test_the_advertised_spans_match_the_printed_geometry():
    """Measured through the detector, not read back from the layout.

    An advertised nominal that disagrees with the ink is worse than no
    nominal: it silently biases every correction derived from it.
    """
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    centres = mt.layout(4, side, 8.0, SHEET, caliper_mm=CALIPER_MM)
    spans = mt.caliper_spans(centres, SQUARES, SQUARE_MM)
    sheet = _sheet(caliper_mm=CALIPER_MM)
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    found = []
    for ids in mt.marker_ids(4, per_board=4):
        board = cv2.aruco.CharucoBoard((SQUARES, SQUARES), SQUARE_MM,
                                       MARKER_MM, dictionary, ids)
        corners, _, _, _ = cv2.aruco.CharucoDetector(board).detectBoard(sheet)
        assert corners is not None and len(corners) == 4
        found.append(np.asarray(corners).reshape(-1, 2))

    def far(a, b):
        return max(float(np.hypot(*(p - q))) for p in a for q in b) / PPM

    order = sorted(range(4), key=lambda i: (found[i][:, 1].mean(),
                                            found[i][:, 0].mean()))
    tl, tr, bl, br = (found[i] for i in order)
    assert far(tl, tr) == pytest.approx(spans["across"], abs=0.2)
    assert far(tl, bl) == pytest.approx(spans["down"], abs=0.2)


def test_a_caliper_too_short_for_any_layout_is_refused():
    """Rather than quietly laying out something unmeasurable."""
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    with pytest.raises(ValueError, match="caliper"):
        mt.layout(4, side, 8.0, SHEET, caliper_mm=40.0)


def test_no_scale_bar_is_drawn_any_more():
    """Nothing on the sheet should look like a ruler.

    A board's own black square is 12.5 mm; anything much longer than
    that is a bar, and a bar invites the measurement this sheet exists
    to discourage.
    """
    sheet = _sheet(caliper_mm=CALIPER_MM)
    dark = np.asarray(sheet) < 128
    longest = 0
    for row in dark:
        xs = np.nonzero(row)[0]
        if xs.size:
            runs = np.split(xs, np.nonzero(np.diff(xs) != 1)[0] + 1)
            longest = max(longest, max(len(r) for r in runs))
    assert longest / PPM < 2 * SQUARE_MM


# --- 7. the label has to survive the scissors ------------------------
#
# docs/planning/labelling-the-cut-targets.md: the empty white frame is
# cutting tolerance, not something the detector uses.  ChArUco reads
# the four interior markers, whose nearest edge is 1.75 mm inside the
# board boundary, so a label outside the board measured 40/40 with
# 9 um of corner movement -- the repeatability of the label-free
# baseline.  What breaks it is ink *on* a marker.


def _ink(sheet, x0_mm, y0_mm, x1_mm, y1_mm):
    """Dark pixels in a millimetre box, as (rows, cols) in mm."""
    def px(v):
        return int(round(v * PPM))
    crop = np.asarray(sheet)[px(y0_mm):px(y1_mm), px(x0_mm):px(x1_mm)]
    rows, cols = np.nonzero(crop < 128)
    return rows / PPM + y0_mm, cols / PPM + x0_mm


@pytest.mark.xfail(strict=True,
                   reason="labels are still outside the cut box")
def test_the_label_is_inside_the_cut_box():
    """So cutting on the grey line keeps the label.

    This is the whole point: a piece that has been cut out has to
    still say which piece it is.  The crop deliberately reaches
    beyond the cut box on three sides, so that ink escaping the box
    is caught rather than cropped away.
    """
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    margin = 8.0
    sheet = _sheet(caliper_mm=CALIPER_MM, margin_mm=margin)
    for cx, cy in mt.layout(4, side, margin, SHEET, caliper_mm=CALIPER_MM):
        left, right = cx - side / 2 - margin, cx + side / 2 + margin
        top = cy - side / 2 - margin
        rows, cols = _ink(sheet, left - 6.0, top - 6.0,
                          right + 6.0, cy - side / 2)
        assert rows.size, "no label ink in the band above the board"
        assert rows.min() >= top, (
            f"label ink {top - rows.min():.2f} mm above the cut line")
        assert cols.min() >= left and cols.max() <= right, (
            "label ink outside the cut box sideways")


@pytest.mark.xfail(strict=True,
                   reason="labels are still outside the cut box")
def test_the_label_keeps_its_clearance_from_the_board():
    """Ink near a marker is the one thing that breaks detection.

    Measured: 2 to 3 mm of overlap kills the top-middle marker and
    three markers interpolate only two of the four corners.  The
    board edge already buys 1.75 mm of headroom; this asks for more,
    because nothing in that measurement modelled ink spread or a
    wobbling blade.
    """
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    margin = 8.0
    sheet = _sheet(caliper_mm=CALIPER_MM, margin_mm=margin)
    for cx, cy in mt.layout(4, side, margin, SHEET, caliper_mm=CALIPER_MM):
        top = cy - side / 2
        rows, _ = _ink(sheet, cx - side / 2 - margin, top - margin,
                       cx + side / 2 + margin, top)
        assert rows.size
        assert top - rows.max() >= mt.LABEL_CLEAR_MM - 0.1, (
            f"label ink reaches {top - rows.max():.2f} mm of the board, "
            f"less than the {mt.LABEL_CLEAR_MM} mm it should keep")


@pytest.mark.xfail(strict=True,
                   reason="labels are still outside the cut box")
def test_nothing_is_printed_above_the_cut_box():
    """The cut piece is exactly the cut box, 53.5 mm square.

    The old label sat 5.5 mm above the line, so keeping it meant
    cutting a piece about 62 mm tall and carrying that onto the disc.
    """
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    margin = 8.0
    sheet = _sheet(caliper_mm=CALIPER_MM, margin_mm=margin)
    for cx, cy in mt.layout(4, side, margin, SHEET, caliper_mm=CALIPER_MM):
        top = cy - side / 2 - margin
        rows, _ = _ink(sheet, cx - side / 2 - margin, top - 7.0,
                       cx + side / 2 + margin, top)
        assert rows.size == 0, (
            f"{rows.size} dark pixels above board ({cx:.0f}, {cy:.0f})'s "
            f"cut line, so the piece is taller than its cut box")


@pytest.mark.xfail(strict=True,
                   reason="labels are still outside the cut box")
def test_the_label_is_the_size_it_claims():
    """Measured off the pixels, because legibility is the point."""
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    margin = 8.0
    sheet = _sheet(caliper_mm=CALIPER_MM, margin_mm=margin)
    cx, cy = mt.layout(4, side, margin, SHEET, caliper_mm=CALIPER_MM)[0]
    rows, cols = _ink(sheet, cx - side / 2 - margin,
                      cy - side / 2 - margin,
                      cx + side / 2 + margin, cy - side / 2)
    # Cap height is about 0.72 em for this face; digits and '#' set it.
    assert 0.55 <= (rows.max() - rows.min()) / mt.LABEL_EM_MM <= 0.95
    assert cols.max() - cols.min() <= side, (
        "the label is wider than the board it names")


@pytest.mark.xfail(strict=True,
                   reason="labels are still outside the cut box")
def test_a_margin_too_narrow_for_the_label_is_refused():
    """Rather than printing the label onto the markers."""
    with pytest.raises(ValueError, match="label|margin"):
        _sheet(caliper_mm=CALIPER_MM, margin_mm=1.0)


@pytest.mark.xfail(strict=True,
                   reason="labels are still outside the cut box")
def test_the_top_of_the_page_is_no_longer_reserved_for_labels():
    """LABEL_SPACE_MM is dead once the labels are inside the box."""
    side = mt.board_side_mm(SQUARES, SQUARE_MM)
    half = side / 2 + 8.0
    first = mt.layout(4, side, 8.0, SHEET)[0]
    assert first[1] == pytest.approx(mt.PAGE_MARGIN_MM + half, abs=0.01)
    assert not hasattr(mt, "LABEL_SPACE_MM")
