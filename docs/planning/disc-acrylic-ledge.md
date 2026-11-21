# The disc's acrylic ledges are boxed in by the N target and the bar's inserts, not by the 12 x 12 stock

*Record, 2026-11-20. Short version: **the inherited 3/8 in ledges had no
reason; the free room makes them 12.3 mm north and 10.7 mm south, with the
acrylic 9 29/32 in tall and off-centre*** — geometry from the SCAD, not
measured on a built disc.

## Nothing set the 3/8 in ledge

The Gemini-generated disc (c93c0ee) cut the acrylic to 12 x 9 3/4 in, which
leaves 3/8 in over the 9 in opening at each end. Neither the SCAD nor the
build guide nor the commit history gives a reason. Only the 12 in width is
forced: the stock is 12 in and the opening is 12 in, so there is no ledge
east or west. Height-wise the 12 in stock would allow 1 1/2 in per side.

The ledge matters because the #6-32 window inserts sit centred on it, 3/16 in
from the opening. A 3/16 in pilot then leaves 2.4 mm of wood to the opening,
which is a split-out risk; see 67a2d88.

## What actually bounds it

| side | bound | largest ledge | insert centre to opening | wood beside a 3/16 in pilot |
|---|---|---:|---:|---:|
| as received | none | 9.53 mm | 4.76 mm | 2.38 mm |
| north | recess stops 3 mm before the N ChArUco target (its edge is 3 mm past the sheet's far edge, at +5.118 in) | 12.30 mm | 6.15 mm | 3.77 mm |
| south | 3 mm of wood beside the bar's 4.5 mm M2 insert pockets on the peg line (-5.156 in) | 11.02 mm | 5.51 mm | 3.13 mm |

Adopted: north edge 4 63/64 in (12.30 mm ledge), south edge 4 59/64 in
(10.72 mm ledge, rounded down to a 64th), so the acrylic is 12 x 9 29/32 in,
centred 1/32 in north of the optical centre. The operator accepted the
asymmetry. A piece put back upside down shows itself, because its holes
miss the inserts.

The 3 mm wood margins are choices, not derived quantities. Both are now
`assert`s in `cad/animation_disc_17_5in.scad`, and each was checked to fire
when its edge moves to 5.0 in.

## Two larger options, not taken

* **Move the N target north.** Its outer corner has about 16 mm before the
  round-over. Each millimetre raises the camera height needed to frame the
  sheet and all four targets, already about 423 mm against test_rig02's 340.
* **Run the acrylic under the whole bar.** That gives a 28 mm south ledge,
  and the bar's screws would clamp the window through it. The channel would
  then be cut entirely in acrylic, which floats up to 0.4 mm per side in its
  recess. That puts the registration reference on a part that moves each
  time it is reinstalled. It would also leave 1.5 mm between the recess and
  both the bar's edge and the S target.

## Status

Nothing here is measured on a built disc. The geometry is the SCAD's, and
the bounds depend on two placements that are design choices: the N target's
3 mm gap to the sheet, and the bar's insert pockets. The knife insert's
outside diameter is still unmeasured, so the wall left beside the insert
itself, as opposed to beside its pilot, is unknown. Calipering one insert
settles it.
