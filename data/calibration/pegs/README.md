# ACME peg bars

One directory per physical bar. Everything measured here — peg
diameters, heights, dome geometry, clearance — is a property of *that
bar* and does not transfer to another, so a new bar gets a new
directory and its own pass through
[../../../docs/measuring-punch-tolerance.md](../../../docs/measuring-punch-tolerance.md)
part C.

| bar | model | where |
|---|---|---|
| [honbay_0001](honbay_0001/) | Honbay stainless comic/animation peg bar | Monte's office desk, Ashland Haus |

Camera captures of a bar live with the **camera that took them**, under
`../distortion/<camera>/`, because focus and intrinsics are part of
what those frames mean. For honbay_0001 that is
[../distortion/v4k_01/](../distortion/v4k_01/) — `bar_reference.jpg`
and `peg_profile-*.jpg`.

Paper is measured separately, in [../paper/](../paper/): the punch
belongs to the ream, not to the bar.


## The geometry is stored in the wrong place

A bar's measurements are written up here, but the numbers the code
actually reads live in `data/calibration/distortion/v4k_01/*.json` —
a directory named after a **camera**. Three of them, each carrying its
own copy of the same `peg` block.

So measuring the bar means editing three files that have nothing to do
with the bar, and this directory, which is named after the bar, holds
no machine-readable record at all. Correcting the centre spacing on
2026-09-25 touched all three.

The bar and the camera are independent pieces of hardware: either can
be replaced without the other. A `honbay_0001.json` here, referenced
by the camera calibrations rather than copied into them, would put
each measurement in one place and make "which bar was this shot with?"
a question the file can answer.

Not done yet, because it changes the calibration file format and
`Calibration.from_dict` with it.
