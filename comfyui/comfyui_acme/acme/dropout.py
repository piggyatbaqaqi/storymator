"""Colour dropout: keep the graphite, whiten the undercolour.

Animators block in with a coloured pencil -- non-photo blue
historically, carmine for Dr. Boulos -- and draw the keeper line over
it in graphite.  Dropout is what a reprographic camera did with
non-photo blue: render the coloured pencil as paper and the graphite as
line.

**Why not a hue threshold.**  The first attempt was the OpenToonz
"Blue Sketch Cleaner", which selects pixels by HSV hue.  On
``ManRunCycle_Rough_CleanUp_2001_WWC/10F/20260920-001539.png`` the
blue "1" measures H 99, S 56 -- but the *graphite* measures H 97, S 38
at the median, because a dark neutral with a few counts of blue cast
has a large saturation (S is a ratio over V).  Both land in the same
window, and no setting separates them.

**What works.**  White-balance against the paper, then take each
pixel's *brightest* channel.  A light coloured pencil reflects nearly
as much as paper in at least one channel (non-photo blue in blue,
carmine in red), so its brightest channel is near paper white.
Graphite is neutral and dark, so it is dark in every channel,
including the brightest.  A levels step then maps anything at or above
``white_level`` of paper to white.

Nothing here names a hue, so it serves blue and carmine alike.  The
price is that a *dark* saturated colour -- ballpoint blue, say -- is
dark in every channel too and is kept, as line.  That is the right
answer for a dropout: non-photo blue is defined by being light.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .ink import white_point

_REC709 = np.array([0.2126, 0.7152, 0.0722])


@dataclass(frozen=True)
class DropoutResult:
    """What :func:`dropout_colour` produces for one frame.

    ``gray``     (H, W) float in [0, 1]: the graphite on white.
    ``dropped``  (H, W) bool: pixels that a plain luminance render
                 would have kept as marks (luminance below
                 ``mark_level`` of paper) but which the dropout
                 rendered white -- i.e. what was taken away, so it can
                 be checked.
    ``white``    (3,) the paper white the frame was balanced against,
                 in the input's own units.
    """

    gray: np.ndarray
    dropped: np.ndarray
    white: np.ndarray


def dropout_colour(rgb: np.ndarray, white_percentile: float = 90.0,
                   white_level: float = 0.85,
                   mark_level: float = 0.88) -> DropoutResult:
    """Render light coloured pencil as paper and graphite as line.

    ``rgb`` is (H, W, C) with C >= 3, in any scale (0-1 float or 0-255);
    only the first three channels are used.  ``white_percentile`` picks
    the paper white, as in :func:`acme.ink.white_point`.
    ``white_level`` is the fraction of paper white at or above which a
    pixel's brightest channel renders white.  ``mark_level`` only
    shapes the ``dropped`` report: a pixel counts as a mark when its
    balanced luminance is below this fraction of paper white.  It is
    separate from ``white_level`` so that moving the whitening cutoff
    does not also move what the report calls a mark.

    The 0.85 default is measured on the run-cycle scan.  Of the blue
    "1"'s 392 mark pixels, 0.88 rendered 299 exactly white and left 64
    at 0.95 or lighter; 0.85 renders 356 white and keeps 99.1 % of the
    face's graphite as line; 0.82 renders 372 but starts eating
    graphite (98.3 %, 9 pixels dropped).
    """
    arr = np.asarray(rgb)
    if arr.ndim != 3 or arr.shape[2] < 3:
        raise ValueError(f"expected (H, W, C>=3), got shape {arr.shape}")
    if not 0.0 < white_level <= 1.0:
        raise ValueError(f"white_level {white_level} not in (0, 1]")
    if not 0.0 < mark_level <= 1.0:
        raise ValueError(f"mark_level {mark_level} not in (0, 1]")
    if not 0.0 <= white_percentile < 100.0:
        raise ValueError(
            f"white_percentile {white_percentile} not in [0, 100)")

    colour = arr[..., :3].astype(float)
    white = white_point(colour, percentile=white_percentile)
    # Dividing by the measured white is the whole of the balance, and
    # it also removes the input's scale: 0-255 and 0-1 come out alike.
    balanced = np.clip(colour / white, 0.0, 1.0)
    gray = np.clip(balanced.max(axis=2) / white_level, 0.0, 1.0)
    lum = balanced @ _REC709
    dropped = (lum < mark_level) & (gray >= 1.0)
    return DropoutResult(gray=gray, dropped=dropped, white=white)
