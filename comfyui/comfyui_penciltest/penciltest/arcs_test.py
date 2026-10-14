"""The arcs measurement, on paths whose answers are known by hand.

Three groups.  **Geometry** pins the measurement itself, including the
invariances -- an angle that changed when the page was moved or scaled
would be measuring the capture rather than the drawing.  **Sequences**
fix what happens at the ends and on a bare key pair.  **Policy** checks
that the thresholds really are parameters: the same path has to read
differently under different thresholds, or the numbers are baked in and
the studio cannot set them.

The expected angles were computed independently and are written out to
six figures, so a change in the implementation has to disagree with
arithmetic rather than with a previous run of itself.
"""

from __future__ import annotations

import math
from typing import List

import pytest

from . import arcs


# A ten-millimetre key separation, with the inbetween moved around.
A: arcs.Point = (0.0, 0.0)
B: arcs.Point = (10.0, 0.0)

STRAIGHT: arcs.Point = (5.0, 0.0)           # 180.000000 -- forbidden
SHALLOW: arcs.Point = (5.0, 0.5)            # 168.578814
GENTLE: arcs.Point = (5.0, 1.5)             # 146.601512
RIGHT: arcs.Point = (5.0, 5.0)              # 90.000000
CORNER: arcs.Point = (5.0, 9.0)             # 58.109208
SPIKE: arcs.Point = (2.0, 12.0)             # 43.152390

# A run of two inbetweens on a genuine arc: 146.310 at each.
#
# The obvious-looking [A, GENTLE, (7.0, 1.0), B] is NOT this, which an
# earlier draft of this file got wrong.  Its second interior angle is
# 175.601, over the default straight threshold, so a test asserting
# "all accepted" failed on the fixture rather than on the code.  Picked
# by measurement now, not by eye.
ARC: List[arcs.Point] = [A, (3.0, 2.0), (7.0, 2.0), B]


def _rotate(p: arcs.Point, degrees: float) -> arcs.Point:
    t = math.radians(degrees)
    return (p[0] * math.cos(t) - p[1] * math.sin(t),
            p[0] * math.sin(t) + p[1] * math.cos(t))


# ------------------------------------------------------------- geometry

def test_a_straight_run_is_one_hundred_and_eighty() -> None:
    """The case the principle forbids outright, and the one a flow-based
    interpolator produces by construction."""
    assert arcs.interior_angle(A, STRAIGHT, B) == pytest.approx(180.0)


@pytest.mark.parametrize("point, expected", [
    (SHALLOW, 168.578814),
    (GENTLE, 146.601512),
    (RIGHT, 90.0),
    (CORNER, 58.109208),
    (SPIKE, 43.152390),
])
def test_known_angles(point: arcs.Point, expected: float) -> None:
    assert arcs.interior_angle(A, point, B) == pytest.approx(expected,
                                                             abs=1e-6)


def test_an_equilateral_triangle_reads_sixty() -> None:
    """A value nobody has to trust a calculator for."""
    apex = (5.0, 5.0 * math.sqrt(3.0))
    assert arcs.interior_angle(A, apex, B) == pytest.approx(60.0)


def test_the_angle_does_not_care_which_neighbour_comes_first() -> None:
    assert arcs.interior_angle(A, GENTLE, B) == pytest.approx(
        arcs.interior_angle(B, GENTLE, A))


def test_the_angle_survives_moving_the_page() -> None:
    """Otherwise it measures where the paper sat, not how the character
    moved."""
    shift = 137.0
    moved = [(p[0] + shift, p[1] - shift) for p in (A, GENTLE, B)]
    assert arcs.interior_angle(*moved) == pytest.approx(
        arcs.interior_angle(A, GENTLE, B))


def test_the_angle_survives_turning_the_page() -> None:
    turned = [_rotate(p, 37.0) for p in (A, GENTLE, B)]
    assert arcs.interior_angle(*turned) == pytest.approx(
        arcs.interior_angle(A, GENTLE, B))


def test_the_angle_survives_a_change_of_scale() -> None:
    """A field size change must not turn an acceptable arc into a
    corner."""
    bigger = [(p[0] * 3.7, p[1] * 3.7) for p in (A, GENTLE, B)]
    assert arcs.interior_angle(*bigger) == pytest.approx(
        arcs.interior_angle(A, GENTLE, B))


@pytest.mark.parametrize("path", [
    (A, A, B),          # the inbetween sits on the first key
    (A, B, B),          # ...or on the second
    (A, A, A),
])
def test_a_coincident_point_is_an_error_not_an_angle(
    path: List[arcs.Point],
) -> None:
    """Undefined, and saying 0 or 180 would be a lie the harness would
    then act on."""
    with pytest.raises(ValueError):
        arcs.interior_angle(*path)


@pytest.mark.parametrize("point", [STRAIGHT, SHALLOW, GENTLE, RIGHT,
                                   CORNER, SPIKE])
def test_the_angle_is_always_between_zero_and_one_eighty(
    point: arcs.Point,
) -> None:
    assert 0.0 <= arcs.interior_angle(A, point, B) <= 180.0


# ------------------------------------------------------------ sequences

def test_a_key_pair_has_no_interior_angles() -> None:
    """Not an error: with no inbetween there is nothing to judge."""
    assert arcs.interior_angles([A, B]) == []


@pytest.mark.parametrize("path", [[], [A]])
def test_a_path_too_short_to_have_an_inside_gives_nothing(
    path: List[arcs.Point],
) -> None:
    assert arcs.interior_angles(path) == []


def test_one_angle_per_interior_point() -> None:
    path = [A, GENTLE, (7.0, 1.0), B]
    assert len(arcs.interior_angles(path)) == len(path) - 2


def test_the_angles_are_in_path_order() -> None:
    path = [A, CORNER, GENTLE, B]
    first, second = arcs.interior_angles(path)
    assert first == pytest.approx(arcs.interior_angle(A, CORNER, GENTLE))
    assert second == pytest.approx(arcs.interior_angle(CORNER, GENTLE, B))


# --------------------------------------------------------------- policy

def test_a_straight_run_reads_as_straight() -> None:
    reading, = arcs.read_path([A, STRAIGHT, B])
    assert reading.straight and not reading.corner
    assert not reading.accepted


def test_a_corner_reads_as_a_corner() -> None:
    reading, = arcs.read_path([A, CORNER, B])
    assert reading.corner and not reading.straight
    assert not reading.accepted


def test_a_gentle_arc_is_accepted() -> None:
    reading, = arcs.read_path([A, GENTLE, B])
    assert reading.accepted


def test_the_thresholds_are_parameters_not_policy_baked_in() -> None:
    """The same drawing, judged differently, because where the line
    falls is the studio's call and not this module's."""
    lenient = arcs.read_path([A, SHALLOW, B], straight_degrees=179.0)
    strict = arcs.read_path([A, SHALLOW, B], straight_degrees=160.0)
    assert lenient[0].accepted
    assert strict[0].straight


def test_a_reading_names_the_drawing_not_its_offset() -> None:
    """So a rejection can say which drawing, which is what an animator
    needs to hear."""
    path = [A, GENTLE, CORNER, B]
    readings = arcs.read_path(path)
    assert [r.index for r in readings] == [1, 2]


def test_every_interior_point_is_reported_even_when_it_passes() -> None:
    """A harness that reports only failures cannot be distinguished from
    one that is not running."""
    readings = arcs.read_path(ARC)
    assert len(readings) == 2
    assert all(r.accepted for r in readings)
    assert [round(r.degrees, 3) for r in readings] == [146.310, 146.310]
