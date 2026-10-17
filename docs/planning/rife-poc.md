# RIFE proof of concept — design

*2026-10-16. Follows
[pencil-test-architecture.md](pencil-test-architecture.md), which makes
the proxy generator an instrument whose only obligations are
legibility, speed and faithful spacing.*

## 1. What it must answer

Five questions, in the order that would kill the idea soonest.

| # | question | why it could kill the idea |
|---|---|---|
| 1 | Does RIFE expose an **arbitrary timestep**? | the CLI documents only `--multi` and `--exp`, i.e. powers of two. If the model API has no `timestep`, §2's dyadic driver stops being optional |
| 2 | Is the output **legible enough to judge a pose**? | §4.2 predicts flow methods *ghost and double* lines on sparse black-on-white. That is the failure that matters, not joint onset |
| 3 | Does it **honour position along the path**? | §1's spacing contract. A proxy that puts a drawing somewhere the chart did not ask for voids the animator's approval |
| 4 | How does it degrade with **gap width**? | acceptance §7's unanswered question, promoted to load-bearing by §7c |
| 5 | Is it **fast enough for a flip loop**? | the whole reason we are not using ToonComposer |

**What it must not try to answer.** Whether the drawings are any good,
whether they obey the seven principles, or whether the final synthesis
stage works. The frames are disposable by design; see §1 of the
architecture.

## 2. Prerequisite, already checked

Interpolation accuracy cannot mean more than the registration under it.
Peg centroids across the twelve cleanups:

| | |
|---|---|
| typical disagreement with drawing 1 | **1–3 px** |
| worst | **6.4 px**, drawing 5 |
| at 200 px/inch | **0.82 mm** |

Good enough that a global shift will not dominate — but **6.4 px is a
floor on what any accuracy number here can mean**, and it is not
nothing for a flow estimator working on two-pixel lines. Report it
beside every result.

*(Two drawings returned four peg blobs rather than five. That is my
detector missing an edge dot, not a registration fault — the five-blob
cases bracket them.)*

## 3. The data

The corpus is better than a single example, which matters because one
triple proves nothing.

| | |
|---|---|
| cleanup triples | drawings *n*, *n+g*, *n+2g* — **10 at g=1** |
| rough triples | same, in blue pencil — **10 at g=1** |
| ground truth | the middle drawing, which the artist made |
| gap sweep | **g = 1, 2, 3** — predict 1, 3, 5 frames across a widening span |

The gap sweep is the point. §7c argues that the joint-onset objection
scales with gap width; this measures whether *interpolation quality*
does too, on the same axis.

## 4. Measurement, chosen in light of a mistake

**Mean absolute error is not used.** It misled twice during the
ToonComposer spike — it passed a run with a third arm, then ranked a
washed-out run above a better one — and an operator's eye caught both.
See §7b's retraction.

| what | measures | why this one |
|---|---|---|
| **contact sheets** | everything | **primary.** A human looks. This is the arbiter |
| **ink ratio** (generated ÷ truth ink pixels) | ghosting and washout | **directly tests §4.2's prediction.** Doubling pushes it above 1; washout below |
| **Chamfer distance** between ink masks | how far lines land from true lines | IoU is brutal on two-pixel lines, where a sub-pixel shift reads as total failure. Chamfer degrades gracefully and is interpretable: *"the line is 3 px from where it should be"* |
| **spacing fraction** via `penciltest.arcs` | §1's contract | the harness, used for its actual purpose for the first time |

## 5. Preprocessing sweep

§4a left open what RIFE wants as input, and flagged that the 1990s
threshold evidence may not transfer because **optical flow wants
gradients and a threshold destroys them**.

Three conditions, same triples: **raw capture**, **contrast-normalised
greyscale**, **thresholded**. If raw wins, §4a's conclusion — that
legibility processing is for registration and display, not for the
interpolator — is confirmed by measurement rather than argument.

## 6. Environment

A separate conda env, for a reason the ToonComposer spike already met:
**Practical-RIFE states python ≤ 3.11 and `storymator` is 3.14.** Same
pattern as `tooncomposer-spike` — do not disturb the documented
environment.

