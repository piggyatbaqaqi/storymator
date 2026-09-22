"""Finding coloured peg crowns by chroma rather than by brightness.

The peg tops are marked with ink, and the ink is the one thing in the
frame whose *colour* differs from the paper.  Shadows do not qualify:
a shadow is the paper at lower luminance and the same hue, which is
why the greyscale detector has never been able to tell one from a peg.

**Chroma gates; greyscale measures.** Nothing here produces geometry.
The ink says *a peg is about here*, and :func:`acme.rect.fit_rect`
then takes the rectangle off luminance, where the whole crown is
visible whether or not the pen reached all of it.  Coverage is uneven
-- in ``fresh_ink_007`` one rect peg gives 1781 ink pixels and the
other gives 35, with both crowns looking thoroughly blue -- so a
rectangle fitted to the ink would have an angle that means nothing.

The colour itself lives in an :class:`acme.model.InkSignature` on the
calibration, so changing ink is editing a JSON file.  Nothing in this
module names a hue.

Representation, chosen by measurement over the whole inked corpus
(docs/planning/ink-landmarks.md): white-balance the frame against the
paper by von Kries scaling, convert to CIE L*a*b*, and take the
**angle of (a*, b*)**.  Two rival representations were tried on
identical pixels --

    Lab with the paper's chroma subtracted   sd 5.1 deg, spread 21.4
    von Kries then r,g chromaticity          sd 10.1 deg, spread 33.5
    von Kries then Lab a*b* angle            sd 4.1 deg, spread 13.2

-- across two days, four lighting setups, blank paper and artwork, a
bar move and a re-inking.  The third wins because Lab's cube root
makes the (a*, b*) *angle* almost invariant to how brightly a peg
happens to render, which is the dominant nuisance: the three pegs are
mirrors at different angles and vary 2.4x in chroma magnitude within a
single frame.

Magnitude is a loose gate, not a measure.  ``C*/(L* + 16)`` is exactly
scale-invariant where Lab is a cube root, but peg crowns are dark
enough to reach the linear segment, where it is not: halving the light
costs the angle 3.2 degrees and the relative chroma 16.5 %.  So the
angle discriminates and the magnitude only rejects grey.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import numpy as np

from .model import InkSignature

# D65, and the sRGB primaries.  Spelled out rather than imported so
# this module keeps the same dependency footprint as the rest of acme.
_RGB_TO_XYZ = np.array([
    [0.4124, 0.3576, 0.1805],
    [0.2126, 0.7152, 0.0722],
    [0.0193, 0.1192, 0.9505],
], dtype=float)
_WHITE_D65 = np.array([0.95047, 1.0, 1.08883], dtype=float)
_DELTA = 6.0 / 29.0

# L* is 116 f(Y/Yn) - 16, so L* + 16 carries the same cube root as a*
# and b* do.  It is the Lab definition, not a fudge factor.
_L_OFFSET = 16.0


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """(..., 3) sRGB in 0-255 or 0-1 to CIE L*a*b*."""
    raise NotImplementedError


def white_point(rgb: np.ndarray, inside: Optional[np.ndarray] = None,
                percentile: float = 90.0) -> np.ndarray:
    """The paper's own RGB, as the white reference for von Kries."""
    raise NotImplementedError


def balance(rgb: np.ndarray, white: np.ndarray) -> np.ndarray:
    """von Kries: scale each channel so ``white`` becomes neutral."""
    raise NotImplementedError


def chroma_angle_deg(lab: np.ndarray) -> np.ndarray:
    """Angle of (a*, b*), in degrees. The colour-bearing quantity."""
    raise NotImplementedError


def relative_chroma(lab: np.ndarray) -> np.ndarray:
    """``C*/(L* + 16)``: chroma with most of the brightness divided out."""
    raise NotImplementedError


def ink_mask(rgb: np.ndarray, signature: InkSignature,
             inside: Optional[np.ndarray] = None) -> np.ndarray:
    """Pixels whose colour matches ``signature``."""
    raise NotImplementedError


def ink_windows(mask: np.ndarray, min_area_px: float = 12.0,
                pad_px: int = 12) -> List[Tuple[slice, slice]]:
    """Bounding boxes around each ink patch, padded to hold the crown.

    Padding is the point: the ink is a subset of the peg top, so a box
    drawn tightly around it cuts off the part the geometry comes from.
    """
    raise NotImplementedError


def measure_signature(rgb: np.ndarray,
                      windows: Sequence[Tuple[int, int]],
                      name: str = "",
                      radius_px: int = 70) -> InkSignature:
    """Derive a signature from a frame with known peg locations.

    What ``bin/measure-ink`` is for: onboarding a new ink is shooting
    one frame, not guessing at a colour name.
    """
    raise NotImplementedError
