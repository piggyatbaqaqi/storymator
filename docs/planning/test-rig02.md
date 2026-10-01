# The id blocks work; the camera is still not where the test said to put it

**Verdict.** Two results from `test_rig02`, and they pull opposite ways.

**The marker-id allocation is proved in practice.** Eighteen frames,
sixty board poses, **zero duplicate ids**. Nine of those frames carry
`charuco_0001` (ids 0–30) and all four ref 2 pieces (40–55) at once,
which is exactly the frame that was unreadable on ref 1. ref 1's
pieces are off the disc — no id below 40 appears in the artwork set.

**The camera moved the wrong way.** It went **up 19 mm and out 34 mm**
from `test_rig01`, so the targets are *less* even than before and the
disc plane is recovered worse.

| rig | height | lateral | incidence | marker side | spread |
|---|---:|---:|---:|---:|---:|
| test_rig01, mounted | 321 mm | 240 mm | 36.8° | 31–74 px | 2.4× |
| **focus-100 hand-held** | 348 mm | **28 mm** | **4.6°** | **62–66 px** | **1.1×** |
| **test_rig02, mounted** | 340 mm | **274 mm** | **38.8°** | **22–78 px** | **3.5×** |

The hand-held test frame showed what centring buys: a 1.1× spread
against 3.5×. The mounted rig did not inherit it.

## What the plane costs now

| set | four-target frames | normal scatter | at the paper corner | of budget |
|---|---:|---:|---:|---:|
| artwork | 5 of 9 | 0.457° | **1.133 mm** | **141 %** |
| charuco | 3 of 9 | 0.176° | 0.435 mm | 54 % |

Both are thin — five frames and three — and they disagree by more than
either can resolve, so neither is a number to rely on. What is solid
is the reason: at 38.8° incidence with `tan` 0.805, every milliradian
of normal error costs 25 % more than it did at rig 01's 29.7°, and
the targets span 22 to 78 px so the weak one dominates.

**Over half the frames lose a target.** Only 5 of 9 and 3 of 9 have
all four, and the missing one is almost always W, the outermost at
175.5 mm. A three-target frame fits a plane exactly and reports no
residual, so it cannot even warn you.

## The targets themselves are where they were

Recovered from 60 poses, and essentially identical to ref 1's layout
because the same landscape sheet forces it:

| | bearing from N | radius | rig 01 radius |
|---|---:|---:|---:|
| N (piece #0) | — | 140.5 mm | 138.5 |
| E (#1) | 91.1° ± 0.7 | 165.4 mm | 164.9 |
| S (#2) | 184.5° ± 1.4 | 138.2 mm | 137.9 |
| W (#3) | 271.4° ± 1.4 | 175.5 mm | 176.6 |

Radius fit residual 2.36 mm, which is the disc shifting under the hand
between rotations rather than target placement.

## The charuco set cannot recalibrate the lens

It was the obvious hope and it does not work. Across the nine frames
the board's normal moves **0.18° to 0.41°** — it is the same sheet
lying flat on a disc that turns about its own normal, so its
orientation barely changes. Zhang's method separates focal length from
distance only when the board is seen at many *orientations*. The set
is degenerate for intrinsics.

It can still **check** the stored lens, and does: `charuco_0001`
reprojects at **1.262 ± 0.097 px** against the 48-frame calibration's
0.707. Elevated — but these are single-frame fits of a paper board,
and the same ambiguity applies as before: 1 px at 440 mm is 168 µm of
object, so a little bow explains it as well as a changed lens.

**The focus setting was not recorded**, and that is the gap that
matters. The stored calibration is at `focus_absolute` 134; the
hand-held test at this height used 100. Until that is known, every
number in this document carries an unquantified lens error.

A real recalibration needs the 48-frame treatment: the board held at
many angles, not lying on the disc.

## Better than rig 01 in one respect

The lighting is **reproducible**. Room light, white terminal and the
CZUR Fancy Pro's lamp, with **no window light** — where `test_rig01`
had diffuse sunlight that moved through the session and could never
be repeated. The CZUR is a second camera being used as an
illuminator; it is unnamed and uncalibrated, and worth naming if it
stays.

## What to change

**Centre the camera.** It is the one change the measurements already
argue for, it was demonstrated by hand, and it is worth more than
anything else available: the hand-held frame got the four targets to
within 7.5 % of each other, where this rig spans 250 %.

**Record the focus**, and recalibrate the lens at whatever it turns
out to be if it is not 134.

## Status

**Measured**: all 60 board poses, the camera's height, offset and
incidence, the target radii and bearings, the duplicate-id count, the
board-normal spread and the `charuco_0001` reprojection — from the
eighteen frames, using ref 2's measured 11.905 mm square and the
stored `v4k_01` intrinsics.

**Computed**: the paper-corner projections, from the normal scatter
and the incidence.

**Not recorded**: the focus setting, the disc diameter (carried over
from rig 01 rather than re-measured), and per-frame exposure — these
frames did not go through `bin/collect-captures`.

**The cheapest test**: nine static frames with the camera moved over
the disc centre. If the marker sizes come back within 10 % of each
other, the geometry is fixed and the plane follows.
