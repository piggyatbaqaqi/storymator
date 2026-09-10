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
* [planning/artifact-tracking.md](planning/artifact-tracking.md) — why
  ComfyUI's outputs and working state are tracked the way they are, and
  what backs them up.
