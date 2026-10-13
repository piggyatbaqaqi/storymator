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
| **repository tooling** | [`requirements-dev.txt`](../requirements-dev.txt) | pytest, mypy, flake8, bibtexparser — installed by whoever works on the repo, by nobody else |
| **the environment** | the `storymator` conda env | numpy, scipy, Pillow, OpenCV and torch come from here, and are deliberately *not* pip-declared, so nobody installs a second conflicting set |

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

* **mypy and flake8 have no configuration file** anywhere — no
  `setup.cfg`, `.flake8` or `mypy.ini`. CLAUDE.md requires new code to
  pass both, so "passes mypy" currently means "passes whatever mypy is
  on the path, with its defaults", which is not reproducible between
  machines or over time.
* **The `storymator` conda environment is undocumented.** There is no
  `environment.yml`, and running the suite under the wrong environment
  does not fail — it silently collects fewer tests. That is an
  experienced failure, not a hypothetical one, and `requirements-dev.txt`
  does nothing about it.
* **The `bin/` CLIs' runtime dependencies are undeclared.** They import
  numpy, scipy, Pillow and OpenCV and rely on the conda environment
  having them.

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
