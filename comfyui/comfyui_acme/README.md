# comfyui_acme

Registration of hand-drawn animation captured on an ACME peg bar, for
ComfyUI 0.35+ (V3 schema API).

Every drawing lands on **one canonical raster in ACME field
coordinates**, so frame *n* and frame *n+1* can be differenced,
onion-skinned or measured with no further alignment — and frames that
cannot be trusted are refused, with a reason, instead of being silently
mis-registered.

Design and rationale: `docs/planning/acme-registration-plugin.md` in the
storymator repository. Bench procedure for the geometry constants:
`docs/measuring-punch-tolerance.md`.

## Install

```sh
ln -s /path/to/storymator/comfyui/comfyui_acme \
      /path/to/ComfyUI/custom_nodes/comfyui_acme
```

Then **restart ComfyUI** — custom nodes are loaded once at startup.

`requirements.txt` is needed only for lens calibration; the
registration nodes run on what ComfyUI already has. Install it into the
environment ComfyUI itself runs in, not whatever the shell defaults to.

### Checking it loaded

A custom node that fails to import is reported once in ComfyUI's
console and then simply is not there, which looks identical to having
forgotten the symlink. Loading it the same way ComfyUI does says so
directly:

```sh
cd /path/to/ComfyUI
python - <<'EOF'
import asyncio, importlib.util, pathlib, sys
sys.path.insert(0, str(pathlib.Path.cwd()))
path = pathlib.Path("custom_nodes/comfyui_acme/__init__.py")
spec = importlib.util.spec_from_file_location(
    "comfyui_acme", path, submodule_search_locations=[str(path.parent)])
mod = importlib.util.module_from_spec(spec)
sys.modules["comfyui_acme"] = mod
spec.loader.exec_module(mod)
ext = asyncio.run(mod.comfy_entrypoint())
for n in asyncio.run(ext.get_node_list()):
    print(n.define_schema().node_id)
EOF
```

Nine node ids means the pack is sound and any remaining problem is in
ComfyUI's own discovery. The `submodule_search_locations` argument is
not optional: the pack uses relative imports, so it has to be loaded as
a package rather than a lone module.

## Nodes

| node | does |
|---|---|
| `AcmeCapture` | a frame from the rig, checked against the calibration it will be interpreted with |
| `AcmeCalibrateLens` | camera intrinsics from several board views |
| `AcmeCalibration` | bar, sheet and raster geometry, with measured values replacing the nominal ones |
| `AcmeCalibrationSave` / `Load` | JSON, so a rig's geometry outlives a workflow |
| `AcmeDetectSheet` | fit each frame; emit a pose, an overlay, and a verdict |
| `AcmeRegister` | resample onto the canonical raster — the product |
| `AcmeRegistrationReport` | residual distribution and every refusal reason |
| `AcmeFilterByResidual` | split a batch into trusted and not |

A minimal graph. **The image fans out; it does not flow through
AcmeDetectSheet**, whose image output is a diagnostic overlay:

```
                     ┌──────────────> AcmeDetectSheet ─ overlay ─> Preview
                     │                      │  report ──────────> Preview
   AcmeCapture ── image                     └─ pose ─┐
    (or LoadImage)   │                               │
                     └──────────────> AcmeRegister <─┘ ─ registered -> Preview
                                            ^
   AcmeCalibrationLoad ─ calibration ───────┴──> (and to the other two)

   AcmeDetectSheet.pose ──> AcmeRegistrationReport ──> Preview
```

**`AcmeRegister.image` takes the same frames `AcmeDetectSheet` was
given, never its `overlay` output.** Both are `IMAGE` and both have the
right shape, so wiring the overlay there works and silently warps the
drawn outline, peg markers and verdict text into the product. Nothing
downstream notices.

Capturing live instead of loading files:

```
AcmeCalibrationLoad -> AcmeCapture -> AcmeDetectSheet -> AcmeRegister
                   \--------------------^
```

`AcmeCapture` takes the calibration to **check against**, not to
capture with. Intrinsics belong to a camera at one focus — v4k_01's
are valid at `focus_absolute` 134 and nowhere else — so a frame shot at
any other focus carries a lens model that does not describe it, and
nothing in the picture says so. The node would rather stop than pass
one downstream; `on_mismatch` can be set to `warn` if you know better.

## How the fit works

**The sheet outline gives the homography; the pegs give the datum.**

Three collinear points cannot determine a homography — they fix a
projective frame on their own line and leave a three-parameter family
open — and the ACME pegs are collinear by design. So perspective comes
from the four paper corners, which are four points in general position.
The pegs then apply a small in-plane **rigid** correction, because the
pegs are what the drawing is actually aligned to and punch tolerance is
real. Scale is deliberately not free in that second step: letting it
float would let detection error quietly shrink the drawing.

The leftover disagreement between the observed peg triangle and the
known bar is `residual_px`, and it is why the plugin can refuse.

Nothing is calibrated that can be knocked: pose is solved per frame, so
moving the camera between captures — or mid-session — is a supported
operating mode rather than a failure to survive.

## Testing

The arithmetic imports neither ComfyUI nor torch:

```sh
cd comfyui/comfyui_acme
pytest -q                 # unit tests
pytest -q --integration   # and the rig
```

**Run these under the environment ComfyUI runs in.** The pack's own
arithmetic needs only numpy and scipy, but `tests/test_nodes.py`
imports the node classes for real, which needs `comfy_api` and so
everything ComfyUI depends on. Those tests *skip* elsewhere rather than
failing, which is convenient and also a trap: a green run in the wrong
environment is quietly nine tests lighter. Check the skip count.

`COMFYUI_ROOT` points at the ComfyUI checkout if it is not at the
default path.

From the repository root, name the pack explicitly instead:

```sh
pytest comfyui/comfyui_acme -q --integration
```

**`--integration` is registered by this pack's `conftest.py`, so pytest
has to reach it.** It does when the pack is the working directory or is
named on the command line, and not otherwise — `pytest --integration`
from the repository root fails, as does naming a path that does not
exist from where you are standing.

The error in both cases is `unrecognized arguments: --integration`,
because pytest parses options before it validates paths. It is
reporting the second problem, not the first: **check the path before
you believe the flag is broken.**

Synthetic captures with exact ground truth cover rotation to ±25°,
keystone, sensor noise, camera moves, and each refusal path.

### Layout

Unit tests live **beside the module they exercise**, as
`acme/foo_test.py`. `tests/test_*.py` is the older layout and is being
migrated one module at a time; both are collected meanwhile.

Five remain in the old layout: `test_geometry`, `test_register`,
`test_lens`, `test_charuco`, and `test_fit` — which is **currently
split**, with orientation tests in `acme/fit_test.py` and the rest in
`tests/test_fit.py`. Consolidating that one is worth doing first;
each of the others is a rename, plus a `pytest.ini` edit when the last
moves. Worth doing as its own commit rather than mixed into feature
work.

`tests/test_node_contract.py` and `tests/test_nodes.py` stay where they
are: they are cross-cutting rather than one module's unit tests, and
the first one *must* live outside `nodes/` — a test file inside it
makes pytest import `nodes/__init__.py`, which needs ComfyUI.

`acme/detect.py` has **no tests**, which is the largest gap in the
pack: it is where every real-world failure so far has actually lived.

### Integration tests

Files named `*_integration_test.py` need **real hardware** and are
skipped unless `--integration` is passed. They are for late in
development, not for every run: they open the camera, so they fail if
ComfyUI or anything else is holding it.
