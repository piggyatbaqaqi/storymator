"""Phase 1 nodes: calibrate, detect, register, report.

Thin adapters.  Everything with arithmetic in it lives in :mod:`acme`,
so the acceptance harness can call the same code without standing up a
graph -- and so these classes stay short enough to read.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import numpy as np
from comfy_api.latest import io, ui

from ..acme.fit import Pose, fit_pose
from ..acme.model import Calibration, FieldSpec, PegModel, SheetModel
from ..acme.register import register_image
from ..acme.report import batch_report
from ._convert import (batch_to_numpy, draw_overlay, masks_to_tensor,
                       residual_chart, stack_to_tensor, to_gray)

AcmeCalibrationType = io.Custom("ACME_CALIBRATION")
AcmePoseType = io.Custom("ACME_POSE")

CATEGORY = "storymator/acme"

#: Marks on the greyscale diagnostic.  Fixed rather than verdict-
#: coloured, and red because a grey pixel has R == G == B, so anything
#: with R > G is unambiguously a mark.
DIAGNOSTIC_RED = (255, 64, 64)


class AcmeCalibration(io.ComfyNode):
    """Bar, sheet and raster geometry.

    Defaults are the standard ACME bar, confirmed against the operator's
    own 2026-09-17.  They are defaults and not constants: the bar in the
    room is the ground truth, and docs/measuring-punch-tolerance.md is
    the procedure for replacing them with measured values.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeCalibration",
            display_name="ACME Calibration",
            category=CATEGORY,
            description="Peg bar, sheet and output raster geometry.",
            inputs=[
                io.Combo.Input(
                    "bar_position", options=["below", "above"],
                    tooltip="Where the artist keeps the bar. Disney-style "
                            "is below. This decides which way up the "
                            "registered frame comes out; geometry alone "
                            "cannot tell, because the bar is symmetric."),
                io.Float.Input("px_per_mm", default=11.63, min=1.0,
                               max=100.0, step=0.01,
                               tooltip="Output raster resolution. 11.63 is "
                                       "4K across a 13 inch frame."),
                io.Float.Input("peg_spacing_mm", default=101.6, min=10.0,
                               max=500.0, step=0.01,
                               tooltip="Round peg to each rectangular peg. "
                                       "4 inches on a standard ACME bar."),
                io.Float.Input("round_peg_mm", default=6.35, min=1.0,
                               max=50.0, step=0.01),
                io.Float.Input("rect_peg_long_mm", default=12.7, min=1.0,
                               max=50.0, step=0.01),
                io.Float.Input("rect_peg_short_mm", default=3.175, min=0.5,
                               max=50.0, step=0.001),
                io.Float.Input("sheet_width_mm", default=266.7, min=10.0,
                               max=1000.0, step=0.1),
                io.Float.Input("sheet_height_mm", default=317.5, min=10.0,
                               max=1000.0, step=0.1),
                io.Float.Input("punch_offset_mm", default=12.0, min=0.0,
                               max=200.0, step=0.01,
                               tooltip="Punched edge to the peg line. This "
                                       "is offset_normal from the bench "
                                       "measurement."),
            ],
            outputs=[AcmeCalibrationType.Output("calibration")],
        )

    @classmethod
    def execute(cls, bar_position, px_per_mm, peg_spacing_mm, round_peg_mm,
                rect_peg_long_mm, rect_peg_short_mm, sheet_width_mm,
                sheet_height_mm, punch_offset_mm) -> io.NodeOutput:
        sheet = SheetModel(width_mm=sheet_width_mm,
                           height_mm=sheet_height_mm,
                           punch_offset_mm=punch_offset_mm,
                           bar_position=bar_position)
        calibration = Calibration(
            peg=PegModel(round_diameter_mm=round_peg_mm,
                         rect_long_mm=rect_peg_long_mm,
                         rect_short_mm=rect_peg_short_mm,
                         centre_spacing_mm=peg_spacing_mm),
            sheet=sheet,
            field_spec=FieldSpec.for_sheet(sheet, px_per_mm=px_per_mm))
        return io.NodeOutput(calibration)


