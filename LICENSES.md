# Licensing

storymator is **GPL-3.0-or-later**, except where a directory below says
otherwise. The full text is in [LICENSE](LICENSE).

| path | licence | notes |
|---|---|---|
| everything not listed below | **GPL-3.0-or-later** | source, build scripts, tooling |
| `comfyui/comfyui-acme/` | **GPL-3.0-or-later** | ComfyUI is itself GPL-3.0, so this matches its ecosystem |
| `docs/` | **undecided** | prose, not source — see below |
| `data/calibration/acme_paper/` | **CC-BY-4.0** | our own measurements; declared in that dataset's card |
| `data/calibration/distortion/` — non-code | **CC-BY-SA-4.0** | frames, calibration JSON, cards |
| `data/calibration/distortion/**/*.py` | **GPL-3.0-or-later** | code is code wherever it sits |
| `data/calibration/targets/` | **CC-BY-SA-4.0** | ours under the CalibrX terms — **trademark note below** |
| `data/calibration/pegs/` | **undecided** | the only data directory still uncalled |

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

`distortion/` is **CC-BY-SA-4.0** — the frames, the calibration JSON
and the cards — as are the `targets/` they were shot against.
Share-alike rather than plain BY because a camera calibration is the
kind of thing that improves by being given back.

`pegs/` is **still undecided**. It is the obvious sibling of
`distortion/` and will probably follow it, but it has not been called.

**Code is code wherever it sits.** `anisotropy_scan.py` and
`make_calibration.py` live inside a CC-BY-SA-4.0 directory and are
**GPL-3.0-or-later** like the rest of the source. Both carry an SPDX
header saying so, which is the one place in this repository where the
boundary genuinely needs marking.

Mixing the two CC licences across directories is fine, and the
compatibility runs one way: CC-BY-4.0 material (`acme_paper`) may be
incorporated into a CC-BY-SA-4.0 work, not the reverse.

## `data/calibration/targets/` — ours, under the CalibrX terms

Both SVGs were generated with **CalibrX** under a lifetime commercial
licence. The terms grant ownership of generated output explicitly, in
two places:

> **§4** "You retain ownership of images, metadata, calibration
> projects, exported files, and other content that you upload or
> generate through CalibrX."
>
> **§5** "CalibrX, including its software, user interface, design,
> branding, documentation, and SDK, is owned by CalibrX… These Terms do
> not transfer any ownership of **the platform** to you. **You keep
> ownership of your own uploaded content and calibration outputs**, as
> described in Section 4."

The split is deliberate: the platform is theirs, the output is ours —
§5 reserves their side and then points back to §4 for ours. These
files are therefore released **CC-BY-SA-4.0** with the rest of the
calibration data.

The licence held is the **Commercial** tier — $149 lifetime, published
as *"Products for sale"* and *"Full rights, usable across your team."*
That is the correct tier: the cheaper **R&D** tier is published as
*"Not for calibrating products you sell"*, which rules out selling
calibrated cameras explicitly.

Dated copies of both the terms and the pricing page are kept in
[docs/licensing/](docs/licensing/), because vendor pages change and
what governs is the version in force when the files were generated.
§3 defers specifics to what is shown at checkout, so the plan page is
part of the record, not a footnote to it.

### Trademark — calibrx.io

**"calibrx.io" is a trademark of CalibrX and is not licensed here.**
§5 reserves their branding, and owning a file is not owning a mark on
it. Creative Commons licences do not grant trademark rights in any
case — CC-BY-SA-4.0 §2(b)(2): *"Patent and trademark rights are not
licensed under this Public License"* — so the mark travels outside the
grant rather than conflicting with it.

The printed legend on each board carries that mark. Anyone
redistributing a **modified** board under the share-alike terms should
**remove the calibrx.io mark**, so a changed target cannot imply
endorsement CalibrX never gave. Unmodified copies may keep it; it is
accurate there.

### The dependency remains removable

No longer a licensing need, but worth keeping on the record. A ChArUco
board is a fully specified construction: `DICT_6X6_250` lives in
Apache-2.0 OpenCV and `CharucoBoard.generateImage()` produces an
equivalent. Regenerating would cost a reprint, a re-measure per
`docs/calibrating-a-camera.md`, and a re-shoot of the distortion set —
and would retire the trademark question entirely. A choice now, not a
necessity.

### Calibration frames are settled too

`distortion-*.jpg` are photographs of the board. The derivative-work
question that used to sit here is moot: the board is ours under §4, so
photographs of it carry no third-party interest.

### The SDK output

`data/calibration/distortion/v4k_01/calibrx/` holds a calibration
produced by the calibrx SDK from our frames. The numbers are
measurements of *our* camera and a tool does not acquire rights in its
output — but the file carries a server-side `calibration_id`, so check
the SDK's terms before redistributing it alongside the rest.

## Decisions still to make

* **`docs/`** — prose under GPL is awkward. CC-BY-4.0 or CC-BY-SA-4.0
  is the usual choice.
* **`pegs/`** — CC-BY-SA-4.0 to match `distortion/`, or CC-BY-4.0 to
  match `acme_paper`. The only data directory still uncalled.
* **`-or-later` vs `-only`** — this file says `-or-later`, the FSF's
  own recommendation and the kinder option downstream. To make it
  `-only`, change the line above and say so in the source headers.
* **SPDX headers.** Only the two scripts under `distortion/` carry
  them, where the GPL/CC boundary needs marking. Elsewhere `LICENSE`
  plus this file is unambiguous; adding them repo-wide is tidiness, not
  a requirement.
