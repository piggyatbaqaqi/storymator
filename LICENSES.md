# Licensing

storymator is **GPL-3.0-or-later**, except where a directory below says
otherwise. The full text is in [LICENSE](LICENSE).

| path | licence | notes |
|---|---|---|
| everything not listed below | **GPL-3.0-or-later** | source, build scripts, tooling |
| `comfyui/comfyui-acme/` | **GPL-3.0-or-later** | ComfyUI is itself GPL-3.0, so this matches its ecosystem |
| `docs/` | **undecided** | prose, not source — see below |
| `data/calibration/acme_paper/` | **CC-BY-4.0** | our own measurements; declared in that dataset's card |
| `data/calibration/distortion/`, `data/calibration/pegs/` | **undecided** | our own measurements — see below |
| `data/calibration/targets/` | **THIRD PARTY, UNRESOLVED** | not ours to license — see below |

## Why GPL-3.0-or-later for the code

ComfyUI is GPL-3.0, and `comfyui-acme` is a ComfyUI custom node, so
copyleft is the natural fit rather than an imposition. The runtime
dependencies are all one-way compatible with it: OpenCV is Apache-2.0,
numpy, scipy and Pillow are BSD-family.

## Data

Measurement data is **not** covered by the GPL. Numbers describing a
piece of paper are a poor fit for a software licence, and downstream
users should be able to cite a peg diameter without inheriting
copyleft.

`acme_paper` is **CC-BY-4.0**, declared in its dataset card.

`distortion/` and `pegs/` are the same kind of thing — our own
photographs and caliper readings of our own equipment — and will
probably follow, but they are **not yet declared**. Some storymator
data is expected to go out under **CC-BY-SA-4.0** instead; which
licence applies to which dataset is decided per release.

> Note on `distortion/v4k_01/`: the calibration frames are photographs
> **of** the third-party target below. See the open question.

## `data/calibration/targets/` — not ours to license

`calibrx-charuco-175x225mm.svg` and `calibrx-charuco-175x125mm.svg`
came from **calibrx.io** (the mark printed on the boards; confirm the
spelling before purchasing — it is not "calibrix"). Each SVG carries
that mark and **no embedded copyright notice or licence text**. We have
not established terms for them.

Until that is resolved these files are **third-party assets under
unknown terms**. Nothing in this repository grants any right to them,
and they should be treated as not redistributable.

### The dependency is removable

A ChArUco board is a fully specified construction, not a creative work
we need from a vendor. `DICT_6X6_250` is defined in OpenCV, which is
Apache-2.0, and `cv2.aruco.CharucoBoard(...).generateImage()` produces
an equivalent board in a few lines. What calibrx.io supplies is
convenience — a tidy PDF with a legend and a printed scale bar.

So this is an engineering afternoon, not a negotiation, if that is the
preferred route:

1. Generate the board with OpenCV, into `targets/` as our own asset.
2. Print and measure it per `docs/calibrating-a-camera.md` — five
   squares corner to corner on the calipers, six readings.
3. It becomes `charuco_0002`; re-shoot the distortion set against it.
4. Delete the calibrx SVGs, and the question disappears.

Step 3 is the real cost, and the procedure for it is written down.

### What actually ships

Worth separating, because it narrows the exposure. Calibrating a camera
**with** a board is use, not redistribution. What a customer of a
calibrated camera receives is `v4k_01.json` — focal length, principal
point, distortion coefficients. Those are measurements of *the camera*,
and the board is the instrument that produced them, not a component of
them.

The redistribution question is therefore about the **board files in
this repository**, and secondarily about the **calibration photographs
that contain the board**.

### Open questions — for the operator, not for Claude

These need the vendor's actual terms and, for the second one, probably
a lawyer. They are recorded here rather than guessed at.

* **Which tier applies.** Selling calibrated cameras reads as
  commercial. Whether an R&D tier covers a DIY system that others build
  themselves depends entirely on how that tier is worded.
* **Are the calibration frames derivative?** `distortion-*.raw` are
  photographs of the printed board. If they are, the CC licence chosen
  for `distortion/` cannot be granted until the target question is
  settled. Regenerating the board (above) resolves this too, since a
  re-shot set contains only our own target.

## Decisions still to make

* **`docs/`** — prose under GPL is awkward. CC-BY-4.0 or CC-BY-SA-4.0
  is the usual choice.
* **`distortion/` and `pegs/`** — CC-BY-4.0, matching `acme_paper`, or
  CC-BY-SA-4.0.
* **`-or-later` vs `-only`** — this file says `-or-later`, the FSF's
  own recommendation and the kinder option downstream. To make it
  `-only`, change the line above and say so in the source headers.
* **SPDX headers.** There are none in the source yet. `LICENSE` plus
  this file is sufficient to be unambiguous; per-file
  `SPDX-License-Identifier:` lines are a tidiness improvement, not a
  requirement.
