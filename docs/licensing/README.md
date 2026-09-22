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

## Answered by CalibrX — asked 2026-09-21, replied 2026-09-22

Nassim Hammami, CEO of CalibrX, answered all three items.

1. **Redistribution.** Yes. The generated targets may be distributed.
   Our reading of the §4/§5 ownership split was right.
2. **Trademark.** The targets may carry calibrx.io branding **or
   not** — our choice — and a mention in our documentation is
   *welcome but not required*. The conservative rule we had adopted
   without their input, strip the mark from modified boards, is
   withdrawn. We keep the boards as generated and credit CalibrX in
   the documentation.
3. **Anisotropic targets** *(a suggestion).* Accepted. Support is
   planned for the next few days. Their format currently carries one
   `square_size` and no second axis, so a print whose x and y scales
   differ cannot be described; ours differs by **+0.15 %**, which
   their own fit pushes into fx/fy as a 0.104 % discrepancy — see
   [../../data/calibration/distortion/v4k_01/calibrx/README.md](../../data/calibration/distortion/v4k_01/calibrx/README.md).
   Worth re-checking the format when it ships.

### Where the permission lives

This reply is an email to the operator, not an amendment to the
published terms, and it is not in this directory. The dated copies
here cover what CalibrX published; the permission to redistribute
their branding rests on that message alone. Archiving it beside
`calibrx-terms-2026-09-21.txt` would put the whole record in one
place.
