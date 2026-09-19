"""ACME registration: the arithmetic, with no ComfyUI in sight.

Importable and testable on its own, so the acceptance harness described
in docs/planning/inbetween-acceptance.md can call it directly rather
than standing up a graph.
"""

from .detect import (Blob, bimodal_threshold, find_peg_candidates,
                     find_sheet, sheet_corners)
from .fit import Pose, fit_pose, select_peg_triple
from .geometry import (apply_homography, homography_from_points,
                       rigid_from_points, rms)
from .model import (Calibration, FieldSpec, MM_PER_INCH, PegModel, SheetModel)
from .register import register_image
from .report import batch_report, frame_report

__all__ = [
    "Blob", "bimodal_threshold", "Calibration", "FieldSpec",
    "MM_PER_INCH", "PegModel", "Pose", "SheetModel", "apply_homography",
    "batch_report", "find_peg_candidates", "find_sheet", "fit_pose",
    "frame_report", "homography_from_points", "register_image",
    "rigid_from_points", "rms", "select_peg_triple", "sheet_corners",
]
