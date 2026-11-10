# LTX LoRA of Zoet — to-do

Started 2026-11-07. A proof of concept: teach LTX-2.x the run-cycle
character, **Zoet** (working name Zoephan until 2026-11-10), from the
12 dropped-out cleanups of
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
- [x] **Checkpoint.** The trainer's docs accept a 2.5 split pack
  (transformer, packed Gemma 4 encoder, VAEs), which matches the files
  LTX Desktop already has, but never say whether the *distilled*
  transformer can be trained or a dev one is expected. They do warn to
  match the training base to the inference base, and Desktop runs the
  distilled one. Settle it in the smoke run. Monte accepts the gated
  2.5 terms on Hugging Face; record the 2.5 licence text in
  `LICENSES.md` (a non-commercial term would still block).
  Settled: the *distilled* transformer trains (smoke run, then the
  Modal runs) and its LoRAs load in `ltx_pipelines.distilled`; the 2.5
  agreement is recorded in `LICENSES.md`, accepted 2026-11-07.
- [x] **Video only.** The shipped configs train audio too; our clips
  are silent, so set `audio.is_generated: false`. Done by leaving audio
  out of the config altogether: `audio_vae_path: null` and no audio
  modality block in `configs/mixed.yaml`.
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
- [x] ~~**Captions.** One metadata JSONL. Each caption says what varies
  (pose, hat lifting on 5 and 11, cane swing); style words once.
  Trigger `Zoephan` via `training_strategy.data.lora_trigger`, not in
  the captions.~~ Superseded by the approved captions above and the
  trigger choice below.

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
- [x] **Trigger word.** `Zoephan` has an elephant prior, so it stays
  the character's name and the trigger is chosen separately. The
  operator's candidates were tested on the stock model 2026-11-07, one
  seed each (lab repo, `spikes/ltx-lora-2026-11-07/triggers/`):
  Phenak gave a big-headed cartoon kid, Cellauf a generic boy,
  Vandervell a young man in blue-tinted jeans, and **Zoet a
  featureless mannequin** — the least prior. A second seed (7) for
  Zoet and Cellauf held the pattern: Zoet again a faint generic
  figure, Cellauf again the same boy with hair. **Chosen 2026-11-07:
  `lora_trigger: "Zoet"`**, in the lab repo's
  `spikes/ltx-lora-2026-11-07/configs/mixed.yaml`. The character took
  the trigger's name too, 2026-11-10 (next item).
- [x] **Rename after the test pipeline.** Once the whole pipeline has
  run end to end, change "Zoephan" to "Zoet" throughout the
  documentation (operator, 2026-11-07), **except** experiment records
  — the spike directory and its write-up keep the history as it
  happened. Done 2026-11-10: this file (was `ltx-zoephan-lora-todo.md`),
  the corpus manifest's `character` note and `LICENSES.md`. Lines that
  record what happened under the old name (the elephant, the original
  trigger plan) keep it.
- [x] **Preprocess** latents and text embeddings, 2026-11-07, third
  attempt: the 8-bit text encoder plus embeddings processor peak at
  20.8 of 23.4 GiB, so it only fits with other GPU processes closed.
- [ ] **Smoke run** (10 steps): does it fit in 24 GB? Evidence in the
  lab repo, `spikes/ltx-lora-2026-11-07/runs/`.
  - Validation prompt caching loads the text encoder at startup and
    OOMs; the smoke config has no validation samples.
  - int8: OOM on the first forward pass (22B int8 ≈ 22 GB).
  - int4: needs the venv's ninja, CUDA 13.2 and a `libcudart.so`
    link on the path (`train.sh`), and two patches applied by a
    launcher (`train_patched.py`) without touching the trainer: root
    `*adaln_single` modules left unquantized (an upstream exclusion
    bug), and int4 layers run in bf16 inside the fp32 pass.
  - **Trains: all 10 steps ran, peak 21.7 GB, about 2.4 min/step**
    (~40 h per 1000 steps). The final checkpoint save then OOMed,
    unpacking every int4 weight on the GPU to build the full state
    dict.
- [x] **Rented-GPU benchmark**, run 2026-11-07 on Modal: lab repo,
  `spikes/ltx-lora-2026-11-07/modal/bench.py`, summary in
  `runs/modal_bench_summary.json`. 30 steps of the same recipe in bf16
  (no quantization, no launcher patches); stills and clips timed
  separately, weighted equally as the dataset is.

  | Arm | Still | Clip | Peak | 1000 steps |
  |---|---|---|---|---|
  | H100, checkpointing on | 0.62 s | 1.17 s | 44 GB | ~16 min, ~$1.35 |
  | A100 80GB, checkpointing on | 0.98 s | 3.01 s | 44 GB | ~34 min, ~$2.10 |
  | H100, checkpointing off | 0.38 s | OOM | 80 GB | — |

  Rates read 2026-11-07: H100 $3.95/h, A100 80GB $2.50/h, plus about
  $1.14/h for 8 cores and 96 GiB. Launch to first step ~50 s; Modal
  billed about $0.60 for all three arms, so container start adds a
  few minutes per run. The final LoRA save works in bf16 (214 MB).
  Checkpointing must stay on: the first clip OOMs without it. Not
  measured: validation (text encoder plus 49-frame samples), which
  real runs will add. Locally the same recipe in int4 ran ~2.4
  min/step, ~150× slower than the H100. Getting there took three
  launches: upstream has no `uv.lock` (vendored the local one), and
  Modal's mount paths break the preprocess fingerprint
  (`allow_stale_preprocessed` for the bench only).
