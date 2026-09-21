"""Fitting a slot, and not being moved by what is inside it."""

import numpy as np
import pytest

from acme.rect import fit_rect, principal_axes


def _slot(w=120, h=30, angle_deg=0.0, centre=(200.0, 150.0),
          size=(300, 400)):
    """A filled rectangle drawn into a boolean image."""
    ys, xs = np.mgrid[0:size[0], 0:size[1]]
    t = np.radians(angle_deg)
    dx, dy = xs - centre[0], ys - centre[1]
    u = dx * np.cos(t) + dy * np.sin(t)
    v = -dx * np.sin(t) + dy * np.cos(t)
    return (np.abs(u) <= w / 2) & (np.abs(v) <= h / 2)


# --- the basics -------------------------------------------------------

def test_a_plain_slot_is_recovered():
    r = fit_rect(_slot())
    assert r.centre == pytest.approx([200.0, 150.0], abs=0.5)
    assert r.long_px == pytest.approx(120.0, abs=1.5)
    assert r.short_px == pytest.approx(30.0, abs=1.5)
    assert r.angle_rad == pytest.approx(0.0, abs=0.02)


@pytest.mark.parametrize("angle", [0.0, 7.0, -11.0, 30.0, 88.0])
def test_the_angle_is_recovered(angle):
    """The bar's tilt in the frame, which a centroid discards."""
    r = fit_rect(_slot(angle_deg=angle))
    got = np.degrees(r.angle_rad)
    assert min(abs(got - angle), abs(abs(got - angle) - 180)) < 1.5


def test_a_crop_can_be_offset_back_into_the_frame():
    full = fit_rect(_slot(centre=(200.0, 150.0)))
    crop = _slot(centre=(60.0, 50.0), size=(120, 160))
    assert fit_rect(crop, origin=(140, 100)).centre == pytest.approx(
        full.centre, abs=0.5)


# --- the point of the exercise ----------------------------------------

def test_a_highlight_inside_the_slot_does_not_move_the_centre():
    """A specular highlight on chrome punches a hole in the blob.

    Its centre of MASS moves; the hole's extent does not. This is the
    whole reason for fitting rather than averaging.
    """
    clean = _slot()
    holed = clean.copy()
    holed[140:160, 150:190] = False          # a bite out of one end
    mass_shift = np.linalg.norm(
        np.array([np.nonzero(clean)[1].mean(), np.nonzero(clean)[0].mean()])
        - [np.nonzero(holed)[1].mean(), np.nonzero(holed)[0].mean()])
    assert mass_shift > 3.0, "the bite must actually move the centroid"
    assert fit_rect(holed).centre == pytest.approx(
        fit_rect(clean).centre, abs=0.5)


def test_a_bite_out_of_the_slot_EDGE_does_not_move_the_centre():
    """The one that is actually hard.

    An interior hole is ignored by an outer contour for free. A
    highlight that eats into the slot's *boundary* is not, and that is
    what a specular on a chrome peg near the slot wall does. The rect
    survives because the extremes it is pinned by still exist
    elsewhere along the edge -- a centroid has no such protection.
    """
    clean = _slot()
    bitten = clean.copy()
    bitten[135:150, 170:230] = False          # a notch in one long edge

    def centroid(m):
        ys, xs = np.nonzero(m)
        return np.array([xs.mean(), ys.mean()])
    assert np.linalg.norm(centroid(clean) - centroid(bitten)) > 1.5, \
        "the notch must actually move the centroid"
    assert fit_rect(bitten).centre == pytest.approx(
        fit_rect(clean).centre, abs=0.5)


def test_which_end_the_peg_sits_at_does_not_move_the_centre():
    """The measured case: the slot is 15.75 mm and the peg 12.70, so
    ~3 mm stands open and the peg may be at either end.

    What is detected is the hole either way -- peg and open slot both
    read dark -- so the only thing that actually varies is where the
    peg's specular highlight falls inside it. The answer must not
    follow the highlight around.
    """
    left, right = _slot(), _slot()
    left[142:158, 150:180] = False      # highlight toward the left end
    right[142:158, 220:250] = False     # ...and toward the right

    def centroid(m):
        ys, xs = np.nonzero(m)
        return np.array([xs.mean(), ys.mean()])
    assert np.linalg.norm(centroid(left) - centroid(right)) > 3.0, \
        "the two highlights must actually pull the centroid apart"
    assert fit_rect(left).centre == pytest.approx(
        fit_rect(right).centre, abs=0.5)


def test_size_is_reported_so_a_non_slot_can_be_refused():
    """15.75 x 3.09 mm is a free consistency check -- the one thing a
    centroid can never provide."""
    r = fit_rect(_slot(w=120, h=30))
    assert r.matches(120.0, 30.0)
    assert not r.matches(60.0, 30.0)
    assert not r.matches(120.0, 90.0)


# --- axes -------------------------------------------------------------

def test_the_long_axis_comes_first():
    long_axis, short_axis = principal_axes(_slot(w=120, h=30))
    assert abs(float(np.dot(long_axis, short_axis))) < 1e-9
    assert abs(long_axis[0]) > abs(long_axis[1])


def test_the_axis_sign_is_canonical():
    """eigh's sign is arbitrary, and an arbitrary sign once registered
    two captures of one sheet into mirror images of each other."""
    a, _ = principal_axes(_slot(angle_deg=20.0))
    b, _ = principal_axes(_slot(angle_deg=20.0, centre=(210.0, 160.0)))
    assert np.allclose(a, b, atol=1e-9)


# --- noise ------------------------------------------------------------

def test_a_ragged_edge_does_not_move_the_centre_much():
    """Real hole edges are torn paper, not straight lines."""
    rng = np.random.default_rng(3)
    clean = _slot()
    ragged = clean.copy()
    edge = clean & ~np.roll(clean, 1, axis=0) | clean & ~np.roll(clean, 1, 1)
    ragged[edge & (rng.random(clean.shape) < 0.5)] = False
    assert fit_rect(ragged).centre == pytest.approx(
        fit_rect(clean).centre, abs=1.0)


def test_corners_bound_the_rectangle():
    r = fit_rect(_slot(w=120, h=30, angle_deg=0.0))
    c = r.corners()
    assert c.shape == (4, 2)
    assert c[:, 0].min() == pytest.approx(140.0, abs=1.5)
    assert c[:, 0].max() == pytest.approx(260.0, abs=1.5)
    assert c[:, 1].min() == pytest.approx(135.0, abs=1.5)
    assert c[:, 1].max() == pytest.approx(165.0, abs=1.5)


def test_corners_turn_with_the_rectangle():
    """They must follow the fit, not the image axes."""
    c = fit_rect(_slot(angle_deg=30.0)).corners()
    edge = c[1] - c[0]
    assert np.degrees(np.arctan2(edge[1], edge[0])) == pytest.approx(
        30.0, abs=1.5)
    assert np.linalg.norm(edge) == pytest.approx(120.0, abs=2.0)
