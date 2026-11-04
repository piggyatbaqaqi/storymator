"""The AcmeColourDropout node, imported for real.

The arithmetic is tested in ``acme/dropout_test.py``; this checks only
the ComfyUI boundary -- tensor layout, batching, and that each frame is
balanced against its own paper.  Skips without ComfyUI, as
``tests/test_nodes.py`` does.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

pytest.importorskip("comfy_api.latest",
                    reason="needs ComfyUI on the path; run under the "
                           "environment ComfyUI runs in")

from comfyui_acme.acme.dropout_test import (BLOCKS, PAPER,  # noqa: E402
                                            scene)
from comfyui_acme.nodes import PHASE_1, AcmeColourDropout  # noqa: E402


def _batch(*frames: np.ndarray) -> torch.Tensor:
    return torch.from_numpy(np.stack(frames).astype(np.float32))


def test_node_is_registered() -> None:
    assert AcmeColourDropout in PHASE_1
    assert AcmeColourDropout.define_schema().node_id == "AcmeColourDropout"


def test_outputs_a_grey_image_and_a_mask_per_frame() -> None:
    image, dropped = AcmeColourDropout.execute(
        _batch(scene(), scene()), 90.0, 0.88, 0.88).result
    assert isinstance(image, torch.Tensor)
    assert isinstance(dropped, torch.Tensor)
    assert image.shape == (2,) + scene().shape
    assert dropped.shape == (2,) + scene().shape[:2]
    assert image.dtype == torch.float32 and dropped.dtype == torch.float32
    assert torch.equal(image[..., 0], image[..., 1])
    assert torch.equal(image[..., 1], image[..., 2])


def test_blue_is_whitened_and_graphite_kept() -> None:
    image, dropped = AcmeColourDropout.execute(
        _batch(scene()), 90.0, 0.88, 0.88).result
    npb, graphite = BLOCKS["npb"], BLOCKS["graphite"]
    assert torch.all(image[0][npb] == 1.0)
    assert torch.all(dropped[0][npb] == 1.0)
    assert torch.all(image[0][graphite] < 0.6)
    assert torch.all(dropped[0][graphite] == 0.0)


def test_each_frame_is_balanced_against_its_own_paper() -> None:
    """A batch mixing two white balances renders both frames alike."""
    warm = scene(PAPER * np.array([1.0, 0.85, 0.7]))
    image, _ = AcmeColourDropout.execute(
        _batch(scene(), warm), 90.0, 0.88, 0.88).result
    torch.testing.assert_close(image[0], image[1], atol=1e-5, rtol=0)


@pytest.mark.xfail(strict=True,
                   reason="mark_level is accepted but not yet used")
def test_dropped_mask_follows_mark_level() -> None:
    """Non-photo blue (luminance 0.837 of paper) is whitened either
    way, but reported only when the mark line sits above it."""
    _, above = AcmeColourDropout.execute(
        _batch(scene()), 90.0, 0.88, 0.88).result
    _, below = AcmeColourDropout.execute(
        _batch(scene()), 90.0, 0.88, 0.8).result
    npb = BLOCKS["npb"]
    assert torch.all(above[0][npb] == 1.0)
    assert torch.all(below[0][npb] == 0.0)
