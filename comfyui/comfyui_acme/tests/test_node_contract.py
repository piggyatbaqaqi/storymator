"""What can be checked about the node layer without ComfyUI.

``comfy_api`` needs ``av``, which is not a dependency of this pack, so
node modules cannot be imported here and never have been tested.  That
is tolerable only because they are thin adapters -- but "thin" does not
mean "cannot contain a typo", and a name that does not exist in
``acme`` fails at ComfyUI load time, far from the edit that caused it.

Parsing rather than importing catches exactly that class of mistake,
costs nothing, and needs neither ComfyUI nor a camera.

It lives in ``tests/`` rather than beside the modules it checks
because a test file inside ``nodes/`` makes pytest import
``nodes/__init__.py``, which imports ``comfy_api``, which is the very
thing this file exists to work around.
"""

import ast
import importlib
import os
import pathlib

import pytest

NODES = pathlib.Path(__file__).resolve().parent.parent / "nodes"
MODULES = sorted(p for p in NODES.glob("*.py")
                 if not p.name.startswith("_")
                 and not p.name.endswith("_test.py"))


def _tree(path):
    return ast.parse(path.read_text())


@pytest.mark.parametrize("path", MODULES, ids=lambda p: p.name)
def test_names_imported_from_acme_actually_exist(path):
    """A typo here surfaces only when ComfyUI loads the pack."""
    missing = []
    for node in ast.walk(_tree(path)):
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        if "acme" not in node.module:
            continue
        module = importlib.import_module("acme." + node.module.split(".")[-1])
        missing += [f"{node.module}.{a.name}" for a in node.names
                    if not hasattr(module, a.name)]
    assert missing == []


@pytest.mark.parametrize("path", MODULES, ids=lambda p: p.name)
def test_every_node_defines_the_methods_comfyui_calls(path):
    """A class deriving io.ComfyNode owes ComfyUI two classmethods."""
    for node in ast.walk(_tree(path)):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = {ast.unparse(b) for b in node.bases}
        if "io.ComfyNode" not in bases:
            continue
        defined = {n.name for n in node.body
                   if isinstance(n, ast.FunctionDef)}
        assert {"define_schema", "execute"} <= defined, \
            f"{node.name} is missing {{'define_schema', 'execute'}} - defined"


@pytest.mark.parametrize("path", MODULES, ids=lambda p: p.name)
def test_io_types_used_exist_in_the_installed_comfyui(path):
    """Skipped unless ComfyUI is findable; it is not a dependency."""
    root = os.environ.get("COMFYUI_ROOT", "/data/piggy/src/github.com/"
                                          "Comfy-Org/ComfyUI")
    io_source = pathlib.Path(root) / "comfy_api" / "latest" / "_io.py"
    if not io_source.exists():
        pytest.skip(f"no ComfyUI at {root}; set COMFYUI_ROOT to check")
    text = io_source.read_text()
    used = {n.value.attr for n in ast.walk(_tree(path))
            if isinstance(n, ast.Attribute)
            and isinstance(n.value, ast.Attribute)
            and isinstance(n.value.value, ast.Name)
            and n.value.value.id == "io"}
    assert [u for u in sorted(used) if f"class {u}(" not in text] == []
