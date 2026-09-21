# Licensing evidence

Dated copies of third-party material, kept because vendor pages change
and what governs is the version in force when our files were made.

**Documents in this directory belong to their respective owners**, as
listed below. The CC-BY-SA-4.0 grant covering the rest of `docs/` does
not extend here.

## Provenance

| file | owner | source | retrieved | how |
|---|---|---|---|---|
| `calibrx-terms-2026-09-21.txt` | CalibrX | `https://calibrx.io/terms-and-conditions` | 2026-09-21 | fetched with `curl`; plain text extracted from the served HTML, tags stripped, wording unaltered |
| `calibrx-pricing-2026-09-21.png` | CalibrX | `https://calibrx.io/#pricing` | 2026-09-21 | screenshot taken by the operator |
| `README.md` *(this file)* | storymator | — | — | ours; **CC-BY-SA-4.0** |

Conclusions drawn from this material live in
[../../LICENSES.md](../../LICENSES.md). Nothing here is legal advice.

## CalibrX tiers, as published 2026-09-21

| | price | scope | credits |
|---|---|---|---|
| Free | $0 | "See it work" | 50 to start |
| Research & Development | $49 lifetime | "Internal work" — **"Not for calibrating products you sell."** | 300/month for life |
| **Commercial** *(the licence held)* | $149 lifetime | "Products for sale" — **"Full rights, usable across your team."** | 1000/month for life |

**The R&D tier would not have covered this project.** "Not for
calibrating products you sell" is explicit, and selling calibrated
cameras is exactly that — so the earlier idea that R&D might serve if
the rig were offered as a DIY system is closed off by the tier's own
wording. Commercial is the correct tier and is the one held.

## Credits

5 per project, 1 per detection, 5 per camera model solved; uploads
free. The v4k_01 calibration cost about 11 credits of a 1000/month
allowance.

Worth noting for planning: **our own OpenCV pipeline consumes no
credits at all.** `anisotropy_scan.py` and `make_calibration.py` run
locally, so refitting the same frames a dozen ways — which is how the
board anisotropy was found — costs nothing. CalibrX is the independent
cross-check, not the working tool.

## Open with CalibrX — asked 2026-09-21

Three items are with `support@calibrx.io`. The guidance in
`LICENSES.md` is our reading pending their reply, not their position.

1. **Redistribution.** Whether the §4/§5 ownership grant is understood
   as permitting generated output to be released under an open licence.
2. **Trademark.** Whether the `calibrx.io` mark may stay on
   redistributed boards, and what they want on modified ones. Our
   current rule — strip it from modified boards, keep it on unmodified
   — is a default chosen without their input.
3. **Anisotropic targets** *(a suggestion).* Their format carries one
   `square_size` and no second axis, so a print whose x and y scales
   differ cannot be described. Ours differs by **+0.15 %**, which their
   own fit pushes into fx/fy as a 0.104 % discrepancy — see
   [../../data/calibration/distortion/v4k_01/calibrx/README.md](../../data/calibration/distortion/v4k_01/calibrx/README.md).

A reply affects three files: `LICENSES.md`,
`data/calibration/targets/README.md`, and this one.
