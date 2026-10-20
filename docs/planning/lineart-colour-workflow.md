# Clean line drawing → coloured character, in ComfyUI

*2026-10-20. Rescued from a spike session's scratchpad; see §5 for why
that matters. This is the colour stage, not the inbetweening stage —
it is the "completely different direction" opened on 2026-10-19 while
[wan-fun-inp-poc.md](wan-fun-inp-poc.md) was stalling.*

## 1. What it does

One cleaned-up line drawing in, one coloured character on a painted
background out. SD 1.5 with a lineart ControlNet holding the drawing's
strokes, two prompts — character and background — concatenated, and the
latent sized from the drawing so the output keeps its aspect.

It is **not** a pencil test and does not inbetween anything. It is the
stage that ToonComposer was relocated to in
[inking-and-tween-plugins.md](inking-and-tween-plugins.md) §4.3, done
with parts we already have and can run.

## 2. Files

| file | what it is |
|---|---|
| `comfyui/workflows/gen_lineart_colour.py` | **the source of truth.** Emits both JSONs: `python gen_lineart_colour.py UI_OUT.json API_OUT.json` |
| `comfyui/workflows/lineart_colour_workflow.json` | the **UI graph** — drag onto the ComfyUI canvas to open and edit |
| `comfyui/workflows/lineart_colour_api.json` | the API twin, for `POST /prompt` |
| `comfyui/workflows/examples/character_clean.png` | a synthetic stick figure for smoke-testing. Not WWC art |

Edit the generator and regenerate; do not hand-edit the JSONs, or the
two will drift.

## 3. The two formats are not interchangeable

The API twin has **18 nodes**, the UI graph **21**. API format drops
bypassed nodes and canvas-only nodes, so the twin is missing:

- node 14 `ControlNetLoader` (canny) and node 15 `ControlNetApplyAdvanced`,
  the **bypassed** canny branch;
- node 21 `MarkdownNote`, the on-canvas instructions.

So the UI graph is the richer artefact and the one to keep. Converting
API → UI recovers the executable path and silently loses the rest; that
conversion was written and then thrown away once the generator turned up,
because the generator already emits both.

Verified 2026-10-20: the generator's API output is byte-identical to the
copy rescued from the scratchpad, and the UI graph round-trips to that
same API prompt.

## 4. Before it will run

**It has never produced an image.** The only recorded run, 2026-10-19
16:13, failed validation:

```
ControlNetLoader 11:
  - Value not in list: 'control_v11p_sd15_lineart_fp16.safetensors' not in []
```

`not in []` — ComfyUI saw *no* ControlNet models at all. That has since
been fixed: the lineart model was downloaded at 16:32, nineteen minutes
later, so the workflow has never been tried since the thing blocking it
was cleared.

Present now, in `ComfyUI/models/`:

| | |
|---|---|
| `checkpoints/v1-5-pruned-emaonly-fp16.safetensors` | ✓ stock Stability SD 1.5, not a community merge |
| `controlnet/control_v11p_sd15_lineart_fp16.safetensors` | ✓ 722 MB |
| `controlnet/control_v11p_sd15_canny_fp16.safetensors` | **✗ absent** |

The canny model's absence does not block a run — node 15 is bypassed —
but node 14 will show an invalid value when the graph opens. Either
fetch it from `comfyanonymous/ControlNet-v1-1_fp16_safetensors` or
ignore the warning.

**Licences.** Both the checkpoint and the lineart ControlNet are
CreativeML OpenRAIL-M, accepted for this project 2026-10-13. Traced
2026-10-20: the checkpoint is stock SD 1.5, so there is no community
merge with untraced ancestry underneath it.

## 5. Why this was nearly lost

The session that built it ran in a VS Code window opened on the
**pinball** directory, so Claude Code filed it under the pinball project
and its scratchpad landed in `/tmp` under a pinball path. Nothing was
committed to either repo. The only copy of a working artefact sat in a
temporary directory belonging to a session that was about to be retired.

The same directory confusion caused the OOM recorded in the
`tooncomposer-spike-oom` memory. Second time; worth a rule.

**Rule:** a spike that produces an artefact someone will want again —
a workflow, a config, a generator — gets committed before the session
ends. The scratchpad is for intermediates, not for results.

## 6. Open

- Run it. Nothing here has been executed end to end.
- The note baked into node 21 warns that a transparent PNG loads as
  black and the ControlNet then reads the whole frame as ink. Untested.
- Whether `end_percent` 0.8 actually lets the background fill in, or
  whether the empty paper still pushes the result toward a blank
  backdrop. The value was chosen by reasoning, not measurement.
- Whether this belongs in the suite at all, or stays a scratch tool.
