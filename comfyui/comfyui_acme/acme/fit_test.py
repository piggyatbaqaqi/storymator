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

import pytest

from acme.fit import fit_pose
from acme.model import Calibration, FieldSpec, PegModel, SheetModel
from acme.synth import camera_homography, render

SIZE = (1280, 960)

pending = pytest.mark.xfail(reason="orientation tiebreak ignores peg y")


def _rig():
    return Calibration(peg=PegModel(), sheet=SheetModel(),
                       field_spec=FieldSpec())


@pending
@pytest.mark.parametrize("roll_deg", [0.0, 175.0, 180.0, 185.0])
def test_the_pegs_land_on_the_peg_line_whatever_the_camera_roll(roll_deg):
    """The fit must not choose a hypothesis that puts the pegs 194 mm
    from the line they are nailed to.

    Rolling the camera past 90 degrees is what makes "prefer the
    smaller frame rotation" pick the wrong end of the sheet.
    """
    cal = _rig()
    h = camera_homography(cal, SIZE, roll_deg=roll_deg)
    pose = fit_pose(render(cal, h, SIZE), cal)
    assert pose.accepted, pose.reason
    assert abs(pose.punch_offset_mm) < 20.0, (
        f"pegs landed {pose.punch_offset_mm:.1f} mm from the peg line; "
        f"the sheet is 180 degrees out")


@pending
def test_a_flipped_sheet_is_not_silently_accepted():
    """The failure mode that matters: not a refusal, but a confident
    fit of the sheet end for end."""
    cal = _rig()
    h = camera_homography(cal, SIZE, roll_deg=180.0)
    pose = fit_pose(render(cal, h, SIZE), cal)
    assert pose.accepted, pose.reason
    corners = pose.corners_image
    assert corners is not None
    # The punched edge is the short distance from the pegs, always.
    assert abs(pose.punch_offset_mm) < 20.0
