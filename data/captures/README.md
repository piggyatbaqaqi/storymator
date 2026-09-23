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

| `2026-09-21-rect-first` | 2 | Ambient room light, cell phone behind the lens, white monitor screen opposite the room light. First frames with rectangle fitting in earnest; the shadows are picked up as features. |
| `2026-09-21-phone-beside-lens` | 6 | As above but the phone *next* to the lens rather than behind it. Subjectively a much better match. |
| `2026-09-21-low-grazing` | 2 | Phone held low above the paper, ambient room light, white monitor. Shot to test the specular base line. |
| `stability-light-A` | 6 | Repeat frames, light held still. The unclipped control: outline error 1-5 px across all six. |
| `stability-light-B` | 6 | Repeat frames with the sheet increasingly clipped, 5.5 % to 26.6 %. Outline error tracks the clipping to 84 px. |
| `hamster-crowbar-A` | 2 | Printed animation art by Dr. Boulos, lighting as `-phone-beside-lens`. Regression case: detection must not be confused by artwork. |
| `hamster-crowbar-B` | 2 | Same art, lighting as `-low-grazing`. |
| `blue` | 5 (+5 diagnostics) | Peg crowns coloured with a pen+GEAR dry-erase marker. Exposure alternates frame to frame, medians 0.243/0.067/0.212/0.059/0.220, so half the session is near-black. Note reads "phone next to lens, bar moved, exposure fixed" and that bar move is why 006 shows the tint far more weakly than 008 and 010. Holds `blue_006_round_peg_closeup.png`, a byte-exact crop. |
| `blue_hamster` | 3 (+1 diagnostic; 2 lost) | Dr. Boulos's printed hamster art on blue-marked pegs, phone next to the lens, exposure fixed. `003`/`004` are one setup; `002` has the bar moved right. **Two frames were destroyed** — see below. The paper's right edge bows 8-11 mm. |
| `fresh_ink` | 2 | Dry-erase blue reapplied to all three crowns, phone next to the lens, exposure fixed. `007` blank, `008` the printed hamster art. The cleanest peg detection so far: the three pegs are the top three components of a b* < -8 threshold in both, artwork included. Numbered from 007 because the operator pruned the run's diagnostics by hand. |
| `square` | 7 (+7 diagnostics) | Bar squared to the frame, pegs reinked. Room light **off**, monitor white, phone light next to the lens. `013` blank and `014` art are the pair; `008`-`012` are earlier tries and `010` is near-black. Shot to test the outline fix -- and they show squaring the sheet does *not* help, because the mask is near-square either way. |

That first row is the argument for the tool. Everything in it would
have been worth labelling and none of it was, because there was no
habit and no place to put it.

## Collecting twice into one session

Numbering continues from the highest frame the session has already
used, counting both the files on disk and the manifest's entries. So a
second collect appends, and a frame deleted by hand leaves a gap
rather than an alias for something the manifest still describes.

It did not always. Until 2026-09-22 numbering restarted at 001 on
every run, so a second collect wrote over the first one's frames;
`blue_hamster` lost two that way, and their entries survive in its
manifest marked `"lost"`. The content-hash skip never covered this —
it stops the same *frame* being copied twice and says nothing about
the *name* a genuinely new frame is given.

Tests are in `bin/collect_captures_test.py`, the first tests for
anything in `bin/`.
