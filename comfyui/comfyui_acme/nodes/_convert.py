"""Tensor <-> numpy at the ComfyUI boundary, and overlay drawing.

Kept apart from ``acme`` on purpose: everything in this file knows
about torch and ComfyUI conventions, and nothing in ``acme`` does.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from ..acme.rect import Rect

import numpy as np
import torch
from PIL import Image, ImageDraw


def batch_to_numpy(images: torch.Tensor) -> List[np.ndarray]:
    """(B, H, W, C) float tensor -> list of (H, W, C) float arrays."""
    return [f.detach().cpu().numpy().astype(np.float64) for f in images]


def to_gray(frame: np.ndarray) -> np.ndarray:
    """Luminance, for detection.  Rec. 709, because the pencil we care
    about is neutral and the undercolour is not."""
    if frame.ndim == 2:
        return frame
    weights = np.array([0.2126, 0.7152, 0.0722])[:frame.shape[2]]
    return (frame[..., :len(weights)] * weights).sum(axis=-1) / weights.sum()


def stack_to_tensor(frames: List[np.ndarray]) -> torch.Tensor:
    """List of (H, W[, C]) -> (B, H, W, C) float32 tensor."""
    prepared = []
    for f in frames:
        arr = f if f.ndim == 3 else f[:, :, None]
        if arr.shape[2] == 1:
            arr = np.repeat(arr, 3, axis=2)
        prepared.append(np.clip(arr, 0.0, 1.0).astype(np.float32))
    return torch.from_numpy(np.stack(prepared))


def masks_to_tensor(masks: List[np.ndarray]) -> torch.Tensor:
    """List of (H, W) bool -> (B, H, W) float32 tensor."""
    return torch.from_numpy(
        np.stack([m.astype(np.float32) for m in masks]))


def draw_overlay(frame: np.ndarray, corners: Optional[np.ndarray],
                 pegs: Optional[np.ndarray], caption: str,
                 accepted: bool,
                 colour: Optional[Tuple[int, int, int]] = None,
                 peg_rects: Optional[Sequence["Rect"]] = None
                 ) -> np.ndarray:
    """The fit drawn over the frame, with its verdict written on it.

    The caption is burned in rather than only returned as a string so
    that an ordinary PreviewImage shows the reason a frame was refused.
    Somebody looking at a contact sheet of two hundred captures should
    not have to wire up a text node to find the bad one.
    """
    rgb = frame if frame.ndim == 3 else np.repeat(frame[:, :, None], 3, 2)
    img = Image.fromarray(
        (np.clip(rgb[..., :3], 0, 1) * 255).astype(np.uint8)).convert("RGB")
    draw = ImageDraw.Draw(img)
    good = (60, 220, 120)
    bad = (250, 90, 70)
    # The verdict colours the marks by default.  A caller may override
    # it -- the greyscale diagnostic does, because the verdict is
    # already carried by the overlay and the report, and one fixed
    # colour stays legible on neutral whatever the outcome.
    if colour is None:
        colour = good if accepted else bad

    if corners is not None and len(corners) == 4:
        draw.polygon([tuple(p) for p in corners], outline=colour, width=3)
        for i, (x, y) in enumerate(corners):
            draw.text((x + 6, y + 6), str(i), fill=colour)
    if pegs is not None:
        r = max(6, img.width // 120)
        for index, (x, y) in enumerate(pegs):
            # The fitted slot when there is one: an outline says "this
            # shape, this angle, this long", which is checkable at a
            # glance.  A circle only says "something is here".
            rect = peg_rects[index] if peg_rects is not None else None
            if rect is not None:
                draw.polygon([tuple(p) for p in rect.corners()],
                             outline=colour, width=3)
            else:
                draw.ellipse([x - r, y - r, x + r, y + r],
                             outline=colour, width=3)
            draw.line([x - r * 2, y, x + r * 2, y], fill=colour, width=1)
            draw.line([x, y - r * 2, x, y + r * 2], fill=colour, width=1)

    # An empty caption means no banner at all, which keeps the
    # greyscale diagnostic uniformly grey outside the marks -- the
    # property that makes "anything with R > G is a mark" true.
    if caption:
        pad = 6
        lines = [caption[i:i + 88] for i in range(0, len(caption), 88)]
        box_h = 14 * len(lines) + 2 * pad
        draw.rectangle([0, 0, img.width, box_h], fill=(20, 20, 24))
        for i, line in enumerate(lines):
            draw.text((pad, pad + 14 * i), line, fill=colour)
    return np.asarray(img).astype(np.float64) / 255.0


def residual_chart(values: List[float], accepted: List[bool],
                   threshold: float, size: Tuple[int, int] = (720, 260)
                   ) -> np.ndarray:
    """A bar per frame, with the rejection threshold drawn across.

    Hand-rolled rather than matplotlib: this pack's only dependency
    beyond ComfyUI's own is OpenCV, and adding a plotting stack to draw
    one bar chart is not a trade worth making.
    """
    width, height = size
    img = Image.new("RGB", (width, height), (18, 18, 22))
    draw = ImageDraw.Draw(img)
    if not values:
        draw.text((10, 10), "no frames", fill=(200, 200, 200))
        return np.asarray(img).astype(np.float64) / 255.0

    margin = 34
    top = max(max(values), threshold) * 1.25 or 1.0
    plot_h = height - 2 * margin
    bar_w = max(1.0, (width - 2 * margin) / len(values))

    for i, (value, ok) in enumerate(zip(values, accepted)):
        x = margin + i * bar_w
        h = 0.0 if not np.isfinite(value) else min(value / top, 1.0) * plot_h
        draw.rectangle([x, height - margin - h, x + max(bar_w - 1, 1),
                        height - margin],
                       fill=(60, 220, 120) if ok else (250, 90, 70))

    y = height - margin - (threshold / top) * plot_h
    draw.line([margin, y, width - margin, y], fill=(240, 200, 80), width=2)
    draw.text((margin, max(0, y - 16)),
              f"threshold {threshold:.2f} px", fill=(240, 200, 80))
    draw.text((6, 6), f"registration residual, px   (max {top/1.25:.2f})",
              fill=(210, 210, 215))
    draw.text((6, height - 18), f"{len(values)} frames",
              fill=(150, 150, 158))
    return np.asarray(img).astype(np.float64) / 255.0
