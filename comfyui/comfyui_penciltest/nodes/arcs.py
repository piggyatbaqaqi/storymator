"""The arcs check, as a ComfyUI node.

A thin adapter.  Everything with arithmetic in it lives in
:mod:`penciltest.arcs`, so the acceptance harness can call the same code
without standing up a graph -- and so this class stays short enough to
read.

The node takes a **path**, not drawings.  Whatever produces the path --
the centre of ink, a tracked hand, a tagged landmark -- is a separate
node and a separate argument, and this one does not care.  See section
11.2 of the planning note, where what gets tracked is still open.
"""

from __future__ import annotations

from comfy_api.latest import io, ui

from ..penciltest import arcs

PencilTestPathType = io.Custom("PENCILTEST_PATH")

CATEGORY = "penciltest/harness"


class PencilTestInteriorAngle(io.ComfyNode):
    """Arcs: is the inbetween on a curve, or on a line, or on a corner?

    The manuscript states the principle as a geometric predicate rather
    than a feeling -- *"no part of the move would be on a purely
    straight line"*, *"sharp angles must be avoided"* -- so this can
    measure it instead of discussing it.

    **It reports rather than filters.**  Every interior drawing comes
    back with its angle, passing ones included, because a harness that
    returns only failures cannot be told apart from one that is not
    running.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PencilTestInteriorAngle",
            display_name="Interior Angle (arcs)",
            category=CATEGORY,
            description="The angle at each inbetween, against the arcs "
                        "principle. 180 is a straight line.",
            inputs=[
                PencilTestPathType.Input(
                    "path",
                    tooltip="One tracked point per drawing, keys and "
                            "inbetweens alike, in order."),
                io.Float.Input(
                    "straight_degrees",
                    default=arcs.DEFAULT_STRAIGHT_DEGREES,
                    min=90.0, max=180.0, step=0.1,
                    tooltip="At or above this the path reads as a "
                            "straight line, which the principle "
                            "forbids. PROVISIONAL -- the studio sets "
                            "this; the manuscript names the failure "
                            "but not the number."),
                io.Float.Input(
                    "corner_degrees",
                    default=arcs.DEFAULT_CORNER_DEGREES,
                    min=0.0, max=180.0, step=0.1,
                    tooltip="At or below this the path turns a corner "
                            "rather than an arc. Also provisional."),
            ],
            outputs=[
                io.String.Output("report"),
                io.Boolean.Output("accepted"),
                io.Float.Output("worst_degrees"),
            ],
        )

    #: What ``worst_degrees`` reports when there is no inbetween at
    #: all.  180 rather than 0 or NaN because a key pair with nothing
    #: between the keys does trace a straight segment -- so the number
    #: is honest about the geometry, and it cannot be mistaken for a
    #: sharp corner by anything reading the socket.
    NO_INSIDE_DEGREES = 180.0

    @classmethod
    def execute(cls, path, straight_degrees,
                corner_degrees) -> io.NodeOutput:
        readings = arcs.read_path(path, straight_degrees, corner_degrees)
        text = arcs.report(readings)
        worst = arcs.worst_reading(readings)
        return io.NodeOutput(
            text,
            all(r.accepted for r in readings),
            cls.NO_INSIDE_DEGREES if worst is None else worst.degrees,
            ui=ui.PreviewText(text),
        )
