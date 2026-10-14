"""ComfyUI wrappers. The arithmetic lives in ``penciltest/``."""

from typing import List

from .arcs import PencilTestInteriorAngle

PHASE_1: List[type] = [
    PencilTestInteriorAngle,
]

__all__ = [c.__name__ for c in PHASE_1] + ["PHASE_1"]
