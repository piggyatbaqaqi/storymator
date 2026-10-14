"""Arcs: the interior angle at an inbetween.

The first of the acceptance harness's measurements, and the one the
planning note argues should be built first.

*Everything in nature moves on a curved path.*  The manuscript states it
as a geometric predicate rather than a feeling -- *"no part of the move
would be on a purely straight line"*, and *"sharp angles must be
avoided"* -- so a candidate inbetween can be measured against it instead
of discussed.

**Why this module has no arc-deviation function.** The acceptance note
also asks for the inbetween's *deviation from an arc fitted through the
neighbouring keys*.  On a single inbetween that is degenerate: three
distinct non-collinear points determine exactly one circle, so the
deviation of the inbetween from the circle through key-inbetween-key is
identically zero for every candidate, however bad.  Measured over 20 000
random inbetweens the worst deviation was 3.6e-12, which is
floating-point noise.  Deviation needs the arc fixed *independently* of
the candidate -- three keys, or two inbetweens -- and so belongs in a
separate function with a different fixture requirement.  See
``docs/planning/inking-and-tween-plugins.md`` section 10.

**This module measures; it does not judge.**  Thresholds are parameters
with provisional defaults, because where the line falls is a studio
judgement and Daniel's to set.  The manuscript names the two failures
but not the numbers.

Positions are in **millimetres on the page** and angles in **degrees**,
per section 11.2 of the planning note.  Nothing here knows what a
drawing looks like: it takes points, so whatever supplies them --
centre of ink, a tracked hand, a tagged landmark -- is somebody else's
problem and can change without touching this.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

#: A position on the page, in millimetres.
Point = Tuple[float, float]

#: Provisional.  A path this close to 180 degrees reads as a straight
#: line, which the principle forbids outright.  Daniel's to set.
DEFAULT_STRAIGHT_DEGREES: float = 175.0

#: Provisional.  Below this the path turns a corner rather than an arc.
#: Daniel's to set; the manuscript says "sharp", not how sharp.
DEFAULT_CORNER_DEGREES: float = 90.0


@dataclass(frozen=True)
class AngleReading:
    """One interior angle, and what it means at the given thresholds."""

    index: int
    degrees: float
    straight: bool
    corner: bool

    @property
    def accepted(self) -> bool:
        """Neither a straight run nor a corner."""
        return not (self.straight or self.corner)


def interior_angle(before: Point, at: Point, after: Point) -> float:
    """The angle at ``at``, in degrees, between its two neighbours.

    180 is a straight line through all three; 0 would be a complete
    reversal.  Raises :class:`ValueError` if ``at`` coincides with a
    neighbour, where the angle is undefined rather than zero.

    Computed as ``atan2(|cross|, dot)`` rather than from the cosine.
    Near 180 degrees the cosine flattens out -- its derivative goes to
    zero -- so ``acos`` loses precision in exactly the region this
    check does its work, and rounding can push the argument outside
    [-1, 1] and raise where the answer is simply 180.  ``atan2`` has
    neither problem and needs no clamp.
    """
    ux, uy = before[0] - at[0], before[1] - at[1]
    vx, vy = after[0] - at[0], after[1] - at[1]
    if (ux, uy) == (0.0, 0.0) or (vx, vy) == (0.0, 0.0):
        raise ValueError(
            "the angle at a point coinciding with one of its neighbours "
            "is undefined; got "
            f"before={before!r}, at={at!r}, after={after!r}")
    cross = ux * vy - uy * vx
    dot = ux * vx + uy * vy
    return math.degrees(math.atan2(abs(cross), dot))


def interior_angles(path: Sequence[Point]) -> List[float]:
    """The angle at every interior point of ``path``.

    One shorter by two than the path, so a bare key pair gives none --
    which is correct, not an error: with no inbetween there is nothing
    to judge.
    """
    return [interior_angle(path[i - 1], path[i], path[i + 1])
            for i in range(1, len(path) - 1)]


def read_path(
    path: Sequence[Point],
    straight_degrees: float = DEFAULT_STRAIGHT_DEGREES,
    corner_degrees: float = DEFAULT_CORNER_DEGREES,
) -> List[AngleReading]:
    """Measure every interior point and say what each one reads as.

    ``index`` is the position in ``path``, so a rejection can name the
    drawing rather than its offset among the interior points.

    Every interior point is reported, passing ones included.  A harness
    that returns only failures cannot be told apart from one that is
    not running.
    """
    readings: List[AngleReading] = []
    for i in range(1, len(path) - 1):
        degrees = interior_angle(path[i - 1], path[i], path[i + 1])
        readings.append(AngleReading(
            index=i,
            degrees=degrees,
            straight=degrees >= straight_degrees,
            corner=degrees <= corner_degrees,
        ))
    return readings
