# Setting up the scene so detection works

*Written 2026-09-21 from the first real `AcmeDetectSheet` run, which
refused with `no_consistent_triple  15 candidate(s)`. The detector was
working correctly; the scene was not.*

Companion to [calibrating-a-camera.md](calibrating-a-camera.md), which
covers the lens. This covers everything in front of it.

---

## Nothing bright may touch the sheet

**This was the whole failure.** The sheet segments by brightness and
the largest bright component is taken as the paper. A plastic bag and
a pale carpet lay below the peg bar, touching the sheet's bottom-left
corner, so paper and bag became **one component of 4.37 million
pixels** reaching the frame's bottom edge — and the corner fit was
asked for a rectangle that was not there.

The mask was fine. The corners were nonsense: one landed inside the
paper, one above it, one well below it on the bag.

Downstream this does not look like a segmentation problem at all. The
outline homography is wrong, so the pegs land at **y ≈ 190–203 mm**
where the model expects **y = 0**, and their spacings come out
**120.3 and 101.7 mm** instead of 101.6 twice. The detector then
reports, accurately, that no three candidates form a valid trio.

**Put something matte and dark under and around the bar**, covering
everything the camera can see past the paper. Black card is ideal and
is already on hand for the scanner work.

*Check:* the bright component should stop at the paper. If it reaches
the frame edge, something else is in it.

---

## Light it properly, and evenly

The failing frame had **median 0.384 and p98 0.490** — nothing within
half of saturation. Two consequences:

**The pegs fragment.** They are polished chrome, so under dim uneven
light each one breaks into several disconnected dark patches rather
than one blob. In the failing frame the left rectangular peg came
apart into **five** candidates spread over 23 mm, and the round peg
into two. Even with a correct outline, the fit would then pick a
fragment's centroid rather than the peg's.

**The threshold gets fragile.** A bimodal split at 0.253 separates
paper from desk with little margin, so a pale object anywhere near the
paper's brightness joins it.

This is the opposite of the calibration finding, where exposure did not
matter — correlation between brightness and per-frame error was −0.00
on a **black-on-white printed target**. A ChArUco board has ample
contrast at any exposure. Chrome pegs on white paper do not.

---

## Check the sheet model matches the paper

`canson_ream_0001` is **8.5 × 11 in**, not the 10.5 × 12.5 in ACME
field paper the `SheetModel` defaults to. In the peg frame the punched
edge is the 11 in one, so it is **279.4 mm along the bar by 215.9 mm
into the sheet** — see
[../data/calibration/acme_paper/README.md](../data/calibration/acme_paper/README.md).

`v4k_01.json` already carries the corrected values. A wrong sheet model
gives a plausible-looking outline and quietly wrong peg coordinates.

---

## Diagnosing a refusal

The refusal reasons distinguish the failure modes, and are worth
reading literally:

| reason | means |
|---|---|
| `no_candidates` | fewer than three peg-like regions. Check `peg_appearance` and the lighting. |
| `no_consistent_triple` | candidates exist but no valid trio. **Usually the outline, not the pegs** — check the mask first. |
| `residual_too_high` | the trio was found and does not fit. Paper curl, a peg fragment chosen over a peg, or a genuinely bad frame. |

`no_consistent_triple` is the misleading one: it names the pegs, and
the cause is normally upstream of them. Look at the sheet mask and the
fitted corners before touching any peg parameter.

A quick way to see it is to overlay the mask and the fitted corners on
the frame — `AcmeDetectSheet`'s `overlay` output draws the corners, and
a bad fit is obvious at a glance.

---

## What is *not* yet established

The first run is **not** evidence about peg-top parallax. Blanking the
background crudely, to test the diagnosis, also clipped the paper, so
that run's outline residual stayed at 559 px and its punch offset came
out 193.70 mm against a nominal 12. Its apparent peg span of 222.05 mm
implies an effective peg height of **25–38 mm** against a peg that
stands 6.26 mm above the paper — impossible, and confirming the outline
was still wrong rather than that parallax is large.

Measuring `h_eff` from a real capture still needs a frame where the
outline fits cleanly, which needs the background and lighting fixed
first. That remains the open input to the parallax correction.