- [x] **Three short runs:** stills only, clips only, mixed
  (`batch_size: 1`). Same prompts, same seeds. Run 2026-11-07 on
  Modal H100s, 2000 steps each, checkpoints every 250 on the
  `zoet-runs` volume; $9.10 for the three. Evidence in the lab repo,
  `spikes/ltx-lora-2026-11-07/compare/`. Read from the trainer's
  validation, which can only approximate the distilled sampler (8
  steps, no guidance), so this ranks the arms; it does not judge
  them:
  - Drawing 1 as first frame: **stills-only holds the model best**
    (darker, coherent lines; hat, ears, nose, cane, coat in nearly
    every frame). Mixed ghosts more; clips-only is faintest and
    smears mid-clip.
  - Text only: mixed draws a top-hatted runner from step 1250 with no
    props; stills-only gets the hat by 1500 but holds a sheet of paper
    in almost every sample (the style sentence's "on white paper");
    clips-only never learns the hat.
  - Operator, 2026-11-09: stills `step_001750_2` is the best sample
    (likes the pony-tail); the floating hat and the mid-step crouch are
    lost; more steps not obviously better.
- [x] **Renders through the real pipeline**, 2026-11-09 on Modal H100s:
  `ltx_pipelines.distilled` with the baseline's settings (fp8-cast,
  1088×768, 49 frames, seed 42), no offload, ~1.5 min each. Stock (same
  Zoet prompt), stills at 1000/1750/2000, mixed at 1750/2000, text-only
  and drawing-1 first frame. Evidence in the lab repo,
  `spikes/ltx-lora-2026-11-07/renders/`: figure, feet and hat montages
  (drawings on twos above frames 0–23 and 24–47, identical crops) from
  `montage_render.sh`, and `overview_{i2v,t2v}.png`.
  - The LoRA loads: with the same prompt, stock draws a bald generic
    man; every stills checkpoint draws the top-hatted character.
  - Drawing 1 as first frame: stills stays on model through all 48
    frames at every checkpoint, and the three are hard to rank. Stock
    breaks into scribble in some frames. Mixed goes faint and smeary
    after frame 0, so it is worse in the real pipeline too.
  - Text only: stills draws hat, coat and fists, faint, with no cane
    and **no paper prop** at any checkpoint.
  - Motion (feet band): feet travel through contact, passing and up in
    order, with smears in a few frames. A step every ~9.6 frames
    against the drawings' 12, the same rhythm as stock. No crouch on
    the down poses (d5, d11), no hat lift, and the cane stays upright.
    **The LoRA has learned the look, not this cycle's acting.**
- [x] **Drop "on white paper"** from the style sentence (operator,
  2026-11-09): `captions_nopaper.json`, `dataset_nopaper.jsonl`;
  stills-only retrained 2000 steps. **It did not remove the prop**: the
  trainer's text-only samples still hold a sheet from step 750. In the
  real pipeline there is still no prop, and the hat is lost at
  1000/1750. Hypothesis, untested: the prompt's "each drawing held for
  two frames" comes only from the clip captions, which stills-only
  never saw; mixed saw it and never drew the prop. Modal for the day:
  $5.60.
- [x] **The LoRA as an inbetweener**, 2026-11-10 (operator-approved
  placement). Drawings pinned as keyframes at their on-twos frame
  times: k3 = d01@0, d05@8, d11@20; k6 = k3 plus the same keys one
  cycle later. Stills step 1750 against stock; seed 42, guide strength
  1.0. Evidence in the lab repo, `renders/montages/*_k3_*`, `*_k6_*`.
  - The key drawings do appear at their frames, crouch and floating
    hat included. But they are **reached through scribble and left by
    dissolving**, not by travel. Between keys the figure returns to a
    d01-like pose instead of running on through d06–d10.
  - With keys every cycle (k6) both models **jump and hold**. Stock
    holds every pose for three frames; the LoRA holds d11 for seven
    frames and brings the second crouch in eight frames early.
  - **The LoRA does not help here.** It hits the keys no better than
    stock, and stock's approach into d05 is cleaner. Not varied: guide
    strength, the seed, and the prompt's "each drawing held for two
    frames", which may invite holds.
- [ ] **Load check.** LTX Desktop skips a mismatched LoRA silently:
  confirm a visible difference with the LoRA on and off.
  The step-1750 stills LoRA is installed at
  `~/.local/share/LTXDesktop/models/loras/zoet/zoet-stills-1750-lora.safetensors`
  (2026-11-10). Desktop's API needs the Electron app's token, so the
  with/without pair is run from the UI by the operator.

## Pencil test

- [x] Generate a run of Zoet with the trained LoRA and judge it by
  motion: does a foot travel through intermediate positions, in order,
  without jumping or holding, and stay on model? Band crops of the foot,
  generated frames and Dr. Boulos's drawings in two rows of one montage.
- [x] Write up [ltx-lora-poc.md](ltx-lora-poc.md) (2026-11-10); update
  `pencil-test-architecture.md` §3, `inking-and-tween-plugins.md` §7a
  and `bibliography.bib`. Archive frames, montages and logs to
  `~/lab/storymator/spikes/ltx-lora-<date>`; none of it is published.
