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

# How far from a candidate hue a pixel may sit and still be
# counted as that hue while the direction is being refined.
_HUE_WINDOW_DEG = 40.0

# Below this, the "ink" is paper and the hue is noise.
_MIN_MEASURABLE_CHROMA = 0.05


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """(..., 3) sRGB in 0-255 or 0-1 to CIE L*a*b*."""
    arr = np.asarray(rgb, dtype=float)
    if arr.shape[-1] != 3:
        raise ValueError(f"expected a trailing RGB axis, got {arr.shape}")
    if arr.max(initial=0.0) > 1.0:
        arr = arr / 255.0
    arr = np.clip(arr, 0.0, 1.0)
    linear = np.where(arr <= 0.04045, arr / 12.92,
                      ((arr + 0.055) / 1.055) ** 2.4)
    xyz = linear.reshape(-1, 3) @ _RGB_TO_XYZ.T / _WHITE_D65
    f = np.where(xyz > _DELTA ** 3, np.cbrt(xyz),
                 xyz / (3 * _DELTA ** 2) + 4.0 / 29.0)
    lab = np.stack([116.0 * f[:, 1] - 16.0,
                    500.0 * (f[:, 0] - f[:, 1]),
                    200.0 * (f[:, 1] - f[:, 2])], axis=1)
    return lab.reshape(arr.shape)


def white_point(rgb: np.ndarray, inside: Optional[np.ndarray] = None,
                percentile: float = 90.0) -> np.ndarray:
    """The paper's own RGB, as the white reference for von Kries.

    The paper, not a grey card: it is the only reference that is in
    every frame, and the illuminant is whatever was on the desk that
    evening.  Canson cream is not neutral, which is exactly why it has
    to be measured rather than assumed.
    """
    arr = np.asarray(rgb, dtype=float)
    flat = arr.reshape(-1, 3) if inside is None else arr[inside]
    if flat.size == 0:
        raise ValueError("no pixels to take a white point from")
    lum = flat @ np.array([0.2126, 0.7152, 0.0722])
    bright = flat[lum >= np.percentile(lum, percentile)]
    white = bright.mean(axis=0)
    if not np.all(white > 1e-6):
        raise ValueError(f"white point {white} has a dead channel")
    return white


def balance(rgb: np.ndarray, white: np.ndarray) -> np.ndarray:
    """von Kries: scale each channel so ``white`` becomes neutral.

    Scaling is the whole of it, and it is what makes the mask
    indifferent to white balance: a camera's channel gains multiply,
    and dividing by a white measured in the same frame cancels them
    exactly.
    """
    arr = np.asarray(rgb, dtype=float)
    w = np.asarray(white, dtype=float)
    scaled = arr / np.maximum(w, 1e-6) * float(w.mean())
    return np.clip(scaled, 0.0, 255.0 if arr.max(initial=0.0) > 1.0 else 1.0)


def chroma_angle_deg(lab: np.ndarray) -> np.ndarray:
    """Angle of (a*, b*), in degrees. The colour-bearing quantity."""
    arr = np.asarray(lab, dtype=float)
    return np.degrees(np.arctan2(arr[..., 2], arr[..., 1]))


def relative_chroma(lab: np.ndarray) -> np.ndarray:
    """``C*/(L* + 16)``: chroma with most of the brightness divided out.

    Exactly scale-invariant where Lab is a cube root, because L* + 16
    carries the same one.  Peg crowns are dark enough to reach the
    linear segment, where it is not -- hence a floor rather than a
    measurement.
    """
    arr = np.asarray(lab, dtype=float)
    return (np.hypot(arr[..., 1], arr[..., 2])
            / np.maximum(arr[..., 0] + _L_OFFSET, 1e-6))


def _angular_difference(a: np.ndarray, b: float) -> np.ndarray:
    """Shortest signed distance between angles, in degrees."""
    return np.abs((np.asarray(a, dtype=float) - b + 180.0) % 360.0 - 180.0)


