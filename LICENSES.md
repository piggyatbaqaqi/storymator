# Licensing

storymator is **GPL-3.0-or-later**, except where a directory below says
otherwise. The full text is in [LICENSE](LICENSE).

| path | licence | notes |
|---|---|---|
| everything not listed below | **GPL-3.0-or-later** | source, build scripts, tooling |
| `comfyui/comfyui-acme/` | **GPL-3.0-or-later** | ComfyUI is itself GPL-3.0, so this matches its ecosystem |
| `docs/` | **CC-BY-SA-4.0** | prose — **except `docs/licensing/`, see below** |
| `docs/licensing/` | **their respective owners** | see that directory's README for per-file provenance |
| `data/calibration/acme_paper/` | **CC-BY-4.0** | our own measurements; declared in that dataset's card |
| `data/calibration/distortion/` — non-code | **CC-BY-SA-4.0** | frames, calibration JSON, cards |
| `data/calibration/targets/` | **CC-BY-SA-4.0** | ours under the CalibrX terms — **trademark note below** |
| `data/calibration/pegs/` — non-code | **CC-BY-SA-4.0** | caliper readings and analysis of our own bar |
| `data/**/*.py` | **GPL-3.0-or-later** | code is code wherever it sits; all carry SPDX headers |

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

`pegs/` is **CC-BY-SA-4.0** too, matching `distortion/` — the same
kind of thing, caliper readings and analysis of our own bar.

**Code is code wherever it sits.** Six Python files live inside data
directories and are **GPL-3.0-or-later** like the rest of the source.
All six carry an SPDX header naming both their own licence and the
licence of the directory around them, because that boundary is the one
place in this repository a reader could reasonably guess wrong:

| file | surrounding data |
|---|---|
| `acme_paper/acme_paper.py`, `acme_paper/src/*.py` | CC-BY-4.0 |
| `distortion/v4k_01/anisotropy_scan.py`, `make_calibration.py` | CC-BY-SA-4.0 |
| `pegs/honbay_0001/analyse.py` | CC-BY-SA-4.0 |

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

## `docs/` — CC-BY-SA-4.0, with one carve-out

Prose and diagrams are **CC-BY-SA-4.0**, matching the calibration data
they document.

**Documents under `docs/licensing/` belong to their respective owners**,
as documented in
[docs/licensing/README.md](docs/licensing/README.md) — which lists each
file with its owner, source URL, retrieval date and method. They are
dated copies of vendor material, kept as evidence of what was in force
when our files were generated. The grant above stops at that directory.

## Open with CalibrX — asked 2026-09-21, awaiting reply

Three questions are with `support@calibrx.io`. **The guidance above is
our cautious reading pending their answers, not their position.**

1. **Redistribution.** Whether the §4/§5 ownership grant is understood
   as permitting output to be released under an open licence — giving
   files to the public, rather than the team-scoped use the Commercial
   tier describes.
2. **Trademark.** Whether the `calibrx.io` mark on a generated board
   may stay on redistributed copies, and what they want on modified
   ones. Our current rule — strip it from modified boards, keep it on
   unmodified — is a conservative default chosen without their input,
   and their answer supersedes it either way.
3. **Anisotropic targets** *(a suggestion, not a question).* Their
   format carries one `square_size` and no second axis, so a print
   whose x and y scales differ cannot be described. Ours differs by
   **+0.15 %**, which their own fit pushes into fx/fy as a 0.104 %
   discrepancy — see
   [data/calibration/distortion/v4k_01/calibrx/README.md](data/calibration/distortion/v4k_01/calibrx/README.md).
   A second axis in the board spec would let their pipeline recover it.

If the answers move any of this, update **this file, the notice in
`data/calibration/targets/README.md`, and the tier notes in
`docs/licensing/README.md`** — the guidance is stated in all three.

## Decisions still to make

* **`-or-later` vs `-only`** — this file says `-or-later`, the FSF's
  own recommendation and the kinder option downstream. To make it
  `-only`, change the line above and say so in the source headers.
* **SPDX headers.** All six Python files inside data directories carry
  them, which is where the GPL/CC boundary needs marking. Elsewhere
  `LICENSE` plus this file is unambiguous; adding them repo-wide is
  tidiness, not a requirement.
