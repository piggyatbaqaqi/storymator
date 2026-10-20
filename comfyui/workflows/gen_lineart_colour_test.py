"""Regression suite for the lineart-colour workflow generator.

Six groups, ordered by what they protect.

**Builder** pins `node()` itself, including the defaults, because every
other test reads the table it fills in.

**UI graph** and **API prompt** check the two outputs separately. They
are different documents with different rules: the UI graph keeps
bypassed and canvas-only nodes, the API prompt drops them and splices
the bypass away. Confusing the two is the mistake this module exists to
avoid, so each is checked against its own contract.

**Agreement** is the group that matters most. The generator's whole
purpose is that one source produces two consistent files; a change that
quietly desynchronises them would otherwise show up as a workflow that
runs differently from the one on the canvas.

**Artefacts** compares the committed JSONs against a fresh generation.
It fails if someone hand-edits a JSON instead of the generator, which is
the documented way to break this.

**Installed ComfyUI** checks the graph against the node definitions
actually on this machine -- widget order, input names, link types. It is
skipped where ComfyUI is not importable, because it is the only group
that needs it. This is the group that would catch a ComfyUI upgrade
renaming an input out from under the workflow.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import pytest

from . import gen_lineart_colour as g

HERE = Path(__file__).resolve().parent
BYPASS = 4


# --------------------------------------------------------------------------
# Builder
# --------------------------------------------------------------------------

@pytest.fixture
def table() -> Iterator[Dict[int, Dict[str, Any]]]:
    """Lend `node()` the module global, then put the real table back.

    `N` is populated at import time and every other test reads it, so a
    test that calls `node()` has to leave it exactly as it found it.
    """
    saved = dict(g.N)
    g.N.clear()
    yield g.N
    g.N.clear()
    g.N.update(saved)


def test_node_records_every_field(table: Dict[int, Dict[str, Any]]) -> None:
    g.node(1, "KSampler", "t", [1, 2], [3, 4], ["w"],
           inputs=[("model", "MODEL", (9, 0))], outputs=[("LATENT", "LATENT")], mode=2)
    assert table[1] == {"type": "KSampler", "title": "t", "pos": [1, 2], "size": [3, 4],
                        "widgets": ["w"], "inputs": [("model", "MODEL", (9, 0))],
                        "outputs": [("LATENT", "LATENT")], "mode": 2}


def test_node_defaults_are_empty_and_enabled(table: Dict[int, Dict[str, Any]]) -> None:
    g.node(1, "PreviewImage", "t", [0, 0], [1, 1], [])
    assert table[1]["inputs"] == []
    assert table[1]["outputs"] == []
    assert table[1]["mode"] == 0


def test_node_copies_sequences_into_lists(table: Dict[int, Dict[str, Any]]) -> None:
    """Tuples are accepted but stored as lists, so later code can append."""
    g.node(1, "X", "t", [0, 0], [1, 1], [], inputs=(("a", "A", None),),
           outputs=(("B", "B"),))
    assert isinstance(table[1]["inputs"], list)
    assert isinstance(table[1]["outputs"], list)


# --------------------------------------------------------------------------
# UI graph
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ui() -> Dict[str, Any]:
    return g.build_ui()


@pytest.fixture(scope="module")
def api() -> Dict[str, Dict[str, Any]]:
    return g.build_api()


def test_ui_links_point_at_real_nodes_and_slots(ui: Dict[str, Any]) -> None:
    by_id = {n["id"]: n for n in ui["nodes"]}
    for link_id, src, sslot, dst, dslot, typ in ui["links"]:
        assert src in by_id, f"link {link_id} from missing node {src}"
        assert dst in by_id, f"link {link_id} to missing node {dst}"
        assert sslot < len(by_id[src]["outputs"]), f"link {link_id} bad source slot"
        assert dslot < len(by_id[dst]["inputs"]), f"link {link_id} bad target slot"


def test_ui_link_endpoints_agree_with_node_slots(ui: Dict[str, Any]) -> None:
    """Both ends of every link must name it, or the canvas draws a stray wire."""
    by_id = {n["id"]: n for n in ui["nodes"]}
    for link_id, src, sslot, dst, dslot, _typ in ui["links"]:
        assert link_id in (by_id[src]["outputs"][sslot]["links"] or [])
        assert by_id[dst]["inputs"][dslot]["link"] == link_id


def test_ui_has_no_dangling_link_references(ui: Dict[str, Any]) -> None:
    known = {link[0] for link in ui["links"]}
    for n in ui["nodes"]:
        for i in n["inputs"]:
            assert i["link"] is None or i["link"] in known
        for o in n["outputs"]:
            for link_id in o["links"] or []:
                assert link_id in known


def test_ui_link_types_match_the_source_output_type(ui: Dict[str, Any]) -> None:
    by_id = {n["id"]: n for n in ui["nodes"]}
    for _lid, src, sslot, _dst, _dslot, typ in ui["links"]:
        assert by_id[src]["outputs"][sslot]["type"] == typ


def test_ui_counters_match_the_contents(ui: Dict[str, Any]) -> None:
    assert ui["last_node_id"] == max(n["id"] for n in ui["nodes"])
    assert ui["last_link_id"] == len(ui["links"])


def test_ui_keeps_the_bypassed_and_canvas_only_nodes(ui: Dict[str, Any]) -> None:
    """The reason the UI graph is the richer artefact; see the planning note."""
    modes = {n["id"]: n["mode"] for n in ui["nodes"]}
    types = {n["type"] for n in ui["nodes"]}
    assert BYPASS in modes.values(), "the bypassed canny branch vanished"
    assert "MarkdownNote" in types, "the on-canvas instructions vanished"


def test_ui_marks_optional_inputs_with_the_hollow_shape(ui: Dict[str, Any]) -> None:
    for n in ui["nodes"]:
        for i in n["inputs"]:
            if i["name"] in g.OPTIONAL:
                assert i.get("shape") == 7, f"node {n['id']} {i['name']} not drawn optional"


def test_ui_flags_widget_driven_inputs(ui: Dict[str, Any]) -> None:
    """EmptyLatentImage takes width/height from a link, so they carry `widget`."""
    latent = next(n for n in ui["nodes"] if n["type"] == "EmptyLatentImage")
    driven = {i["name"] for i in latent["inputs"] if "widget" in i}
    assert driven == {"width", "height"}


# --------------------------------------------------------------------------
# API prompt
# --------------------------------------------------------------------------

def test_api_drops_canvas_only_and_bypassed_nodes(api: Dict[str, Dict[str, Any]]) -> None:
    assert all(v["class_type"] != "MarkdownNote" for v in api.values())
    bypassed = {str(nid) for nid, n in g.N.items() if n["mode"] == BYPASS}
    assert bypassed, "fixture assumption: something is bypassed"
    assert not (bypassed & set(api)), "a bypassed node reached the API prompt"


def test_api_splices_the_bypass_through_to_the_live_branch(
        api: Dict[str, Dict[str, Any]]) -> None:
    """KSampler is wired to the bypassed canny apply on canvas.

    Bypass means "pass my input through", so the submitted prompt must
    reach past it to the lineart apply, keeping the slot: positive from
    slot 0, negative from slot 1. Getting this wrong would silently drop
    the ControlNet, which is the whole workflow.
    """
    sampler = next(v for v in api.values() if v["class_type"] == "KSampler")
    lineart = next(k for k, v in api.items()
                   if v["class_type"] == "ControlNetApplyAdvanced")
    assert sampler["inputs"]["positive"] == [lineart, 0]
    assert sampler["inputs"]["negative"] == [lineart, 1]


def test_api_references_only_nodes_it_contains(api: Dict[str, Dict[str, Any]]) -> None:
    for nid, spec in api.items():
        for name, val in spec["inputs"].items():
            if isinstance(val, list):
                assert val[0] in api, f"node {nid}.{name} points at absent {val[0]}"


def test_api_keeps_only_what_an_output_needs(api: Dict[str, Dict[str, Any]]) -> None:
    """Every surviving node must be reachable from a SaveImage or PreviewImage."""
    sinks = [k for k, v in api.items()
             if v["class_type"] in {"SaveImage", "PreviewImage"}]
    seen: set[str] = set()
    stack = list(sinks)
    while stack:
        k = stack.pop()
        if k in seen:
            continue
        seen.add(k)
        stack += [v[0] for v in api[k]["inputs"].values() if isinstance(v, list)]
    assert seen == set(api)


def test_api_omits_the_ui_only_widget_slots(api: Dict[str, Dict[str, Any]]) -> None:
    """`control_after_generate` and LoadImage's upload button are canvas-only.

    They sit in widgets_values but are not node inputs, so emitting them
    would make ComfyUI reject the prompt.
    """
    sampler = next(v for v in api.values() if v["class_type"] == "KSampler")
    assert "control_after_generate" not in sampler["inputs"]
    load = next(v for v in api.values() if v["class_type"] == "LoadImage")
    assert set(load["inputs"]) == {"image"}


def test_api_maps_widget_values_onto_the_right_names(
        api: Dict[str, Dict[str, Any]]) -> None:
    """A shift in WIDGETS would put the seed in `steps` without any error."""
    sampler = next(v for v in api.values() if v["class_type"] == "KSampler")
    assert isinstance(sampler["inputs"]["seed"], int)
    assert isinstance(sampler["inputs"]["steps"], int)
    assert isinstance(sampler["inputs"]["cfg"], float)
    assert sampler["inputs"]["sampler_name"] == "dpmpp_2m"
    assert sampler["inputs"]["scheduler"] == "karras"


def test_api_names_the_models_the_workflow_depends_on(
        api: Dict[str, Dict[str, Any]]) -> None:
    ckpt = next(v for v in api.values() if v["class_type"] == "CheckpointLoaderSimple")
    assert ckpt["inputs"]["ckpt_name"] == g.CKPT
    loaders = [v["inputs"]["control_net_name"] for v in api.values()
               if v["class_type"] == "ControlNetLoader"]
    assert loaders == [g.CN_LINEART], "only the live lineart loader should survive"


# --------------------------------------------------------------------------
# Agreement between the two outputs
# --------------------------------------------------------------------------

def test_every_api_node_exists_in_the_ui_with_the_same_class(
        ui: Dict[str, Any], api: Dict[str, Dict[str, Any]]) -> None:
    ui_types = {str(n["id"]): n["type"] for n in ui["nodes"]}
    for nid, spec in api.items():
        assert nid in ui_types, f"API node {nid} is not on the canvas"
        assert ui_types[nid] == spec["class_type"]


def test_api_is_the_ui_with_bypass_resolved(
        ui: Dict[str, Any], api: Dict[str, Dict[str, Any]]) -> None:
    """Walk the canvas links, skipping bypassed nodes, and expect the API wiring.

    Computed from the UI document rather than from `N`, so the two
    outputs are compared against each other rather than both against the
    same intermediate.
    """
    by_id = {n["id"]: n for n in ui["nodes"]}
    src_of = {link[0]: (link[1], link[2]) for link in ui["links"]}

    def through(nid: int, slot: int) -> Tuple[int, int]:
        node = by_id[nid]
        if node["mode"] != BYPASS:
            return nid, slot
        typ = node["outputs"][slot]["type"]
        same = [i for i in node["inputs"] if i["type"] == typ and i["link"] is not None]
        chosen = same[slot] if len(same) > slot else same[0]
        return through(*src_of[chosen["link"]])

    for nid, spec in api.items():
        node = by_id[int(nid)]
        for i in node["inputs"]:
            if i["link"] is None:
                continue
            expected = list(map(str, through(*src_of[i["link"]])))
            expected[1] = int(expected[1])  # type: ignore[call-overload]
            assert spec["inputs"][i["name"]] == expected, f"{nid}.{i['name']}"


# --------------------------------------------------------------------------
# Committed artefacts
# --------------------------------------------------------------------------

def test_committed_json_matches_a_fresh_generation(tmp_path: Path) -> None:
    """Fails if a JSON was hand-edited instead of the generator."""
    ui_out, api_out = tmp_path / "ui.json", tmp_path / "api.json"
    g.main(["gen", str(ui_out), str(api_out)])
    for fresh, committed in ((ui_out, "lineart_colour_workflow.json"),
                             (api_out, "lineart_colour_api.json")):
        on_disk = HERE / committed
        assert on_disk.exists(), f"{committed} is missing from the repo"
        assert json.loads(fresh.read_text()) == json.loads(on_disk.read_text()), (
            f"{committed} is out of step with gen_lineart_colour.py -- "
            "regenerate it rather than editing it")


def test_main_writes_both_files_and_reports_success(tmp_path: Path) -> None:
    ui_out, api_out = tmp_path / "a.json", tmp_path / "b.json"
    assert g.main(["gen", str(ui_out), str(api_out)]) == 0
    assert json.loads(ui_out.read_text())["nodes"]
    assert json.loads(api_out.read_text())


def test_module_runs_as_a_script(tmp_path: Path) -> None:
    ui_out, api_out = tmp_path / "a.json", tmp_path / "b.json"
    proc = subprocess.run(
        [sys.executable, "-I", str(HERE / "gen_lineart_colour.py"),
         str(ui_out), str(api_out)],
        capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(api_out.read_text())


def test_the_example_drawing_is_present() -> None:
    """The smoke-test input the planning note points at."""
    assert (HERE / "examples" / "character_clean.png").exists()


# --------------------------------------------------------------------------
# Agreement with the installed ComfyUI
# --------------------------------------------------------------------------

def _comfy_defs() -> Optional[Dict[str, Any]]:
    """Node classes from a ComfyUI checkout, or None if there is not one."""
    import asyncio
    import os

    for root in ("/data/piggy/src/github.com/Comfy-Org/ComfyUI",
                 os.environ.get("COMFYUI_ROOT", "")):
        if root and Path(root, "nodes.py").exists():
            break
    else:
        return None
    cwd = os.getcwd()
    sys.path.insert(0, root)
    try:
        os.chdir(root)
        import nodes  # type: ignore[import-not-found]
        extra = nodes.init_extra_nodes(init_custom_nodes=False)
        if asyncio.iscoroutine(extra):
            asyncio.run(extra)
        return dict(nodes.NODE_CLASS_MAPPINGS)
    except Exception:
        return None
    finally:
        os.chdir(cwd)
        if root in sys.path:
            sys.path.remove(root)


@pytest.fixture(scope="module")
def comfy() -> Dict[str, Any]:
    defs = _comfy_defs()
    if defs is None:
        pytest.skip("no importable ComfyUI checkout")
    return defs


WIDGET_TYPES = {"INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"}

# Nodes the canvas draws but the backend has never heard of. They carry no
# class in NODE_CLASS_MAPPINGS, which is precisely why build_api drops them.
CANVAS_ONLY = {"Note", "MarkdownNote", "Reroute", "PrimitiveNode"}


def _widget_names(cls: Any) -> List[str]:
    """Input names the frontend renders as widgets, in declaration order.

    ComfyUI 0.35 reports a combo as the string "COMBO"; older versions
    hand back the list of options instead. Accept either, or this reads
    a dropdown as a link slot and the order silently shifts.
    """
    spec = cls.INPUT_TYPES()
    names = []
    for section in ("required", "optional"):
        for name, decl in (spec.get(section) or {}).items():
            typ = decl[0] if isinstance(decl, (list, tuple)) and decl else decl
            if isinstance(typ, list) or typ in WIDGET_TYPES:
                names.append(name)
    return names


def test_every_executable_class_exists_in_this_comfyui(comfy: Dict[str, Any]) -> None:
    used = {n["type"] for n in g.N.values()} - CANVAS_ONLY
    missing = sorted(used - set(comfy))
    assert not missing, f"not installed: {missing}"


def test_the_canvas_only_nodes_really_have_no_backend_class(
        comfy: Dict[str, Any]) -> None:
    """The reason build_api drops them, asserted rather than assumed.

    If ComfyUI ever grew a backend MarkdownNote this would fail, and the
    drop in build_api would want revisiting rather than keeping.
    """
    used = {n["type"] for n in g.N.values()} & CANVAS_ONLY
    assert used, "fixture assumption: the graph has a canvas-only node"
    assert not (used & set(comfy))


def test_widget_order_matches_the_node_definitions(comfy: Dict[str, Any]) -> None:
    """WIDGETS encodes positional order; a renamed or reordered input breaks it."""
    for cls_name, declared in g.WIDGETS.items():
        real = _widget_names(comfy[cls_name])
        named = [w for w in declared if w]
        assert named == [r for r in real if r in named], (
            f"{cls_name}: WIDGETS says {named}, ComfyUI says {real}")


def test_api_input_names_are_real_inputs(
        comfy: Dict[str, Any], api: Dict[str, Dict[str, Any]]) -> None:
    for nid, spec in api.items():
        decl = comfy[spec["class_type"]].INPUT_TYPES()
        valid = set(decl.get("required") or {}) | set(decl.get("optional") or {})
        unknown = set(spec["inputs"]) - valid
        assert not unknown, f"node {nid} ({spec['class_type']}) has unknown {unknown}"


def test_api_link_slots_exist_on_the_source_class(
        comfy: Dict[str, Any], api: Dict[str, Dict[str, Any]]) -> None:
    for nid, spec in api.items():
        for name, val in spec["inputs"].items():
            if isinstance(val, list):
                rets = comfy[api[val[0]]["class_type"]].RETURN_TYPES
                assert val[1] < len(rets), f"node {nid}.{name} slot {val[1]} out of range"