def ink_mask(rgb: np.ndarray, signature: InkSignature,
             inside: Optional[np.ndarray] = None) -> np.ndarray:
    """Pixels whose colour matches ``signature``."""
    lab = srgb_to_lab(balance(rgb, white_point(rgb, inside)))
    match = (_angular_difference(chroma_angle_deg(lab),
                                 signature.direction_deg)
             <= signature.tolerance_deg)
    match &= relative_chroma(lab) >= signature.min_chroma
    if inside is not None:
        match &= inside
    return match


def ink_windows(mask: np.ndarray, min_area_px: float = 12.0,
                pad_px: int = 12,
                merge_px: Optional[int] = None) -> List[Tuple[slice, slice]]:
    """Bounding boxes around each ink patch, padded to hold the crown.

    Padding is the point: the ink is a subset of the peg top, so a box
    drawn tightly around it cuts off the part the geometry comes from.
    A window therefore has to be about a crown wide even when the ink
    is a speck.

    Merging happens *before* padding, and over a shorter distance.
    Padding far enough to hold a crown is also far enough to bridge
    the gap to the next peg, so merging padded boxes would fuse the
    bar into one window; merging the patches themselves joins only
    what is on the same crown.
    """
    from scipy import ndimage
    if merge_px is None:
        merge_px = max(pad_px // 3, 1)
    labels, count = ndimage.label(mask)
    rows, cols = mask.shape
    boxes: List[Tuple[slice, slice]] = []
    for index, box in enumerate(ndimage.find_objects(labels), start=1):
        if box is None or (labels[box] == index).sum() < min_area_px:
            continue
        boxes.append((
            slice(max(box[0].start - merge_px, 0),
                  min(box[0].stop + merge_px, rows)),
            slice(max(box[1].start - merge_px, 0),
                  min(box[1].stop + merge_px, cols))))
    grow = pad_px - merge_px
    return [(slice(max(b[0].start - grow, 0), min(b[0].stop + grow, rows)),
             slice(max(b[1].start - grow, 0), min(b[1].stop + grow, cols)))
            for b in _merge_overlapping(boxes)]


def _merge_overlapping(
        boxes: List[Tuple[slice, slice]]) -> List[Tuple[slice, slice]]:
    """One window per peg, however many patches the pen left on it.

    Uneven coverage breaks a crown's ink into several patches -- six
    components across three pegs in ``blue_010`` -- and each would
    otherwise propose its own candidate for the same peg.
    """
    merged: List[Tuple[slice, slice]] = []
    for box in boxes:
        for i, other in enumerate(merged):
            if (box[0].start < other[0].stop and other[0].start < box[0].stop
                    and box[1].start < other[1].stop
                    and other[1].start < box[1].stop):
                merged[i] = (
                    slice(min(box[0].start, other[0].start),
                          max(box[0].stop, other[0].stop)),
                    slice(min(box[1].start, other[1].start),
                          max(box[1].stop, other[1].stop)))
                break
        else:
            merged.append(box)
    return merged


def _dominant_hue(angles: np.ndarray,
                  weights: np.ndarray) -> Tuple[float, np.ndarray]:
    """The hue most of the ink actually has, and its scatter.

    A circular *mean* is the wrong summary here and measurably so. The
    pixels handed in are dark and saturated, which is most of the ink
    and also a fair amount of sensor noise; noise hues are spread over
    the whole circle and drag a mean off the ink while inflating its
    standard deviation. Pooled over the corpus that gave 53.5 degrees
    of scatter for an ink that holds to about 9.

    The ink is instead the *mode*: the one hue many pixels agree on.
    Take the peak of a smoothed circular histogram, weighted by
    chroma so a saturated pixel counts for more than a grey one, then
    refine within a window around it. Pooled, that returns -59.6
    degrees with 9.2 of scatter, and the six inked frames individually
    land between -56.3 and -63.6.
    """
    edges = np.arange(-180.0, 181.0, 5.0)
    hist, _ = np.histogram(angles, bins=edges, weights=weights)
    # Smooth around the wrap, so a peak straddling +/-180 -- where this
    # ink very nearly sits -- is not split between the two end bins.
    padded = np.concatenate([hist[-4:], hist, hist[:4]])
    hist = np.convolve(padded, np.ones(9) / 9.0, mode="same")[4:-4]
    peak = float((edges[:-1] + 2.5)[int(np.argmax(hist))])

    direction = peak
    for _ in range(2):
        near = _angular_difference(angles, direction) <= _HUE_WINDOW_DEG
        if not near.any():
            break
        radians = np.radians(angles[near])
        direction = float(np.degrees(np.arctan2(
            np.sin(radians).mean(), np.cos(radians).mean())))
    near = _angular_difference(angles, direction) <= _HUE_WINDOW_DEG
    return direction, _angular_difference(angles[near], direction)


def measure_signature(rgb: np.ndarray,
                      windows: Sequence[Tuple[int, int]],
                      name: str = "",
                      radius_px: int = 70) -> InkSignature:
    """Derive a signature from a frame with known peg locations.

    What ``bin/measure-ink`` is for: onboarding a new ink is shooting
    one frame, not guessing at a colour name.

    The direction is a *circular* mean.  The corpus's blue sits near
    -180 degrees on two pegs and just past +180 on a third, where an
    arithmetic mean returns roughly zero -- the opposite hue -- and a
    standard deviation of 161 degrees on a quantity that actually
    holds to 4.
    """
    arr = np.asarray(rgb, dtype=float)
    rows, cols = arr.shape[:2]
    angles: List[float] = []
    chromas: List[float] = []
    for cx, cy in windows:
        patch = arr[max(cy - radius_px, 0):min(cy + radius_px, rows),
                    max(cx - radius_px, 0):min(cx + radius_px, cols)]
        if patch.size == 0:
            continue
        lab = srgb_to_lab(balance(patch, white_point(patch)))
        rel = relative_chroma(lab)
        # The ink is the most saturated thing on a peg: the crown
        # around it and the paper beyond it are both near-neutral.
        # Saturation alone admits plenty of noise -- near-black pixels
        # have hues that are mostly sensor noise -- but the noise
        # points every which way and :func:`_dominant_hue` discards it
        # by taking the mode rather than the mean.  Filtering on
        # darkness here instead was tried and is worse: it needs a
        # percentile of luminance, which on a frame with only two
        # distinct levels selects everything.
        picked = rel >= np.percentile(rel, 90)
        if picked.sum() < 4:
            continue
        angles.extend(chroma_angle_deg(lab)[picked].tolist())
        chromas.extend(rel[picked].tolist())
    if not angles:
        raise ValueError("no ink found in any of the given windows")
    # Selecting the most saturated pixels always returns *something*,
    # so bare paper yields a confident signature for a colour that is
    # not there.  Real ink on a crown sits at 0.38 to 0.77 relative
    # chroma across the corpus; unmarked paper is two orders below
    # that.
    typical = float(np.median(chromas))
    if typical < _MIN_MEASURABLE_CHROMA:
        raise ValueError(
            f"no ink found in any of the given windows: the most "
            f"saturated pixels there sit at {typical:.3f} relative "
            f"chroma, against {_MIN_MEASURABLE_CHROMA:.2f} for anything "
            f"worth calling a colour -- are the windows on the pegs, "
            f"and did the ink take?")
    direction, spread = _dominant_hue(np.asarray(angles),
                                      np.asarray(chromas))
    chromas = list(np.asarray(chromas)[
        _angular_difference(np.asarray(angles), direction) <= 40.0])
    # Bounded at both ends on purpose.  Below 15 degrees a signature
    # measured off one good frame would reject a peg that renders a
    # little differently on the next; above 45 it is admitting a
    # quarter of the hue circle, which is no longer a colour.
    tolerance = float(np.clip(3.0 * spread.std() + 5.0, 15.0, 45.0))
    return InkSignature(
        direction_deg=round(direction, 1),
        tolerance_deg=round(tolerance, 1),
        # Half the ink's typical chroma, not a low percentile of it.
        # The tail of this distribution is the crown around the ink
        # rather than the ink, so a percentile floor lets the whole
        # crown through and the windows merge into one.
        min_chroma=round(float(np.median(chromas) * 0.5), 3),
        name=name)
