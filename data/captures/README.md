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

Notes come in two kinds. `--note` describes the *session*; `--frame-note`
attaches to every frame in that run. Hand-editing a frame's `notes`
key afterwards works too and is preserved by every tool here — the
first one in this corpus was written that way, on
`2026-09-21/2026-09-21_007.png`.

**Collecting twice is safe.** Frames already held in any session are
skipped by content hash, so shoot, collect, shoot, collect and you
only ever get what is new. That was not true at first: the tool took
everything in `temp/`, which only grows, so a second run re-copied the
whole history. Two sessions ended up sharing 22 frames before
`fixes/prune-duplicate-captures` sorted them out.

## When frames disappear

ComfyUI clears `temp/` with `shutil.rmtree` at **startup and shutdown**,
and nowhere else — so frames accumulate indefinitely while it runs and
vanish the moment it restarts. Shoot as many as you like; **collect
before restarting.**

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
