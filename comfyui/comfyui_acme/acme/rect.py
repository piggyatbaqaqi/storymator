"""Fitting the slot, instead of averaging whatever is inside it.

A rectangular peg landmark is not a blob. It is a **hole in the
paper** with structure inside it: the peg body, the open end or ends of
the slot, the bar showing through, and a specular highlight wherever
the light happens to catch the chrome. Taking one centroid over all
that throws the structure away and lets the answer move with the
lighting -- measured on the rig, the detected point sat on a peg's left
shoulder in one frame and dead centre on its side in another.

The hole itself does not move. It is 15.75 x 3.09 mm of crisp paper
edge lying in the paper plane, and fitting **it** gives three things a
centroid cannot:

* a **centre** that is the midpoint of the hole's extent, so interior
  structure -- a highlight, a gap at one end, a peg sitting hard
  against one side -- does not shift it;
* an **angle**, which the bar constrains and which is currently
  discarded entirely;
* a **size**, which is free: anything not close to 15.75 x 3.09 mm is
  not a slot and should be refused rather than fitted.

**Extent, not mass.** That is the whole idea. A bright highlight
punching a hole in the middle of the blob moves its centre of mass and
leaves its bounding extent untouched.

OpenCV does this well, so it does the work: ``findContours`` plus
``minAreaRect`` is the oriented bounding rectangle, and the *outer*
contour ignores interior holes by construction -- which is precisely
the highlight case, for free and better tested than a hand-rolled
equivalent. It is imported lazily, as in :mod:`acme.lens` and
:mod:`acme.capture`, only so a missing install gives a sentence rather
than a traceback; ``opencv-contrib-python`` is a declared dependency of
this pack and is expected to be there.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class Rect:
    """An oriented rectangle in image pixels."""

    centre: np.ndarray          # (2,) x, y
    long_px: float
    short_px: float
    angle_rad: float            # of the long axis, from +x

    @property
    def elongation(self) -> float:
        return self.long_px / max(self.short_px, 1e-9)

    def corners(self) -> np.ndarray:
        """(4, 2) corners, counter-clockwise from the -long -short one."""
        along = np.array([np.cos(self.angle_rad), np.sin(self.angle_rad)])
        across = np.array([-along[1], along[0]])
        a, b = along * self.long_px / 2.0, across * self.short_px / 2.0
        return np.array([self.centre - a - b, self.centre + a - b,
                         self.centre + a + b, self.centre - a + b])

    def matches(self, long_px: float, short_px: float,
                tolerance: float = 0.25) -> bool:
        """Whether this is plausibly the slot we were looking for.

        Relative, on both axes: a slot is 15.75 x 3.09 mm and nothing
        else on the paper is, so this is the cheap refusal a centroid
        could never offer.
        """
        return (abs(self.long_px - long_px) <= tolerance * long_px
                and abs(self.short_px - short_px) <= tolerance * short_px)


def _cv2():
    try:
        import cv2
    except ModuleNotFoundError as exc:      # pragma: no cover
        raise RuntimeError(
            "slot fitting needs OpenCV: pip install "
            "opencv-contrib-python (see requirements.txt)") from exc
    return cv2


def _min_area_rect(mask: np.ndarray):
    """OpenCV's oriented bounding rectangle of the largest blob.

    ``RETR_EXTERNAL`` is the point: the outer contour steps around the
    shape and never enters it, so a hole punched in the middle by a
    specular highlight is not merely tolerated, it is invisible.
    """
    cv2 = _cv2()
    binary = np.ascontiguousarray((np.asarray(mask) > 0).astype(np.uint8))
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("no slot in an empty mask")
    return cv2.minAreaRect(max(contours, key=cv2.contourArea))


def principal_axes(mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Unit vectors along and across a mask's principal directions.

    The long axis comes first, and its sign is canonical so that two
    calls on the same shape cannot disagree by 180 degrees -- an
    arbitrary sign once registered two captures of one sheet into
    mirror images of each other.
    """
    angle = fit_rect(mask).angle_rad
    long_axis = np.array([np.cos(angle), np.sin(angle)])
    return long_axis, np.array([-long_axis[1], long_axis[0]])


def fit_rect(mask: np.ndarray,
             origin: Optional[Tuple[int, int]] = None) -> Rect:
    """An oriented rectangle covering ``mask``'s extent.

    ``origin`` is the crop's (x, y) in the full frame, so a caller
    working on a window need not translate the answer back.
    """
    (cx, cy), (w, h), angle_deg = _min_area_rect(mask)
    # OpenCV reports the angle of its own first side, which may be
    # either one.  Say which axis we mean.
    angle = np.radians(angle_deg if w >= h else angle_deg + 90.0)
    direction = np.array([np.cos(angle), np.sin(angle)])
    # Canonical sign: point the long axis into the right half-plane,
    # and up when it is vertical.
    if direction[0] < 0 or (direction[0] == 0 and direction[1] < 0):
        angle += np.pi
    angle = float((angle + np.pi) % (2 * np.pi) - np.pi)
    centre = np.array([cx, cy], dtype=float)
    if origin is not None:
        centre = centre + np.asarray(origin, dtype=float)
    return Rect(centre=centre, long_px=float(max(w, h)),
                short_px=float(min(w, h)), angle_rad=angle)
