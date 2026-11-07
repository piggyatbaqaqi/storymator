# LTX LoRA of Zoephan — to-do

Started 2026-11-07. A proof of concept: teach LTX-2.x the run-cycle
character, working name **Zoephan**, from the 12 dropped-out cleanups of
`manrun_cycle_2001_wwc`. If the result is good, more drawings of the
character come from Dr. Boulos.

Settled: LTX-2 Community License accepted
([LICENSES.md](../../LICENSES.md)); timing on twos at 24 fps and
training permission (the corpus manifest). Train locally, with 4-bit
weights if needed; a rented GPU is acceptable — the art is not to be
*published*, which is a different thing from never leaving this machine.

## Prepare

- [x] **Trainer.** Cloned `Lightricks/LTX-2` to
  `~/src/github.com/Lightricks/LTX-2` at `4f52161` (2026-11-04), not
  forked: nothing found so far needs a code change. Not the old
  `LTX-Video-Trainer` checkout, which targets LTXV 0.9.x.
- [x] **Environment.** `uv sync` at the repo root, 2026-11-07, into
  `LTX-2/.venv`: torch 2.13.0+cu132, sees the RTX 5090 Laptop (sm_120);
  `ltx_trainer` and `optimum.quanto` import. The snap `uv` is broken
  on this machine; the one in the `storymator` conda env (0.12.2) was
  used.
- [ ] **Checkpoint.** The trainer's docs accept a 2.5 split pack
  (transformer, packed Gemma 4 encoder, VAEs), which matches the files
  LTX Desktop already has, but never say whether the *distilled*
  transformer can be trained or a dev one is expected. They do warn to
  match the training base to the inference base, and Desktop runs the
  distilled one. Settle it in the smoke run. Monte accepts the gated
  2.5 terms on Hugging Face; record the 2.5 licence text in
  `LICENSES.md` (a non-commercial term would still block).
- [ ] **Video only.** The shipped configs train audio too; our clips
  are silent, so set `audio.is_generated: false`.
- [x] **Clean the frames.** Done 2026-11-07. Rather than a fixed
  corner box, the cleaner keeps the figure and drops everything else:
  dark components touching the sheet edge go (the number-box edge on
  every sheet, the right-edge strip on 5, the bar on 11), and so does
  anything not within 40 px of a stroke of 500 px or more (number
  ghosts, dust). 31–3123 px whitened per drawing. Checked by eye on a
  red overlay of every removal: none touches the figure; the 23
  removals within 150 px of it are 1–10 px dust dots, the two largest
  and one inside an ear confirmed against the colour scan. Converted
  to RGB; nothing cropped or moved.
- [x] **Build the clips and stills.** Done 2026-11-07: 12 clips of 25
  frames at 1184×832, 24 fps, H.264 CRF 4 — the 12 drawings on twos,
  starting at each drawing in turn, closing on the first again — plus
  the 12 stills, box-filtered from full resolution. Indexed by drawing
  number from the manifest. Every clip decoded and matched frame by
  frame against the stills: order correct in all 12, worst mean error
  0.02/255.
- [x] **Line weight.** At 1184×832 the lines average to a pale grey
  (drawing 1: median 190/255, darkest 88). Decided 2026-11-07: train on
  the light pencil as is; revisit with automatic clean-up of roughs.
- [x] **Captions** approved 2026-11-07 (`dataset.jsonl` beside the
  clips, from `captions_draft.json` in the spike directory). Each pose
  names its phase (contact 4/10, down 5/11, passing 6/12, up 1–3 and
  7–9), the feet and hands by side, the hat, cane, coat tails and
  trouser cuffs; identity is left to the trigger. Stills 81–108 Gemma
  tokens, clips 719, limit 1024.
- [ ] **Captions.** One metadata JSONL. Each caption says what varies
  (pose, hat lifting on 5 and 11, cane swing); style words once.
  Trigger `Zoephan` via `training_strategy.data.lora_trigger`, not in
  the captions.

## Train

- [x] **Baseline before training.** Run 2026-11-07 on stock LTX-2.5
  22B distilled, no LoRA (`ltx_pipelines.distilled`, fp8-cast weights,
  CPU offload; 1088×768, 49 frames, seed 42; ~4 min each, fits 24 GB).
  Evidence in the lab repo, `spikes/ltx-lora-2026-11-07/baseline/`.
  - Short text prompt: pencil style and an alternating-leg run are
    right, but the figure is a cartoon **elephant** — the stock model
    reads "Zoephan" as elephant.
  - Full 719-token training caption: an incoherent hat-and-cane
    creature with a snout, dissolving into scribble in many frames.
  - Drawing 1 as first frame: stays on model; the legs cycle through
    intermediate positions, but the hat never lifts, the cane stays
    upright, the coat tails barely move, and frames 17–21 ghost
    between poses. This is the result the LoRA must beat.
  - Not run: the reference-sheet ("ingredients") route.
- [ ] **Trigger word.** `Zoephan` has an elephant prior, so it stays
  the character's name and the trigger is chosen separately. The
  operator's candidates were tested on the stock model 2026-11-07, one
  seed each (lab repo, `spikes/ltx-lora-2026-11-07/triggers/`):
  Phenak gave a big-headed cartoon kid, Cellauf a generic boy,
  Vandervell a young man in blue-tinted jeans, and **Zoet a
  featureless mannequin** — the least prior. Awaiting the choice.
- [ ] **Preprocess** latents and text embeddings with the trainer's
  dataset step.
- [ ] **Smoke run** on a small subset: does it fit in 24 GB? In order,
  try the INT8 low-VRAM config, `quantization: "int4-quanto"` (already
  a config option, no patch), a smaller bucket, then a rented GPU.
- [ ] **Three short runs:** stills only, clips only, mixed
  (`batch_size: 1`). Same prompts, same seeds.
- [ ] **Load check.** LTX Desktop skips a mismatched LoRA silently:
  confirm a visible difference with the LoRA on and off.

## Pencil test

- [ ] Generate a run of Zoephan with the trained LoRA and judge it by
  motion: does a foot travel through intermediate positions, in order,
  without jumping or holding, and stay on model? Band crops of the foot,
  generated frames and Dr. Boulos's drawings in two rows of one montage.
- [ ] Write up `docs/planning/ltx-lora-poc.md`; update
  `pencil-test-architecture.md` §3, `inking-and-tween-plugins.md` §7a
  and `bibliography.bib`. Archive frames, montages and logs to
  `~/lab/storymator/spikes/ltx-lora-<date>`; none of it is published.
