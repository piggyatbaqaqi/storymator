"""Pencil tests for ComfyUI: cleanup, inbetweens, and the harness.

Rough drawings in, a readable pencil test out -- and a harness that can
say *which principle* a candidate inbetween violated rather than merely
that it looks wrong.

Design: ``docs/planning/inking-and-tween-plugins.md`` in the storymator
repository, which is this pack's canonical home.  Vocabulary:
``docs/glossary.md`` there.

**This pack knows nothing about any peg bar.**  It takes drawings that
are already registered and never asks how they got that way.  That is
not politeness -- it is what lets the pack be published on its own, and
``penciltest/hygiene.py`` makes it a test rather than an intention.

**It also imports cleanly without ComfyUI present**, for the same reason
``comfyui_acme`` does: ``penciltest/`` is meant to be testable and
callable on its own, and a package root that hard-fails on ``comfy_api``
makes the whole tree unimportable to pytest and the linters alike.
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

    class PencilTestExtension(ComfyExtension):
        @override
        async def get_node_list(self) -> list[type[io.ComfyNode]]:
            return list(PHASE_1)


async def comfy_entrypoint() -> "PencilTestExtension":
    """The pack's entry point, defined exactly once.

    Branching inside one definition rather than defining the name twice,
    one per import branch: two conditional definitions cannot have
    matching signatures, because the fallback branch has no
    ``PencilTestExtension`` to return, and mypy rejects that.
    """
    if _MISSING is not None:
        raise RuntimeError(
            "comfyui_penciltest needs to run inside ComfyUI 0.35 or "
            f"newer: {_MISSING}"
        )
    return PencilTestExtension()
