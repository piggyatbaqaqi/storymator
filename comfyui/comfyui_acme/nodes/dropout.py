"""Colour dropout as a node: graphite kept, coloured undercolour gone."""

from __future__ import annotations

import torch
from comfy_api.latest import io

from ..acme.dropout import dropout_colour
from ._convert import batch_to_numpy, masks_to_tensor, stack_to_tensor
from .registration import CATEGORY


class AcmeColourDropout(io.ComfyNode):
    """Whiten light coloured pencil, keep graphite.

    See :mod:`acme.dropout` for why this is not a hue threshold.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeColourDropout",
            display_name="ACME Colour Dropout",
            category=CATEGORY,
            description="Non-photo-blue (or carmine) dropout: renders "
                        "light coloured pencil as paper and graphite "
                        "as line. White-balances each frame against "
                        "its own paper.",
            inputs=[
                io.Image.Input("image"),
                io.Float.Input(
                    "white_percentile", default=90.0, min=50.0,
                    max=99.9, step=0.1,
                    tooltip="Brightness percentile taken as the paper. "
                            "Lower it only if the drawing covers most "
                            "of the sheet."),
                io.Float.Input(
                    "white_level", default=0.85, min=0.5, max=1.0,
                    step=0.01,
                    tooltip="A pixel whose brightest channel reaches "
                            "this fraction of paper white renders "
                            "white. Lower it if coloured pencil "
                            "survives; raise it if faint graphite "
                            "disappears."),
                io.Float.Input(
                    "mark_level", default=0.88, min=0.5, max=1.0,
                    step=0.01,
                    tooltip="Only affects the dropped mask: a pixel "
                            "darker than this fraction of paper white "
                            "counts as a mark, and is shown if the "
                            "dropout whitened it."),
            ],
            outputs=[io.Image.Output("image"),
                     io.Mask.Output("dropped",
                                    tooltip="What a greyscale render "
                                            "would have kept but the "
                                            "dropout whitened.")],
        )

    @classmethod
    def execute(cls, image: torch.Tensor, white_percentile: float,
                white_level: float, mark_level: float) -> io.NodeOutput:
        grays, masks = [], []
        for frame in batch_to_numpy(image):
            out = dropout_colour(frame, white_percentile, white_level,
                                 mark_level)
            grays.append(out.gray)
            masks.append(out.dropped)
        return io.NodeOutput(stack_to_tensor(grays),
                             masks_to_tensor(masks))
