"""Lens calibration: the one thing worth storing between sessions."""

from __future__ import annotations

from dataclasses import replace

from comfy_api.latest import io, ui

from ..acme.lens import calibrate
from ._convert import batch_to_numpy, to_gray
from .registration import CATEGORY, AcmeCalibrationType


class AcmeCalibrateLens(io.ComfyNode):
    """Focal length, principal point and distortion, from a checkerboard.

    Run once per camera and store the result.  It survives the camera
    being knocked -- pose is solved per frame from the sheet, so nothing
    positional is baked in here -- and only becomes invalid if zoom or
    focus change. Tape the focus ring.

    Worth the trouble for two reasons. Uncorrected radial distortion at
    4K with a wide lens is tens of pixels at the frame corners, and it
    lands in the registration residual where it is indistinguishable
    from paper curl. And a rectangle's aspect ratio cannot be recovered
    from a single perspective view *at all* without intrinsics --
    measured on the first rig photograph, the sheet's along-bar
    dimension solved to the same 10.63 in whatever perpendicular
    dimension was assumed, because the perpendicular one is simply
    unconstrained by the geometry.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeCalibrateLens",
            display_name="ACME Calibrate Lens",
            category=CATEGORY,
            description="Camera intrinsics from several checkerboard "
                        "views. Needs opencv-contrib-python.",
            inputs=[
                io.Image.Input(
                    "images",
                    tooltip="A dozen or more views of one checkerboard. "
                            "Tilt it for focal length, and push it into "
                            "the frame CORNERS for distortion -- that is "
                            "the only place distortion is big enough to "
                            "measure, and centred views alone recover k1 "
                            "badly."),
                AcmeCalibrationType.Input(
                    "calibration",
                    tooltip="Bar and sheet geometry to attach the "
                            "intrinsics to."),
                io.Int.Input("inner_columns", default=9, min=3, max=40,
                             tooltip="Inner corners across: the corners "
                                     "BETWEEN squares, not the squares. "
                                     "A 10x7 board has 9x6."),
                io.Int.Input("inner_rows", default=6, min=3, max=40),
                io.Float.Input("square_mm", default=20.0, min=1.0,
                               max=200.0, step=0.01,
                               tooltip="Measured, not nominal. Printed "
                                       "boards are rarely exactly the "
                                       "size claimed."),
            ],
            outputs=[AcmeCalibrationType.Output("calibration"),
                     io.String.Output("report")],
        )

    @classmethod
    def execute(cls, images, calibration, inner_columns, inner_rows,
                square_mm) -> io.NodeOutput:
        frames = [to_gray(f) for f in batch_to_numpy(images)]
        try:
            matrix, dist, rms, used, skipped = calibrate(
                frames, inner_columns, inner_rows, square_mm)
        except (ValueError, RuntimeError) as exc:
            text = f"calibration failed: {exc}"
            return io.NodeOutput(calibration, text,
                                 ui=ui.PreviewText(text))

        updated = replace(calibration, camera_matrix=matrix,
                          dist_coeffs=dist)
        lines = [
            f"calibrated on {len(used)}/{len(frames)} views, "
            f"reprojection rms {rms:.3f} px",
            "",
            f"  focal length   fx {matrix[0, 0]:8.1f}   fy {matrix[1, 1]:8.1f}",
            f"  principal pt   cx {matrix[0, 2]:8.1f}   cy {matrix[1, 2]:8.1f}",
            "  distortion     " + "  ".join(f"{v:+.4f}" for v in dist[:5]),
        ]
        if skipped:
            lines.append("")
            lines.append("  board not found in views: "
                         + ", ".join(str(i) for i in skipped))
        if rms > 0.5:
            lines += [
                "",
                "  rms above 0.5 px usually means the board was not moved "
                "enough between",
                "  shots rather than that the lens is bad. Add views with "
                "the board tilted",
                "  and pushed into the frame corners.",
            ]
        text = "\n".join(lines)
        return io.NodeOutput(updated, text, ui=ui.PreviewText(text))
