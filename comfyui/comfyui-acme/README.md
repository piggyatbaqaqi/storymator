# comfyui-acme

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
ln -s /path/to/storymator/comfyui/comfyui-acme \
      /path/to/ComfyUI/custom_nodes/comfyui-acme
```

`requirements.txt` is needed only for lens calibration; the registration
nodes run on what ComfyUI already has.

## Nodes

| node | does |
|---|---|
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
python -m pytest comfyui/comfyui-acme/tests -q
```

Synthetic captures with exact ground truth cover rotation to ±25°,
keystone, sensor noise, camera moves, and each refusal path.
