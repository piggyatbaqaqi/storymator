"""ACME registration for ComfyUI.

Camera capture of drawings on an ACME peg bar, resampled onto one
canonical raster so successive drawings can be compared.

Design: docs/planning/acme-registration-plugin.md in the storymator
repository.  The arithmetic lives in ``acme/`` and imports neither
ComfyUI nor torch, so it can be tested and reused on its own.

**This module imports cleanly without ComfyUI present.**  That is not
incidental: ``acme/`` is meant to be testable and callable on its own,
and a package root that hard-fails on ``comfy_api`` makes the whole
tree unimportable to pytest, linters and the acceptance harness alike.
Outside ComfyUI the extension simply is not defined, and asking for it
says so.
"""

from typing import Optional

try:
    from comfy_api.latest import ComfyExtension, io
except ModuleNotFoundError as exc:      # pragma: no cover - env dependent
    _MISSING: Optional[ModuleNotFoundError] = exc
else:
    _MISSING = None

    from typing_extensions import override

    from .nodes import PHASE_1

    class AcmeExtension(ComfyExtension):
        @override
        async def get_node_list(self) -> list[type[io.ComfyNode]]:
            return list(PHASE_1)


async def comfy_entrypoint() -> "AcmeExtension":
    """The pack's entry point, defined exactly once.

    Two conditional definitions of the same name -- one per import
    branch -- is what mypy rejects: their signatures cannot match,
    because the fallback branch has no ``AcmeExtension`` to return.
    Branching on a flag inside a single definition keeps the guard
    behaviour and gives the checker one signature to look at.
    """
    if _MISSING is not None:
        raise RuntimeError(
            "comfyui_acme needs to run inside ComfyUI 0.35 or newer: "
            f"{_MISSING}"
        )
    return AcmeExtension()