class AcmeCalibrationSave(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeCalibrationSave",
            display_name="ACME Calibration Save",
            category=CATEGORY,
            inputs=[AcmeCalibrationType.Input("calibration"),
                    io.String.Input("path", default="acme_calibration.json")],
            outputs=[io.String.Output("path")],
        )

    @classmethod
    def execute(cls, calibration, path) -> io.NodeOutput:
        Path(path).write_text(json.dumps(calibration.to_dict(), indent=2))
        return io.NodeOutput(path, ui=ui.PreviewText(f"wrote {path}"))


class AcmeCalibrationLoad(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeCalibrationLoad",
            display_name="ACME Calibration Load",
            category=CATEGORY,
            inputs=[io.String.Input("path",
                                    default="acme_calibration.json")],
            outputs=[AcmeCalibrationType.Output("calibration")],
        )

    @classmethod
    def execute(cls, path) -> io.NodeOutput:
        data = json.loads(Path(path).read_text())
        return io.NodeOutput(Calibration.from_dict(data))


class AcmeDetectSheet(io.ComfyNode):
    """Fit each frame, and refuse the ones that do not fit.

    Refusal is data, never an exception: one bad frame in a batch of two
    hundred must not kill the run.  The reason reaches the operator four
    ways -- on the node, as a string, burned into the overlay, and as a
    flag inside the pose that downstream nodes can filter on.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeDetectSheet",
            display_name="ACME Detect Sheet",
            category=CATEGORY,
            description="Locate the sheet outline and the peg bar, and "
                        "solve the registration for each frame.",
            inputs=[
                io.Image.Input(
                    "image",
                    tooltip="The captured frames. AcmeRegister must be "
                            "given these SAME frames, not the overlay "
                            "this node emits."),
                AcmeCalibrationType.Input("calibration"),
                io.Float.Input("max_residual_px", default=1.5, min=0.1,
                               max=50.0, step=0.1,
                               tooltip="Reject a frame whose peg fit "
                                       "disagrees with the bar by more "
                                       "than this, in raster pixels."),
                io.Combo.Input("peg_appearance", options=["dark", "bright"],
                               tooltip="Whether the pegs or punch holes "
                                       "read darker or brighter than the "
                                       "paper. A rig property, not a "
                                       "tuning knob."),
            ],
            outputs=[
                AcmePoseType.Output("pose"),
                io.Image.Output(
                    "overlay",
                    tooltip="Diagnostic only: the frame with the fitted "
                            "outline, pegs and verdict drawn on it. Send "
                            "it to a preview. Do NOT feed it to "
                            "AcmeRegister -- the annotations would be "
                            "warped into the product."),
                io.String.Output("report"),
                io.Image.Output(
                    "gray",
                    tooltip="What the detector actually saw -- the Rec. "
                            "709 luminance it works on -- with the "
                            "located corners and pegs marked in red. "
                            "Every detection failure so far has lived "
                            "in this intermediate, invisible in both "
                            "the capture and the overlay."),
            ],
        )

    @classmethod
    def execute(cls, image, calibration, max_residual_px,
                peg_appearance) -> io.NodeOutput:
        frames = batch_to_numpy(image)
        poses: List[Pose] = []
        overlays = []
        diagnostics = []
        for frame in frames:
            gray = to_gray(frame)
            pose = fit_pose(gray, calibration,
                            max_residual_px=max_residual_px,
                            polarity=peg_appearance)
            poses.append(pose)
            overlays.append(draw_overlay(
                frame, pose.corners_image, pose.pegs_image,
                pose.summary(), pose.accepted))
            # No caption, and red regardless of the verdict: the
            # verdict is on the overlay and in the report, and this one
            # answers "what did it see and where did it look".
            marks = draw_overlay(gray, pose.corners_image, pose.pegs_image,
                                 "", pose.accepted, colour=DIAGNOSTIC_RED)
            # Composite the marks back over the ORIGINAL luminance
            # rather than shipping what PIL returned.  Drawing goes
            # through 8 bits, and a diagnostic whose grey is quantised
            # cannot be measured off -- which is half of what it is
            # for.  A mark is any pixel PIL left non-neutral.
            drawn = marks[..., 0] != marks[..., 1]
            plate = np.repeat(gray[:, :, None], 3, axis=2)
            diagnostics.append(np.where(drawn[:, :, None], marks, plate))

        text = batch_report(poses)
        return io.NodeOutput(poses, stack_to_tensor(overlays), text,
                             stack_to_tensor(diagnostics),
                             ui=ui.PreviewText(text))


class AcmeRegister(io.ComfyNode):
    """Resample onto the canonical raster. This is the product.

    A refused frame still occupies its slot in the batch, blank and with
    an all-false validity mask, so that pose *i* and image *i* stay the
    same frame no matter what happened upstream.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeRegister",
            display_name="ACME Register",
            category=CATEGORY,
            description="Warp each frame into ACME field coordinates.",
            inputs=[
                io.Image.Input(
                    "image",
                    tooltip="The ORIGINAL frames, from the same source "
                            "AcmeDetectSheet was given -- not its "
                            "overlay output. Both are IMAGE and both "
                            "have the right shape, so wiring the overlay "
                            "here works and silently bakes the drawn "
                            "annotations into the registered result."),
                AcmePoseType.Input("pose"),
                AcmeCalibrationType.Input("calibration"),
                io.Combo.Input("interpolation",
                               options=["bilinear", "bicubic", "nearest"]),
            ],
            outputs=[io.Image.Output("registered"),
                     io.Mask.Output("valid")],
        )

    @classmethod
    def execute(cls, image, pose, calibration,
                interpolation) -> io.NodeOutput:
        order = {"nearest": 0, "bilinear": 1, "bicubic": 3}[interpolation]
        spec = calibration.raster
        width, height = spec.size_px
        frames = batch_to_numpy(image)
        if len(pose) != len(frames):
            raise ValueError(
                f"{len(pose)} poses against {len(frames)} frames; they must "
                f"come from the same batch")

        out, valid = [], []
        for frame, p in zip(frames, pose):
            if not p.accepted:
                channels = frame.shape[2] if frame.ndim == 3 else 1
                out.append(np.zeros((height, width, channels)))
                valid.append(np.zeros((height, width), dtype=bool))
                continue
            registered, ok = register_image(frame, p.transform, spec,
                                            order=order)
            out.append(registered)
            valid.append(ok)
        return io.NodeOutput(stack_to_tensor(out), masks_to_tensor(valid))


