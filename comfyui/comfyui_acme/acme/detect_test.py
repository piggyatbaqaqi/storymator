"""Peg detection, and what it reports about each candidate.

`acme.detect` had no tests.  These cover the part being changed --
what a candidate's position and shape actually are -- rather than
attempting the whole module at once.
"""

import numpy as np
import pytest

from acme.detect import find_peg_candidates

SHEET = (400, 600)


def _scene(slots, highlight=None, paper=0.7, peg=0.15):
    """A bright sheet with dark slots cut into it.

    ``slots`` are (cx, cy, w, h, angle_deg).  ``highlight`` is a
    bright patch painted inside one of them, standing for a specular
    on chrome.
    """
    gray = np.full(SHEET, paper, dtype=float)
    ys, xs = np.mgrid[0:SHEET[0], 0:SHEET[1]]
    for cx, cy, w, h, ang in slots:
        t = np.radians(ang)
        dx, dy = xs - cx, ys - cy
        u = dx * np.cos(t) + dy * np.sin(t)
        v = -dx * np.sin(t) + dy * np.cos(t)
        gray[(np.abs(u) <= w / 2) & (np.abs(v) <= h / 2)] = peg
    if highlight is not None:
        x0, x1, y0, y1 = highlight
        gray[y0:y1, x0:x1] = paper
    sheet = np.ones(SHEET, dtype=bool)
    sheet[:8] = sheet[-8:] = False
    sheet[:, :8] = sheet[:, -8:] = False
    return gray, sheet


def _find(gray, sheet):
    return find_peg_candidates(gray, sheet, min_area_px=200,
                               max_area_px=20000, polarity="dark")


# --- position ---------------------------------------------------------

def test_a_highlight_inside_a_slot_does_not_move_the_reported_centre():
    """The measured failure, in miniature.

    A specular on the chrome eats a bite out of the dark region. Its
    centre of mass moves; the slot does not. The detector must report
    the slot.
    """
    clean, sheet = _scene([(300, 200, 130, 32, 0.0)])
    holed, _ = _scene([(300, 200, 130, 32, 0.0)],
                      highlight=(250, 300, 190, 210))
    a, b = _find(clean, sheet), _find(holed, sheet)
    assert len(a) == len(b) == 1
    assert np.linalg.norm(a[0].centre - b[0].centre) < 1.0


def test_the_reported_centre_is_the_slot_centre():
    gray, sheet = _scene([(300, 200, 130, 32, 0.0)])
    assert _find(gray, sheet)[0].centre == pytest.approx(
        [300.0, 200.0], abs=1.0)


# --- shape ------------------------------------------------------------

def test_a_candidate_reports_its_angle():
    """Which the bar constrains, and which a centroid discards."""
    for angle in (0.0, 12.0, -20.0):
        gray, sheet = _scene([(300, 200, 130, 32, angle)])
        got = np.degrees(_find(gray, sheet)[0].angle_rad)
        assert min(abs(got - angle), abs(abs(got - angle) - 180)) < 2.0


def test_a_candidate_reports_the_slot_size_not_the_ink_size():
    """So 15.75 x 3.09 mm can be used as a refusal."""
    gray, sheet = _scene([(300, 200, 130, 32, 0.0)],
                         highlight=(250, 300, 190, 210))
    blob = _find(gray, sheet)[0]
    assert blob.long_px == pytest.approx(130.0, abs=3.0)
    assert blob.short_px == pytest.approx(32.0, abs=3.0)


def test_a_round_peg_is_handled_by_the_same_path():
    """A circle's bounding rectangle is a square on its centre, so the
    round landmark needs no special case."""
    ys, xs = np.mgrid[0:SHEET[0], 0:SHEET[1]]
    gray = np.full(SHEET, 0.7)
    gray[((xs - 300) ** 2 + (ys - 200) ** 2) <= 28 ** 2] = 0.15
    sheet = np.ones(SHEET, dtype=bool)
    sheet[:8] = sheet[-8:] = False
    sheet[:, :8] = sheet[:, -8:] = False
    blob = _find(gray, sheet)[0]
    assert blob.centre == pytest.approx([300.0, 200.0], abs=1.0)
    assert blob.elongation == pytest.approx(1.0, abs=0.1)


def test_several_candidates_come_back_independently():
    gray, sheet = _scene([(150, 200, 130, 32, 0.0),
                          (300, 200, 56, 56, 0.0),
                          (450, 200, 130, 32, 0.0)])
    found = sorted(_find(gray, sheet), key=lambda b: b.x)
    assert len(found) == 3
    assert [round(b.x) for b in found] == [150, 300, 450]
