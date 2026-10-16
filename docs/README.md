# storymator docs

## Source documents

### AI-Enabled Traditional Animation Desk — coarse scoping

Dr. Daniel Boulos & La Monte H.P. Yarroll, 31 August 2026.
<https://docs.google.com/document/d/1euWFELh5MPpwjIGTy_AisQGwO_oyXCzBZKsgQI00xxM/edit>

**The governing document.** Everything in this repository is a
subproject of it. Read it before scoping anything here.

Thesis: *"the first system that just lets a 2D animator just
animate — artist becomes the studio,"* with the software meeting the
artist rather than the artist meeting the software.

It scopes a **physical desk**, not only software:

* **Hardware** — touch video-backed ACME disc; tilting ACME work
  surface; motorized disc (traditionally backed by a frosted light);
  under-glass display; live motion-loop screen; production-information
  screen; **integrated camera array**, angled so the artist's hand does
  not obscure the drawing; task light; disc controls; ACME peg bar;
  audio I/O; a dedicated exposure-sheet touchscreen (Corsair Xeneon
  Edge 14.5").
* **Software** — data ingestion (camera input, controls); voice control
  and voice feedback; rough sketch to fully extrapolated and coloured;
  **inbetweening**; cleanup, paint and compositing.
* **Audio** — record self acting, describe the voice to ElevenLabs,
  convert the take into a performance by that voice.
* **Timing vocabulary** — 1 ft = 16 frames (35 mm); first pass is
  thumbnails numbered by frame at 24 fps within a 5–10 second shot,
  mostly keys.

User stories that bear directly on work in this repo:

* *"Artist draws two successive poses on paper. AI automatically
  inbetweens a **pencil test**."*
* *"Interpret timing information from thumbnails."*
* *"Extract an image from a movie that includes obscurations (hands)."*
* *"Exposure sheet visually maps every layer of animation against the
  timeline. Can encode cycles."*
* *"Make an on-the-fly voice script edit which is rendered into the
  pencil test."*

### Boulos, *The Animator's Toolbox* — unfinished manuscript, c. 2015

Supplied 2026-09-10 as the authority for what makes an inbetween
unusable. Three files, same Drive folder as the coarse scoping:

| file | what it is |
|---|---|
| `WorkingDic7_AnmCOmpEss.pdf` | the compiled manuscript — the most complete of the three, ~117 000 characters |
| `the7principles_ThisOne_June2015.docx` | earlier draft with the full 14-chapter book structure |
| `THeANimatorsToolbox_Chapter 3.docx` | Reversal of Curves / Successive Breaking of Joints, standalone |

**The seven principles are the project's local rule set**, distilled by
Daniel over twenty years of teaching from Fred Moore's fourteen points
as passed through Thomas and Johnston's *The Illusion of Life* — reduced
to those observable as motion in nature, which is why it is seven and
not fourteen. They are enumerated, with the manuscript's vocabulary, in
the appendix to
[planning/inbetween-acceptance.md](planning/inbetween-acceptance.md).

Two attributions the manuscript is careful about and so should we be:
**Reversal of Curves** reached Daniel from Glen Keane, who had it from
Ollie Johnston; **Successive Breaking of Joints** from Richard Williams,
who credited Art Babbit.

## Dependencies, and where they are declared

Three tiers, kept apart on purpose:

| tier | file | why there |
|---|---|---|
| **node-pack runtime** | `comfyui/<pack>/requirements.txt` | the ComfyUI Manager installs it into every user's ComfyUI, so it carries what the pack needs to run and nothing else |
| **`bin/` runtime** | [`requirements.txt`](../requirements.txt) | numpy, scipy, Pillow, OpenCV — what the command-line tools import |
| **repository tooling** | [`requirements-dev.txt`](../requirements-dev.txt) | pytest, mypy, flake8, bibtexparser, and torch — installed by whoever works on the repo, by nobody else |
| **the environment** | [`environment.yml`](../environment.yml) | composes the two requirements files onto `python=3.14`, reproducing how the `storymator` env was actually built |

**torch is tooling here, not runtime.** `comfyui_acme/nodes/_convert.py`
imports it, but inside ComfyUI it is already present — which is why the
pack's own `requirements.txt` does not name it, exactly as it does not
name numpy. It is in `requirements-dev.txt` because running
`comfyui_acme/tests/test_nodes.py` *outside* ComfyUI needs it in the
interpreter, and without it those 32 tests **skip rather than fail**.

**There is no top-level `pyproject.toml` and should not be one.** This
repository is a workspace of independently installable components —
`big_green_button/` and `comfyui_acme/` each carry their own
`pytest.ini` — rather than a single distribution. A top-level
`pyproject.toml` would assert otherwise. When a pack is published to the
Comfy registry it gets its **own** `pyproject.toml`, because that is
where the registry reads `[tool.comfy] PublisherId` and
`[project] name`/`version` from. That matters most for
`comfyui_penciltest`, which is meant to leave
([planning/inking-and-tween-plugins.md](planning/inking-and-tween-plugins.md)
§14).

### Three gaps, recorded rather than fixed

* ~~flake8 and mypy have no configuration file.~~ **Closed
  2026-10-14.** [`.flake8`](../.flake8) sets **100 columns** and covers
  the whole repository — flake8 walks up, so one file serves a run from
  the root and from inside a pack alike. mypy needs **two** configs,
  because the packs need a different base directory:
  [`mypy.ini`](../mypy.ini) at the root for `big_green_button/`, `bin/`
  and `data/`, and [`comfyui/mypy.ini`](../comfyui/mypy.ini) run from
  `comfyui/` for the packs. Each file says why.

### What is still red, and deliberately visible

`mypy big_green_button bin data` reports **24 errors in three files**,
all under `data/calibration/`. Unlike the 21 in `comfyui_acme`, these
are not one mechanical class — they are numpy typing: `operator`,
`index`, `slice`, `dtype`, `call-overload`. Real work rather than a
sed, so they were not done as a side effect of adding a config, and
they are left reporting rather than silenced per-file: a count on every
run is harder to forget than a comment.

`.flake8` instead waives per file, naming each code, for six one-shot
analysis scripts that are dense on purpose. Anything not named still
fires there, so a genuine bug in one of them is still caught.
* ~~The `storymator` conda environment is undocumented.~~ **Closed
  2026-10-14** by [`environment.yml`](../environment.yml). One thing it
  cannot supply: `comfy_api` is not a package but a ComfyUI checkout on
  `sys.path`, from `$COMFYUI_ROOT`. Without it, 32 node tests skip
  silently, so a complete setup is the environment **and** a checkout.
* ~~The `bin/` CLIs' runtime dependencies are undeclared.~~ **Closed
  2026-10-14** by [`requirements.txt`](../requirements.txt).

## Glossary

[glossary.md](glossary.md) — the project's vocabulary, in one place so
the code can cite it. The rule is the acceptance note's: **use these
words and no others.** Every entry names its source, because a term
Daniel's manuscript fixes binds this project in a way a general industry
usage does not, and a convention this repository invented binds nobody
but us. §5 lists the words we deliberately do not use.

## Bibliography

[bibliography.bib](bibliography.bib) — BibTeX for everything this
project cites: the two governing documents, the animation-craft lineage
the seven principles come through, and the models assessed in
[planning/inking-and-tween-plugins.md](planning/inking-and-tween-plugins.md).
Every entry was checked against the publisher's or arXiv's own listing;
where a venue comes from the authors' repository rather than the
listing, a `note` field says so. **A citation is not a licence** — see
[LICENSES.md](../LICENSES.md).

## Bench procedures

* [calibrating-a-camera.md](calibrating-a-camera.md) — lens calibration
  end to end for a new camera, written from the first one we did. The
  validation half matters most: two of our three failures were
  invisible in the reprojection error. Ends with a specification for
  the coverage tool that would have caught them.
* [measuring-punch-tolerance.md](measuring-punch-tolerance.md) — how to
  measure ACME punch geometry and peg/hole clearance, with a flatbed and
  a stage micrometer. Produces the three numbers the registration design
  currently assumes. An afternoon's work.

## Ideas, not yet plans

* [ideas/realtime-ui-construction.md](ideas/realtime-ui-construction.md)
  — Daniel, 2026-10-16. A two-speed architecture: instant low-fidelity
  proxy inbetweens for judging timing, slow high-fidelity synthesis
  replacing them behind the animator. Grounded in the 1990s digital
  animation stands.
* [ideas/realtime-ui-construction-response.md](ideas/realtime-ui-construction-response.md)
  — assessment. It maps: the control surface is the exposure sheet we
  already have a schema for. The risk is not latency but the proxy and
  the final disagreeing about spacing, which would make the animator's
  approval meaningless.

## Working notes in this repository

* [planning/inbetween-acceptance.md](planning/inbetween-acceptance.md) —
  **current.** What makes an inbetween unusable, and which of the seven
  principles a machine can check. Written against Daniel's 2026-09-10
  reply and the manuscript.
* [planning/inbetweening-scope.md](planning/inbetweening-scope.md) —
  scoping the automatic-inbetweening subproject. **Superseded in part:**
  its A/B fork mistakenly bundled fidelity target with representation.
  Daniel's answer is B's fidelity on A's substrate — pixels, not
  vectors. See §1 of the acceptance note.
* [planning/rife-poc.md](planning/rife-poc.md) — **current.** Design
  for the RIFE proof of concept. Five questions ordered by which would
  kill the idea soonest, a gap sweep that tests §7c's claim that the
  joint-onset objection scales with gap width, and measurement chosen
  in light of MAE having misled twice.
* [planning/pencil-test-architecture.md](planning/pencil-test-architecture.md)
  — **current.** The pencil test's deliverable is an *approved timing
  chart*, not drawings, so the generator is a swappable instrument and
  the harness splits: spacing for the proxy, the principles for final
  synthesis. Arbitrary *t* is the dominant selection criterion.
  FrameFusion is blocked on non-commercial weights; RIFE leads.
* [planning/inking-and-tween-plugins.md](planning/inking-and-tween-plugins.md)
  — **current.** Assessment of the candidate models for the inking and
  inbetweening plugin suite. LineArt ControlNet is the wrong tool for
  inking; Wan and FrameFusion are baselines rather than the engine;
  ToonComposer takes keyframe sketches at chosen frame indices, which
  is the only interface on offer that accepts a timing chart. Carries
  a licence audit: OpenRAIL-M accepted 2026-10-13, which clears the
  SD-lineage ControlNets for the colour stage; `sketch_simplification`
  and ToonCrafter remain blocked on non-commercial terms, neither on
  the critical path. §10 corrects the acceptance note's arc check, which
  is degenerate for a single inbetween. §11 lists the decisions the
  first tests depend on; §12 reads the ManRunCycle corpus — twelve
  aligned rough/clean pairs, no timing chart, use `12F/` not `10F/`.
  §13 separates the exposure sheet from the timing chart — different
  documents, both needed — and proposes an x-sheet JSON schema. §14 is
  the packaging: split by how far each pack can travel, the middle one
  named `comfyui_penciltest`, with the rig kept out by a test.
* [planning/acme-registration-plugin.md](planning/acme-registration-plugin.md)
  — design for the capture-and-register stage as a ComfyUI 0.35 plugin.
  Carries the rig questions that have to be answered before code.
* [planning/artifact-tracking.md](planning/artifact-tracking.md) — why
  ComfyUI's outputs and working state are tracked the way they are, and
  what backs them up.
