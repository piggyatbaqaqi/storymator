"""Fitting a slot, and not being moved by what is inside it."""

import numpy as np
import pytest

from acme.rect import fit_rect, principal_axes

pending = pytest.mark.xfail(reason="rectangle fitting not implemented")


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

@pending
def test_a_plain_slot_is_recovered():
    r = fit_rect(_slot())
    assert r.centre == pytest.approx([200.0, 150.0], abs=0.5)
    assert r.long_px == pytest.approx(120.0, abs=1.5)
    assert r.short_px == pytest.approx(30.0, abs=1.5)
    assert r.angle_rad == pytest.approx(0.0, abs=0.02)


@pending
@pytest.mark.parametrize("angle", [0.0, 7.0, -11.0, 30.0, 88.0])
def test_the_angle_is_recovered(angle):
    """The bar's tilt in the frame, which a centroid discards."""
    r = fit_rect(_slot(angle_deg=angle))
    got = np.degrees(r.angle_rad)
    assert min(abs(got - angle), abs(abs(got - angle) - 180)) < 1.5


@pending
def test_a_crop_can_be_offset_back_into_the_frame():
    full = fit_rect(_slot(centre=(200.0, 150.0)))
    crop = _slot(centre=(60.0, 50.0), size=(120, 160))
    assert fit_rect(crop, origin=(140, 100)).centre == pytest.approx(
        full.centre, abs=0.5)


# --- the point of the exercise ----------------------------------------

@pending
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


@pending
def test_a_peg_sitting_hard_against_one_end_does_not_move_the_centre():
    """The measured case: the slot is 15.75 mm and the peg 12.70, so
    ~3 mm of it stands open, and the peg may be at either end.

    What is detected is the hole either way, so the answer must be the
    same either way."""
    left = _slot()
    right = _slot()
    left[:, 145:160] = left[:, 145:160] & False    # peg hard right
    right[:, 240:255] = right[:, 240:255] & False  # peg hard left
    assert fit_rect(left).centre == pytest.approx(
        fit_rect(right).centre, abs=0.5)


@pending
def test_size_is_reported_so_a_non_slot_can_be_refused():
    """15.75 x 3.09 mm is a free consistency check -- the one thing a
    centroid can never provide."""
    r = fit_rect(_slot(w=120, h=30))
    assert r.matches(120.0, 30.0)
    assert not r.matches(60.0, 30.0)
    assert not r.matches(120.0, 90.0)


# --- axes -------------------------------------------------------------

@pending
def test_the_long_axis_comes_first():
    long_axis, short_axis = principal_axes(_slot(w=120, h=30))
    assert abs(float(np.dot(long_axis, short_axis))) < 1e-9
    assert abs(long_axis[0]) > abs(long_axis[1])


@pending
def test_the_axis_sign_is_canonical():
    """eigh's sign is arbitrary, and an arbitrary sign once registered
    two captures of one sheet into mirror images of each other."""
    a, _ = principal_axes(_slot(angle_deg=20.0))
    b, _ = principal_axes(_slot(angle_deg=20.0, centre=(210.0, 160.0)))
    assert np.allclose(a, b, atol=1e-9)


# --- noise ------------------------------------------------------------

@pending
def test_a_ragged_edge_does_not_move_the_centre_much():
    """Real hole edges are torn paper, not straight lines."""
    rng = np.random.default_rng(3)
    clean = _slot()
    ragged = clean.copy()
    edge = clean & ~np.roll(clean, 1, axis=0) | clean & ~np.roll(clean, 1, 1)
    ragged[edge & (rng.random(clean.shape) < 0.5)] = False
    assert fit_rect(ragged).centre == pytest.approx(
        fit_rect(clean).centre, abs=1.0)
