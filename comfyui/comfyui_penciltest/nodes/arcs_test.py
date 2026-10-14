"""The adapter, checked for the things an adapter gets wrong.

Not the arithmetic -- that is ``penciltest/arcs_test.py``.  What is
checked here is the wiring: that the schema says what the graph needs,
that execute hands back the outputs in the declared order, and that the
node's defaults are the library's rather than a second copy that can
drift from it.
"""

from __future__ import annotations

from typing import List

import pytest

pytest.importorskip("comfy_api.latest",
                    reason="the node layer needs ComfyUI on the path")

from comfy_api.latest import io            # noqa: E402

from ..penciltest import arcs              # noqa: E402
from . import arcs as node                 # noqa: E402

A: arcs.Point = (0.0, 0.0)
B: arcs.Point = (10.0, 0.0)
GENTLE: arcs.Point = (5.0, 1.5)            # 146.601512
CORNER: arcs.Point = (5.0, 9.0)            # 58.109208
STRAIGHT: arcs.Point = (5.0, 0.0)          # 180.000000
ARC: List[arcs.Point] = [A, (3.0, 2.0), (7.0, 2.0), B]


def _schema() -> io.Schema:
    return node.PencilTestInteriorAngle.define_schema()


# --------------------------------------------------------------- schema

def test_the_node_id_is_prefixed_and_stable() -> None:
    """Saved workflows refer to this string, so it must never change."""
    assert _schema().node_id == "PencilTestInteriorAngle"


def test_the_category_does_not_name_this_project() -> None:
    """The pack is meant to leave; a storymator/ menu would not."""
    assert _schema().category == "penciltest/harness"
    assert "storymator" not in _schema().category


def test_the_inputs_are_what_the_graph_needs() -> None:
    assert [i.id for i in _schema().inputs] == [
        "path", "straight_degrees", "corner_degrees"]


def test_the_outputs_are_declared_in_the_order_execute_returns_them(
) -> None:
    assert [o.display_name for o in _schema().outputs] == [
        "report", "accepted", "worst_degrees"]


def test_the_defaults_are_the_librarys_not_a_second_copy() -> None:
    """Two sets of thresholds that could drift apart is how a graph
    starts disagreeing with the harness that was meant to judge it."""
    by_id = {i.id: i for i in _schema().inputs}
    assert by_id["straight_degrees"].default == arcs.DEFAULT_STRAIGHT_DEGREES
    assert by_id["corner_degrees"].default == arcs.DEFAULT_CORNER_DEGREES


def test_the_node_is_registered() -> None:
    """A node that is not in PHASE_1 does not exist as far as ComfyUI is
    concerned, however correct it is."""
    from . import PHASE_1
    assert node.PencilTestInteriorAngle in PHASE_1


# -------------------------------------------------------------- execute

def test_a_gentle_arc_is_accepted() -> None:
    out = node.PencilTestInteriorAngle.execute(ARC, 175.0, 90.0)
    report, accepted, worst = out.result
    assert accepted is True
    assert worst == pytest.approx(146.310, abs=1e-3)
    assert report.strip()


def test_a_straight_run_is_refused() -> None:
    out = node.PencilTestInteriorAngle.execute([A, STRAIGHT, B], 175.0, 90.0)
    _, accepted, worst = out.result
    assert accepted is False
    assert worst == pytest.approx(180.0)


def test_a_corner_is_refused() -> None:
    out = node.PencilTestInteriorAngle.execute([A, CORNER, B], 175.0, 90.0)
    _, accepted, _ = out.result
    assert accepted is False


def test_the_thresholds_reach_the_library() -> None:
    """Passing them through is the whole job of an adapter, and the
    obvious way to get it wrong is to ignore them."""
    path = [A, (5.0, 0.5), B]              # 168.578814
    _, lenient, _ = node.PencilTestInteriorAngle.execute(
        path, 179.0, 90.0).result
    _, strict, _ = node.PencilTestInteriorAngle.execute(
        path, 160.0, 90.0).result
    assert lenient is True
    assert strict is False


def test_worst_is_the_angle_furthest_from_acceptable() -> None:
    """With a straight run and a corner in one path, the report has to
    name something; the one nearest a threshold would be the least
    useful choice."""
    out = node.PencilTestInteriorAngle.execute(
        [A, GENTLE, CORNER, B], 175.0, 90.0)
    _, accepted, worst = out.result
    assert accepted is False
    assert worst == pytest.approx(
        min(arcs.interior_angles([A, GENTLE, CORNER, B])), abs=1e-3)


def test_a_bare_key_pair_is_accepted_with_nothing_to_say() -> None:
    """No inbetween is not a failure."""
    _, accepted, worst = node.PencilTestInteriorAngle.execute(
        [A, B], 175.0, 90.0).result
    assert accepted is True
    assert worst == pytest.approx(180.0)


def test_worst_degrees_names_the_failure_not_the_smallest_angle() -> None:
    """A path that runs nearly straight and then bends: the straight run
    fails and the bend passes, so the socket must carry the straight
    one."""
    path = [(0.0, 0.0), (5.0, 0.1), (9.0, 0.2), (10.0, 5.0)]
    _, accepted, worst = node.PencilTestInteriorAngle.execute(
        path, 175.0, 90.0).result
    assert accepted is False
    assert worst == pytest.approx(179.714, abs=1e-3)


def test_no_inside_reports_a_straight_segment() -> None:
    """A key pair with nothing between the keys does trace a straight
    line, so 180 is honest rather than a sentinel."""
    assert node.PencilTestInteriorAngle.NO_INSIDE_DEGREES == 180.0