Licence is clean: MIT for code, and the model links are *"under the
same MIT license as this project"*. The one open item from
[pencil-test-architecture.md](pencil-test-architecture.md) §3 stands —
a third-party derivative warns the *training data* may carry
non-commercial terms. **Ask the author before anything ships**; it does
not block a proof of concept.

## 6a. No GPU required — and CPU is the default, not the fallback

Monte asked for confirmation. **Confirmed**, and it is now a design
constraint rather than an expectation.

**The evidence.**

| | |
|---|---|
| device selection | upstream's is the standard `torch.device("cuda" if torch.cuda.is_available() else "cpu")`, with cuDNN touched only when CUDA is present. **CPU works unmodified** |
| precision | no fp16 path in upstream `inference_img.py`. A community fork has an fp16 flag, but it sits inside a CUDA check and does nothing on CPU |
| model size | **~23 MB, fp32**. Against ToonComposer's 77 GB |
| fp16 | not wanted anyway — RIFE's coarse-to-fine flow is reported fp16-sensitive, so **fp32 on CPU is the accurate path**, not a compromise |
| this machine | 24-core Intel Core Ultra 9 275HX |

**The workload is small.** Ten triples × three preprocessing
conditions × three gaps × two media = **180 interpolations**. At 1–5
seconds each that is **3 to 15 minutes**, once, on the CPU.

**So the constraint:** the POC **runs on CPU by default and must be
written that way**. The GPU is used only for an explicit timing
comparison, never silently.

Two reasons that matters beyond convenience.

**An honest answer to question 5.** The machine has a GPU, so letting
torch pick a device would quietly measure the GPU and tell us nothing
about whether a drawing desk needs one. Architecture §5 puts the
instrument outside ComfyUI precisely so it can be light; if the proxy
path runs on a CPU, the desk's hardware story gets much simpler.

**Nothing else in the POC wants a GPU either.** Chamfer, ink ratio,
contact sheets and `penciltest.arcs` are numpy, Pillow and pure Python.

**One thing to check in step 1**, while reading the model file for the
timestep API: that the chosen 4.25 weights carry no CUDA-only
operation. Nothing in RIFE's architecture suggests one — it is
convolutions and `grid_sample` — but it is a free check while that file
is already open.

**Pin the thread count when timing.** Twenty-four cores will otherwise
make the numbers depend on what else the machine is doing, and this
session has already lost a run to a desktop competing for memory.

## 7. Order of work

1. **Verify the timestep API by reading the code**, not the README.
   The model file in `train_log/` is what matters, not
   `inference_video.py`. This is a gate: it decides whether §2's
   dyadic driver is needed.
2. Build the env, fetch a 4.25 model, interpolate one pair, look at it.
3. The g=1 cleanup sweep, three preprocessing conditions.
4. The gap sweep.
5. Roughs, which is the real input — the cleanups are a kinder test.
6. Timing, **CPU first** with a pinned thread count, GPU only as an
   explicit comparison. See §6a — the CPU number is the one that
   decides whether a drawing desk needs a graphics card.

## 8. Success criteria — provisional, Daniel's to set

Stated so the POC can fail rather than merely produce output. The
numbers are placeholders, in the same spirit as `arcs.py`'s thresholds.

| | provisional bar |
|---|---|
| legibility | an animator identifies the pose. **Binary, judged by eye** |
| ghosting | ink ratio within **0.7–1.4** of truth |
| spacing | fraction within **0.05** of the chart. Acceptance §2's named failure is 0.2 |
| speed | **under 200 ms/frame**, so a flip loop survives |

## 9. Scope and lifecycle

**Throwaway, like the ToonComposer spike.** Research code in the
scratchpad, no TDD, downloads kept. Its product is a **recorded
finding** in this directory, not a module.

If RIFE passes, the proxy generator is then built properly — tests
first, confirmed, committed — inside the instrument described in
architecture §5, which does **not** run through ComfyUI.

If it fails, the finding says which of the five questions killed it,
and the next candidate is chosen against the same five.
