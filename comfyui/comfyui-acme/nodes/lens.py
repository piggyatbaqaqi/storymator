"""Lens calibration: the one thing worth storing between sessions."""

from __future__ import annotations

from dataclasses import replace

from comfy_api.latest import io, ui

from ..acme.lens import calibrate, calibrate_charuco, charuco_board
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
                io.Combo.Input(
                    "board_type", options=["charuco", "checkerboard"],
                    tooltip="Prefer ChArUco. Every corner carries an "
                            "identity, so a board pushed half out of "
                            "frame still counts -- and those are the "
                            "views that pin distortion down."),
                io.Int.Input("columns", default=7, min=3, max=40,
                             tooltip="ChArUco: squares across, as the "
                                     "board's own legend states it. "
                                     "Checkerboard: INNER corners, which "
                                     "is one less than the squares."),
                io.Int.Input("rows", default=9, min=3, max=40),
                io.Float.Input("square_mm", default=25.0, min=1.0,
                               max=200.0, step=0.01,
                               tooltip="Only affects the extrinsics: "
                                       "scaling the board scales the "
                                       "translations and leaves focal "
                                       "length, principal point and "
                                       "distortion untouched. A print "
                                       "that came out 7 % large still "
                                       "calibrates the lens correctly."),
                io.Float.Input("marker_mm", default=18.0, min=0.5,
                               max=200.0, step=0.01,
                               tooltip="ChArUco only."),
                io.String.Input("aruco_dictionary",
                                default="DICT_6X6_250",
                                tooltip="ChArUco only. Read it off the "
                                        "board's printed legend."),
            ],
            outputs=[AcmeCalibrationType.Output("calibration"),
                     io.String.Output("report")],
        )

    @classmethod
    def execute(cls, images, calibration, board_type, columns, rows,
                square_mm, marker_mm, aruco_dictionary) -> io.NodeOutput:
        frames = [to_gray(f) for f in batch_to_numpy(images)]
        try:
            if board_type == "charuco":
                board = charuco_board(columns, rows, square_mm,
                                      marker_mm, aruco_dictionary)
                matrix, dist, rms, used, skipped = calibrate_charuco(
                    frames, board)
            else:
                matrix, dist, rms, used, skipped = calibrate(
                    frames, columns, rows, square_mm)
        except (ValueError, RuntimeError) as exc:
            text = f"calibration failed: {exc}"
            return io.NodeOutput(calibration, text,
                                 ui=ui.PreviewText(text))

        updated = replace(calibration, camera_matrix=matrix,
                          dist_coeffs=dist)
        fx, fy = matrix[0, 0], matrix[1, 1]
        cx, cy = matrix[0, 2], matrix[1, 2]
        lines = [
            f"calibrated on {len(used)}/{len(frames)} views, "
            f"reprojection rms {rms:.3f} px",
            "",
            f"  focal length   fx {fx:8.1f}   fy {fy:8.1f}",
            f"  principal pt   cx {cx:8.1f}   cy {cy:8.1f}",
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
