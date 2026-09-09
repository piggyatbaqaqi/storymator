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

## Working notes in this repository

* [planning/inbetweening-scope.md](planning/inbetweening-scope.md) — scoping the
  automatic-inbetweening subproject. **Note:** its A/B framing predates
  a careful reading of the coarse-scoping document above, which already
  names *pencil test* as the output. See the note at the head of that
  file.
