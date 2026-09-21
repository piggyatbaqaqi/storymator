# Camera frames from the rig

Real captures, with what can be derived from them and what cannot.

## Why this exists

ComfyUI writes every `PreviewImage` to its `temp/` directory and
**clears it on restart**. On 2026-09-21 an overnight session worked
through four lighting setups and a fix for a 180° outline error,
measuring each frame carefully — and every one of those frames was
gone by the afternoon. The measurements survive in
[../../docs/rig-setup.md](../../docs/rig-setup.md) and
[../calibration/pegs/honbay_0001/README.md](../calibration/pegs/honbay_0001/README.md);
the pixels do not.

A frame is worth keeping when it is **hard to reproduce**: a
particular lighting rig, a particular failure, a sheet placed a
particular way. Re-running the graph tomorrow does not recreate those.

## Collecting

```sh
bin/collect-captures --note "phone at the lens, room dark, monitor fill"
bin/collect-captures --session daylight --since-minutes 20 --dry-run
```

Captures only by default. Overlays and greyscale diagnostics are
regenerable from a capture plus a calibration, so keeping them stores
the same information twice.

**The note is the point.** Exposure statistics come out of the pixels;
where the light was does not, and nobody reconstructs it a week later.

## What is tracked, and what is not

| | |
|---|---|
| `manifest.json` | **tracked** — small, and it carries the notes |
| `*.png` | **ignored** by default |

53 frames is 406 MB against a 141 MB repository, so a rescue is not by
itself a decision to keep. Commit a frame deliberately, `git add -f`,
when it earns its place as a regression case — a failure worth
reproducing, or a condition worth testing against.

Frames stay on disk either way, and `bin/backup-storymator` covers the
whole tree, so nothing is lost by leaving them untracked.

## Sessions

| session | frames | conditions |
|---|---:|---|
| `2026-09-21` | 53 | **Not recorded.** Rescued after the fact during rectangle-fitting work; the operator was varying the lighting but the setups were not written down. Exposure medians span 0.141–0.792, so they do cover real variety — it is just unlabelled variety. |

That first row is the argument for the tool. Everything in it would
have been worth labelling and none of it was, because there was no
habit and no place to put it.
