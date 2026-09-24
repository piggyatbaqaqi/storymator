"""Geometry of the ACME rig: peg bar, sheet, and the canonical raster.

Every dimension here is a *default*, not a constant.  The bar in the
room is the ground truth and bars vary; docs/measuring-punch-tolerance.md
is the procedure for replacing these with measured values.

Defaults are the standard ACME bar as confirmed by the operator
2026-09-17: rectangular pegs 1/2" x 1/8", a 1/4" round peg, centres 4"
apart, so 8" rect-to-rect.

The **peg frame** is the project's canonical coordinate system:

    origin   centre of the round peg
    +x       along the bar, toward one rectangular peg
    +y       into the sheet, away from the punched edge
    units    millimetres

Choosing the round peg as origin rather than the sheet centre is
deliberate: the pegs are what the artist's drawings are actually aligned
to, so the canonical frame is the one the artwork lives in, and punch
tolerance shows up as sheet-outline error rather than contaminating
every coordinate.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional, Tuple

import numpy as np

MM_PER_INCH = 25.4


@dataclass(frozen=True)
class InkSignature:
    """What the peg crowns are coloured with, in chroma terms.

    The whole colour specification, so swapping ink is editing a JSON
    file rather than touching code.  ``direction_deg`` is the angle of
    (a*, b*) in CIE L*a*b* after the frame is white-balanced against
    the paper; see :mod:`acme.ink` for why that representation and not
    another.

    Defaults are the pen+GEAR dry-erase blue, pooled by
    :func:`acme.ink.measure_signature` over every inked frame in the
    corpus -- two days, four lighting setups, artwork, a bar move and
    a re-inking.  The six frames land individually between -56.3 and
    -63.6 degrees.

    The tolerance is far wider than that 7 degree spread on purpose.
    The nearest competitor in any real frame is the paper itself,
    about 100 degrees away, so there is nothing to be gained by being
    tight and a peg to be lost by it: the worn right-hand peg drops
    out at 25 degrees and is found at 32.
    """

    direction_deg: float = -59.6
    tolerance_deg: float = 32.0
    # C*/(L* + 16).  A floor that rejects grey, not a measurement:
    # peg crowns are dark enough to reach Lab's linear segment, where
    # this is no longer scale-invariant (halving the light costs it
    # 16.5 %), so it is set low and the angle does the deciding.
    min_chroma: float = 0.23
    name: str = "pen+GEAR dry erase blue"


@dataclass(frozen=True)
class PegModel:
    """The three pegs, in the peg frame."""

    round_diameter_mm: float = 0.25 * MM_PER_INCH      # 6.350
    rect_long_mm: float = 0.5 * MM_PER_INCH            # 12.700, along the bar
    rect_short_mm: float = 0.125 * MM_PER_INCH         # 3.175, across it
    centre_spacing_mm: float = 4.0 * MM_PER_INCH       # 101.600, round to rect
    # How high above the PAPER the thing actually detected stands, which
    # decides the parallax correction (see acme.parallax).  Zero means
    # the landmark is in the paper plane and needs none.
    #
    # On honbay_0001 the rect landmarks really are holes -- the slots
    # stand ~3 mm open and on-axis light does not reach in -- so they
    # are 0.  The round peg grips its hole, leaving nothing to see but
    # the dome, whose apparent position is the projection of the
    # hemisphere's centre.  Both default to 0 so a rig that has not
    # measured them is uncorrected rather than wrongly corrected.
    round_landmark_height_mm: float = 0.0
    rect_landmark_height_mm: float = 0.0

    def positions(self) -> np.ndarray:
        """(3, 2) peg centres: -x rect, round, +x rect, in that order."""
        s = self.centre_spacing_mm
        return np.array([[-s, 0.0], [0.0, 0.0], [s, 0.0]], dtype=float)

    def span_mm(self) -> float:
        return 2.0 * self.centre_spacing_mm

    def nominal_area_mm2(self) -> Tuple[float, float]:
        """(round, rect) areas, for sizing detection windows."""
        return (np.pi * (self.round_diameter_mm / 2) ** 2,
                self.rect_long_mm * self.rect_short_mm)


@dataclass(frozen=True)
class SheetModel:
    """The paper, in the peg frame.

    ``punch_offset_mm`` is the distance from the punched edge to the peg
    line.  It is nominal here and is exactly the quantity
    docs/measuring-punch-tolerance.md measures as ``offset_normal``.
    """

    width_mm: float = 10.5 * MM_PER_INCH               # 266.7
    height_mm: float = 12.5 * MM_PER_INCH              # 317.5
    punch_offset_mm: float = 12.0
    bar_position: str = "below"                        # below | above

    def corners(self) -> np.ndarray:
        """(4, 2) sheet corners in the peg frame, counter-clockwise from
        the punched edge's -x end.

        y always points into the sheet, so this is the same rectangle
        whichever convention the studio works in.  ``bar_position``
        affects only how the canonical raster is laid out (see
        :meth:`FieldSpec.for_sheet`), which is what keeps a bar-above
        studio's drawings from coming out upside down.
        """
        half = self.width_mm / 2.0
        near = -self.punch_offset_mm
        far = self.height_mm - self.punch_offset_mm
        return np.array([[-half, near], [half, near],
                         [half, far], [-half, far]], dtype=float)


@dataclass(frozen=True)
class FieldSpec:
    """How the peg frame is sampled into the output raster."""

    px_per_mm: float = 11.63        # 4K across a 13 in frame
    origin_mm: Tuple[float, float] = (0.0, 0.0)   # peg-frame point at px (0,0)
    size_px: Tuple[int, int] = (1024, 1024)       # (width, height)
    flip_y: bool = False

    @classmethod
    def for_sheet(cls, sheet: SheetModel, px_per_mm: float = 11.63,
                  margin_mm: float = 2.0) -> "FieldSpec":
        """A raster that just contains the sheet, plus a margin."""
        corners = sheet.corners()
        lo = corners.min(axis=0) - margin_mm
        hi = corners.max(axis=0) + margin_mm
        size = np.ceil((hi - lo) * px_per_mm).astype(int)
        flip = sheet.bar_position == "below"
        # Bar below means the sheet rises away from the operator, and
        # image rows increase downward, so the raster must flip to come
        # out the right way up.  Bar above needs no flip.
        origin = (float(lo[0]), float(hi[1]) if flip else float(lo[1]))
        return cls(px_per_mm=px_per_mm, origin_mm=origin,
                   size_px=(int(size[0]), int(size[1])), flip_y=flip)

    def matrix(self) -> np.ndarray:
        """3x3 taking peg-frame millimetres to output pixels."""
        sy = -self.px_per_mm if self.flip_y else self.px_per_mm
        return np.array([
            [self.px_per_mm, 0.0, -self.origin_mm[0] * self.px_per_mm],
            [0.0, sy, -self.origin_mm[1] * sy],
            [0.0, 0.0, 1.0],
        ], dtype=float)


@dataclass(frozen=True)
class Calibration:
    """Everything the fitter needs that is not the picture."""

    peg: PegModel = field(default_factory=PegModel)
    sheet: SheetModel = field(default_factory=SheetModel)
    field_spec: Optional[FieldSpec] = None
    camera_matrix: Optional[np.ndarray] = None   # 3x3, AcmeCalibrateLens
    dist_coeffs: Optional[np.ndarray] = None     # (5,) or (8,)
    # What the intrinsics were measured under -- frame size, focus,
    # board. Carried so a capture can be checked against them; see
    # acme.capture.verify_against.  Not geometry, so the fitter
    # ignores it.
    provenance: Optional[dict] = None
    # Absent means the rig has no coloured pegs and detection runs
    # on luminance exactly as it always has.  The whole existing
    # corpus is that case and must keep working.
    ink: Optional[InkSignature] = None

    def __post_init__(self):
        if self.field_spec is None:
            object.__setattr__(self, "field_spec",
                               FieldSpec.for_sheet(self.sheet))

    @property
    def raster(self) -> FieldSpec:
        """The output raster.

        ``field_spec`` is Optional only so that its default can be
        derived from the sheet in ``__post_init__``; a constructed
        Calibration always has one.  This accessor states that
        invariant once instead of leaving every caller to assert it.
        """
        assert self.field_spec is not None, "__post_init__ sets this"
        return self.field_spec

    def check_raster(self) -> None:
        """Raise unless the output raster contains the peg positions.

        A raster that misses them produces a registered frame that
        looks like blank paper rather than like an error, which is
        exactly how it went unnoticed.
        """
        raise NotImplementedError

    def with_bar_position(self, where: str) -> "Calibration":
        if where not in ("below", "above"):
            raise ValueError(f"bar_position must be below or above, "
                             f"not {where!r}")
        sheet = replace(self.sheet, bar_position=where)
        return replace(self, sheet=sheet,
                       field_spec=FieldSpec.for_sheet(
                           sheet, self.raster.px_per_mm))

    def to_dict(self) -> dict:
        def arr(a):
            return None if a is None else np.asarray(a).tolist()
        return {
            "peg": self.peg.__dict__,
            "sheet": self.sheet.__dict__,
            "field_spec": {**self.raster.__dict__},
            "camera_matrix": arr(self.camera_matrix),
            "dist_coeffs": arr(self.dist_coeffs),
            "provenance": self.provenance,
            "ink": None if self.ink is None else dict(self.ink.__dict__),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Calibration":
        def arr(a):
            return None if a is None else np.asarray(a, dtype=float)
        spec = dict(data["field_spec"])
        spec["origin_mm"] = tuple(spec["origin_mm"])
        spec["size_px"] = tuple(int(v) for v in spec["size_px"])
        return cls(
            peg=PegModel(**data["peg"]),
            sheet=SheetModel(**data["sheet"]),
            field_spec=FieldSpec(**spec),
            camera_matrix=arr(data.get("camera_matrix")),
            dist_coeffs=arr(data.get("dist_coeffs")),
            # Written as "_provenance" by hand-authored calibration
            # files, "provenance" by to_dict.  Accept both.
            provenance=data.get("provenance", data.get("_provenance")),
            ink=(None if data.get("ink") is None
                 else InkSignature(**data["ink"])),
        )
