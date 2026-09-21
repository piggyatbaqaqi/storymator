"""Resampling a frame onto the canonical raster.

This is the plugin's actual product: every drawing on one fixed pixel
grid in ACME field coordinates, so frame n and frame n+1 can be
differenced, onion-skinned or measured with no further alignment.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy import ndimage

from .model import FieldSpec


def register_image(image: np.ndarray, transform: np.ndarray,
                   spec: FieldSpec, order: int = 1,
                   fill: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
    """Warp ``image`` (H, W) or (H, W, C) onto the canonical raster.

    ``transform`` maps image pixels to peg-frame millimetres; ``spec``
    maps peg-frame millimetres to output pixels.  Sampling runs
    backwards, output to input, which is what keeps the result free of
    holes.

    Returns ``(registered, valid)`` where ``valid`` marks the output
    pixels that actually drew from inside the source frame.  Callers
    must not treat the fill value as image content -- an unregistered
    border is not black paper.
    """
    width, height = spec.size_px
    ys, xs = np.mgrid[0:height, 0:width].astype(float)
    out_px = np.column_stack([xs.ravel(), ys.ravel(), np.ones(xs.size)])

    # output pixel -> peg mm -> source pixel
    to_source = np.linalg.inv(np.asarray(transform, float)) @ \
        np.linalg.inv(spec.matrix())
    src = out_px @ to_source.T
    w = src[:, 2:3]
    w[np.abs(w) < 1e-12] = 1e-12
    src_xy = src[:, :2] / w

    src_x = src_xy[:, 0].reshape(height, width)
    src_y = src_xy[:, 1].reshape(height, width)

    in_h, in_w = image.shape[:2]
    valid = ((src_x >= 0) & (src_x <= in_w - 1) &
             (src_y >= 0) & (src_y <= in_h - 1))

    planes = image if image.ndim == 3 else image[:, :, None]
    out = np.empty((height, width, planes.shape[2]), dtype=float)
    for c in range(planes.shape[2]):
        out[:, :, c] = ndimage.map_coordinates(
            planes[:, :, c].astype(float), [src_y, src_x],
            order=order, mode="constant", cval=fill)
    out[~valid] = fill

    if image.ndim == 2:
        out = out[:, :, 0]
    return out, valid
