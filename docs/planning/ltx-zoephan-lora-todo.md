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
- [ ] **Environment.** Set up `packages/ltx-trainer` in its own
  environment (it uses `uv`).
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
- [ ] **Clean the frames.** White out the top-right number-box edge and
  the scan-edge strips (frames 5, 11 and 12 most visibly); convert
  mode L to RGB. Keep registration: no per-frame cropping.
- [ ] **Build the dataset.** 12 clips of 25 frames — the 12 drawings on
  twos, starting at each drawing in turn, closing on the first again —
  plus the 12 drawings as stills. Bucket 1184×832 (paper aspect
  1.4232), falling back to 960×672 or 640×448. Index by drawing number
  from the manifest, never by glob.
- [ ] **Captions.** One metadata JSONL. Each caption says what varies
  (pose, hat lifting on 5 and 11, cane swing); style words once.
  Trigger `Zoephan` via `training_strategy.data.lora_trigger`, not in
  the captions.

## Train

- [ ] **Baseline before training.** The fixed prompt set on stock LTX
  with no LoRA, and the reference-sheet ("ingredients") route if it
  runs locally. This is what the LoRA must beat.
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
