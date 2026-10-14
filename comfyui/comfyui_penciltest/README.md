# comfyui_penciltest

Pencil tests from drawings, for ComfyUI 0.35+ (V3 schema API): cleanup,
inbetweens, and a harness that can say *which principle* a candidate
inbetween violated rather than merely that it looks wrong.

**Canonical home: the [storymator](https://github.com/piggyatbaqaqi/storymator)
repository, under `comfyui/comfyui_penciltest/`.** Copies made elsewhere
for upstreaming are downstream of it.

Design and rationale: `docs/planning/inking-and-tween-plugins.md` there.
Vocabulary: `docs/glossary.md` there — the code uses those words and no
others, and `penciltest/hygiene.py` makes that a test.

## What it does not know about

**Any peg bar.** This pack takes drawings that are **already
registered** and never asks how they got that way. Registration against
ACME pegs is `comfyui_acme`'s job, in the same repository, and the
dependency runs one way only: the rig may know about pencil tests, pencil
tests never know they came off a peg bar.

That is enforced rather than intended — `penciltest/hygiene_test.py`
walks every module in this pack and fails if one imports the rig. The
pack is meant to be publishable on its own, and that property is lost
gradually and expensively if nobody is checking.

**ComfyUI, for the half that matters.** `penciltest/` is pure arithmetic
and imports neither ComfyUI nor torch, so it can be tested, called and
reviewed on its own. Only `nodes/` needs `comfy_api`. There is a test for
that too, run in a subprocess, because the claim is about what a fresh
interpreter loads.

## Layout

```
penciltest/   the arithmetic, and its tests, side by side as foo_test.py
nodes/        the ComfyUI wrappers; the only part that imports comfy_api
```

## Running the tests

From this directory, under the `storymator` conda environment:

```sh
python -m pytest           # the pack
flake8 .                   # PEP-8 at 79 columns, like the rest of the repo
cd .. && mypy comfyui_penciltest
```

mypy is configured one level up, in `comfyui/mypy.ini`, and must be run
from there — the reason is written out in that file.

## Install

```sh
ln -s /path/to/storymator/comfyui/comfyui_penciltest \
      /path/to/ComfyUI/custom_nodes/comfyui_penciltest
```

## Status

One node: **Interior Angle (arcs)**, under `penciltest/harness`. It takes
a `PENCILTEST_PATH` — one tracked point per drawing, keys and inbetweens
alike — and reports the angle at each inbetween against the arcs
principle.

**Nothing produces a `PENCILTEST_PATH` yet.** The producer is a feature
tracker, which is the next node; until then the check is callable from
Python and from the test suite but cannot be wired into a graph. Said
here so it reads as a known gap rather than a broken node.
