# Evaluating comfyui_webcamcapture as our camera input

*2026-09-21. Verdict: **borrow from it, do not fork it.** The concept
is right and roughly fifteen of its ninety lines are worth copying; the
rest is wrong for this rig in ways that are not patches.*

Upstream: `github.com/victorchall/comfyui_webcamcapture`, MIT,
© 2024 Victor C Hall.

## What it does right, and what we should take

It is a small, honest node: open `cv2.VideoCapture`, set some
properties, read a frame, convert to a ComfyUI tensor. Three things in
it are worth having and easy to get subtly wrong:

* **The IMAGE contract.** `cvtColor(BGR2RGB)` → `float32 / 255.0` →
  `torch.from_numpy(...).unsqueeze(0)`. Four lines, and the batch
  dimension and the divide are exactly the parts people get wrong.
* **`IS_CHANGED` returning something that always differs**, so ComfyUI
  re-executes rather than serving a cached frame. (Its `seed` widget is
  the 2023-era workaround for this; a changing return value is enough
  now.)
* **Holding the capture open across runs**, with a throwaway first
  frame. Re-opening a UVC device per execution is slow.

## Why we should not fork it

Every measurement below was taken against `v4k_01` on this machine, not
inferred.

### 1. It cannot reach our resolution

`width` is capped at 1920 and `height` at 1080 in the widget
definitions. We capture at **3264 × 2448**. A hard stop as written.

### 2. It never sets FOURCC, and that costs 8×

`cv2.VideoCapture` opens YUYV by default. The node sets width and
height and nothing else, and the driver *accepts* 3264 × 2448 in YUYV —
it just cannot move the data:

| | first frame | sustained |
|---|---:|---:|
| YUYV (what the node gets) | **4.53 s** | **1.3 fps** |
| MJPG (one extra `set`) | 0.58 s | 10.7 fps |

Forcing `CAP_PROP_FOURCC` to `MJPG` *before* setting the geometry is
one line and worth an order of magnitude.

### 3. No absolute focus — and this is the one that matters

The node exposes `autofocus` on/off and nothing more. There is a
commented-out `cap.set(cv2.CALIB_FIX_FOCAL_LENGTH, focus)` in the
source, which would not have worked: that is a calibration flag, not a
capture property.

`CAP_PROP_FOCUS` works fine on this camera —
`set(134)` → `get()` **134.0**, `set(635)` → **635.0** — the node just
does not expose it.

This is not a nice-to-have. **The v4k_01 calibration is valid at
`focus_absolute` 134 and nowhere else.** A capture node that cannot pin
focus produces frames whose intrinsics are silently wrong, which is
precisely the mistake already made once by hand on the peg profiles.

### 4. Two of its controls do not do what they claim

* **`brightness` as a 0–1 float is wrong.** Measured: `set(0.5)` →
  `get()` **0.0**. V4L2 brightness here is an integer scale, so the
  node silently pegs brightness to minimum at its own default.
* **`aperture` does nothing.** `set(1.8)` returns `False`, `get()`
  returns `-1`. Webcams have no aperture control.

### 5. It sets and hopes

`cap.set()` returns a bool that the node discards, and nothing is read
back. For V4L2 that is exactly backwards: properties fail silently and
routinely, as §4 shows.

**Our node needs set-then-verify**, and should check the frame size and
focus against the loaded calibration's `_provenance` block, refusing or
warning loudly on a mismatch. That is an architecture, not a patch —
and it is the whole reason the node is worth having.

### 6. Smaller things

* V1 node API (`INPUT_TYPES` / `RETURN_TYPES` / `FUNCTION`). Still
  supported in 0.35, but our pack is V3 throughout.
* `OUTPUT_NODE = True` on a pure image source, which marks it terminal.
* A bare `except:` around camera open.
* No release on teardown; it holds the device.

## Maintenance

"No changes in over a year" understates it. The last commits are
registry and licence chores from bots (`ComfyNodePRs`, `haohaocreates`);
the **capture code itself has not changed in about two years**. Nothing
is wrong with that for ninety stable lines — it is simply not a project
to track.

## Licence

**MIT**, which is one-way compatible with our GPL-3.0-or-later. We may
copy from it freely provided the copyright notice travels with anything
substantial. Copying four lines of tensor conversion is below that bar,
but an attributing comment costs nothing and is the right manners.

## Recommendation

Write **`AcmeCapture`** ourselves: V3 schema, in `comfyui-acme/nodes/`,
roughly 150 lines, with an attributing comment pointing here.

Widgets it needs that upstream does not have: device selection by
**`/dev/v4l/by-path`** rather than integer index (the V4K reports no
USB serial, so the port is the stable identity — see
`data/calibration/distortion/v4k_01/v4k_01.json`), FOURCC, absolute
focus, and a `verify_against` input taking an `ACME_CALIBRATION` so the
frame size and focus can be checked against what the intrinsics were
measured at.

Per `CLAUDE.md` this starts with `acme_capture_test.py` and a skeleton,
reviewed before implementation.

Keeping upstream's `IS_CHANGED` behaviour matters more here than it
does for them: a registration pass that silently re-uses a cached frame
would look like perfect repeatability.
