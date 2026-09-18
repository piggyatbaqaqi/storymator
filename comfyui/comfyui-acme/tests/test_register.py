"""Registration output: the plugin's actual product."""

import numpy as np

from acme.fit import fit_pose
from acme.model import Calibration, FieldSpec, PegModel, SheetModel
from acme.register import register_image
from acme.synth import camera_homography, render

SIZE = (900, 1100)


def test_registered_frames_share_a_pixel_grid():
    """Two captures from different camera positions must land on the
    same canonical raster -- that is the whole product."""
    cal = Calibration()
    frames = []
    for kwargs in ({"rotation_deg": -10.0},
                   {"rotation_deg": 14.0, "tilt": (1.2e-4, 0.0),
                    "scale": 0.93}):
        h = camera_homography(cal, SIZE, **kwargs)
        pose = fit_pose(render(cal, h, SIZE), cal)
        assert pose.accepted, pose.reason
        out, valid = register_image(
            render(cal, h, SIZE), pose.transform, cal.field_spec)
        frames.append((out, valid))

    assert frames[0][0].shape == frames[1][0].shape
    both = frames[0][1] & frames[1][1]
    assert both.mean() > 0.5, "the two registrations barely overlap"
    difference = np.abs(frames[0][0] - frames[1][0])[both]
    # Edges will never cancel exactly, so judge on the bulk.
    assert np.percentile(difference, 99) < 0.35, (
        f"99th percentile disagreement {np.percentile(difference, 99):.3f}")


def test_pegs_land_where_the_model_says():
    cal = Calibration()
    h = camera_homography(cal, SIZE)
    pose = fit_pose(render(cal, h, SIZE), cal)
    assert pose.accepted, pose.reason
    out, _ = register_image(render(cal, h, SIZE), pose.transform,
                            cal.field_spec)

    spec = cal.field_spec
    for x_mm, y_mm in cal.peg.positions():
        px = spec.matrix() @ np.array([x_mm, y_mm, 1.0])
        col, row = int(round(px[0])), int(round(px[1]))
        assert out[row, col] < 0.5, (
            f"peg at {x_mm:.1f},{y_mm:.1f} mm did not land dark "
            f"at raster pixel {col},{row}")


def test_invalid_region_is_marked_not_filled():
    """An unregistered border is not black paper, and callers need to
    be able to tell the difference."""
    cal = Calibration()
    h = camera_homography(cal, SIZE)
    pose = fit_pose(render(cal, h, SIZE), cal)
    # A window that straddles the edge of the captured frame: the
    # camera sees the sheet plus a small margin, so canonical points
    # far outside it have no source pixel.  2 px/mm keeps the raster
    # small while still covering 250 mm.
    wide = FieldSpec(px_per_mm=2.0, origin_mm=(-250.0, -150.0),
                     size_px=(500, 500))
    out, valid = register_image(render(cal, h, SIZE), pose.transform, wide)
    assert not valid.all()
    assert valid.any()
    assert np.all(out[~valid] == 0.0)


def test_bar_above_flips_the_raster_and_bar_below_does_not():
    below = Calibration().with_bar_position("below")
    above = Calibration().with_bar_position("above")
    assert below.field_spec.flip_y
    assert not above.field_spec.flip_y


def test_calibration_round_trips_through_a_dict():
    cal = Calibration(peg=PegModel(centre_spacing_mm=100.0),
                      sheet=SheetModel(punch_offset_mm=13.5))
    again = Calibration.from_dict(cal.to_dict())
    assert again.peg.centre_spacing_mm == 100.0
    assert again.sheet.punch_offset_mm == 13.5
    assert again.field_spec.size_px == cal.field_spec.size_px