class AcmeRegistrationReport(io.ComfyNode):
    """The milestone's success criterion, as a number and a picture."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeRegistrationReport",
            display_name="ACME Registration Report",
            category=CATEGORY,
            description="Residual distribution across a batch, and the "
                        "reason for every refusal.",
            inputs=[
                AcmePoseType.Input("pose"),
                io.Float.Input("threshold_px", default=1.5, min=0.1,
                               max=50.0, step=0.1),
            ],
            outputs=[io.String.Output("report"), io.Image.Output("chart")],
        )

    @classmethod
    def execute(cls, pose, threshold_px) -> io.NodeOutput:
        text = batch_report(pose)
        chart = residual_chart([p.peg_residual_px for p in pose],
                               [p.accepted for p in pose], threshold_px)
        return io.NodeOutput(text, stack_to_tensor([chart]),
                             ui=ui.PreviewText(text))


class AcmeFilterByResidual(io.ComfyNode):
    """Split a batch into the frames worth keeping and the rest."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="AcmeFilterByResidual",
            display_name="ACME Filter By Residual",
            category=CATEGORY,
            inputs=[io.Image.Input("image"), AcmePoseType.Input("pose")],
            outputs=[io.Image.Output("accepted"),
                     io.Image.Output("rejected"),
                     io.String.Output("report")],
        )

    @classmethod
    def execute(cls, image, pose) -> io.NodeOutput:
        frames = batch_to_numpy(image)
        good = [f for f, p in zip(frames, pose) if p.accepted]
        bad = [f for f, p in zip(frames, pose) if not p.accepted]
        # An empty batch is not a valid IMAGE, so fall back to a single
        # black frame rather than handing the graph something invalid.
        blank = [np.zeros_like(frames[0])] if frames else []
        text = (f"{len(good)} accepted, {len(bad)} rejected\n"
                + "\n".join(f"  frame {i}: {p.reason}"
                            for i, p in enumerate(pose) if not p.accepted))
        return io.NodeOutput(stack_to_tensor(good or blank),
                             stack_to_tensor(bad or blank), text,
                             ui=ui.PreviewText(text))
