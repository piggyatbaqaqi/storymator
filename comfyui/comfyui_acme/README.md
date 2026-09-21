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

`requirements.txt` is needed only for lens calibration; the registration
nodes run on what ComfyUI already has.

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

A minimal graph:

```
LoadImage -> AcmeDetectSheet -> AcmeRegister -> PreviewImage
AcmeCalibration ---^      \-> AcmeRegistrationReport -> PreviewImage
```

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
migrated one module at a time; both are collected meanwhile. Migrating
the remaining six — `test_geometry`, `test_fit`, `test_register`,
`test_lens`, `test_charuco`, `test_detect` — is a rename plus a
`pytest.ini` edit when the last one moves, and is worth doing as its
own commit rather than mixed into feature work.

### Integration tests

Files named `*_integration_test.py` need **real hardware** and are
skipped unless `--integration` is passed. They are for late in
development, not for every run: they open the camera, so they fail if
ComfyUI or anything else is holding it.
