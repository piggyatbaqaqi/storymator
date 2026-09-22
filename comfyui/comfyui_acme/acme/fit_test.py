"""Orientation: which way round the sheet is, when the bar is symmetric.

A 180-degree error is invisible to everything the triple score
measures. Peg spacing and collinearity are both unchanged by turning
the sheet end for end, so the hypothesis search cannot tell the two
apart on those grounds and falls back to preferring the smaller frame
rotation -- a guess about how the camera is mounted.

There is a decisive physical fact it ignores. The punch is **not**
centred across the sheet: the peg line sits 12 mm from the punched edge
and 203.9 mm from the far one. So the pegs' distance from the peg line
is itself the discriminator, and the wrong hypothesis puts them
nowhere near it.

Measured on a real capture, 2026-09-21: the correct correspondence put
the three pegs at y = -2.0, -2.4 and +0.2 mm; the one chosen put them
at +193.9, +194.3 and +191.7. The registration was accepted-looking
and 180 degrees out.
"""

import numpy as np
import pytest

from acme.fit import fit_pose
from acme.model import Calibration, FieldSpec, PegModel, SheetModel
from acme.synth import camera_homography, render

SIZE = (1280, 960)


def _rig():
    return Calibration(peg=PegModel(), sheet=SheetModel(),
                       field_spec=FieldSpec())


@pytest.mark.parametrize("rotation_deg", [0.0, 175.0, 180.0, 185.0])
def test_the_pegs_land_on_the_peg_line_whatever_the_camera_roll(rotation_deg):
    """The fit must not choose a hypothesis that puts the pegs 194 mm
    from the line they are nailed to.

    Rolling the camera past 90 degrees is what makes "prefer the
    smaller frame rotation" pick the wrong end of the sheet.
    """
    cal = _rig()
    h = camera_homography(cal, SIZE, rotation_deg=rotation_deg)
    pose = fit_pose(render(cal, h, SIZE), cal)
    assert pose.accepted, pose.reason
    assert abs(pose.punch_offset_mm) < 20.0, (
        f"pegs landed {pose.punch_offset_mm:.1f} mm from the peg line; "
        f"the sheet is 180 degrees out")


def test_a_flipped_sheet_is_not_silently_accepted():
    """The failure mode that matters: not a refusal, but a confident
    fit of the sheet end for end."""
    cal = _rig()
    h = camera_homography(cal, SIZE, rotation_deg=180.0)
    pose = fit_pose(render(cal, h, SIZE), cal)
    assert pose.accepted, pose.reason
    corners = pose.corners_image
    assert corners is not None
    # The punched edge is the short distance from the pegs, always.
    assert abs(pose.punch_offset_mm) < 20.0


# --- artwork on the sheet ---------------------------------------------


def _paint(cal, image, homography, marks, level):
    """Paint discs on the sheet, positioned in peg-frame millimetres."""
    from acme.geometry import apply_homography
    out = image.copy()
    ys, xs = np.mgrid[0:image.shape[0], 0:image.shape[1]]
    for mm, radius in marks:
        cx, cy = apply_homography(homography, np.array([mm]))[0]
        out[((xs - cx) ** 2 + (ys - cy) ** 2) <= radius ** 2] = level
    return out


def _art_only(cal, image, homography, y_mm=120.0):
    """The real failure: pegs NOT found, artwork forming a false trio.

    Painting distractors onto a scene whose real pegs are perfectly
    visible proves nothing -- the fit simply prefers the real ones,
    which is what it should do. On the actual art page the blank-paper
    detector found no valid trio at all, so the drawings won by
    default. Erasing the pegs reproduces that.
    """
    s = cal.peg.centre_spacing_mm
    erased = _paint(cal, image, homography,
                    [((-s, 0.0), 14), ((0.0, 0.0), 14), ((s, 0.0), 14)],
                    level=0.95)
    return _paint(cal, erased, homography,
                  [((-s, y_mm), 7), ((0.0, y_mm), 7), ((s, y_mm), 7)],
                  level=0.1)


def test_artwork_that_forms_a_false_triple_is_refused_not_fitted():
    """Measured on real art, 2026-09-21.

    A page of Dr. Boulos's hamster drawing yields 44 to 56 peg
    candidates against 4 on blank paper, and the fit locks onto a
    letter in the title, a hamster's belly, and one real peg -- the
    same three pixels under both lightings, so it looks repeatable.
    Punch offset came out 120.02 mm against a nominal 12.

    Being confidently wrong is worse than refusing. A refusal is
    visible; a plausible-looking fit of three drawings is not.
    """
    cal = _rig()
    h = camera_homography(cal, SIZE)
    image = render(cal, h, SIZE)
    # three collinear marks the right distance apart, but 120 mm from
    # the peg line -- which is where the real false positive sat
    pose = fit_pose(_art_only(cal, image, h), cal)
    assert not pose.accepted, (
        f"fitted artwork at punch offset {pose.punch_offset_mm:.1f} mm")
    assert "peg_line" in pose.reason or "peg line" in pose.reason


def test_the_refusal_says_how_far_off_the_pegs_landed():
    """So the operator can tell 'it found my drawing' from 'the
    lighting is bad', which are different problems."""
    cal = _rig()
    h = camera_homography(cal, SIZE)
    pose = fit_pose(_art_only(cal, render(cal, h, SIZE), h), cal)
    assert "120" in pose.reason or "mm" in pose.reason


def test_art_elsewhere_on_the_sheet_does_not_prevent_a_good_fit():
    """The guard must reject false triples without rejecting real
    pages. Drawings are the normal case, not the exception."""
    cal = _rig()
    h = camera_homography(cal, SIZE)
    art = _paint(cal, render(cal, h, SIZE), h, [
        ((-60.0, 90.0), 9), ((20.0, 140.0), 11), ((70.0, 60.0), 8),
        ((-30.0, 170.0), 6)], level=0.1)
    pose = fit_pose(art, cal)
    assert pose.accepted, pose.reason
    assert abs(pose.punch_offset_mm) < 20.0
