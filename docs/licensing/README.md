# Licensing evidence

Dated copies of third-party terms, kept because vendor pages change and
what governs is the version in force when the files were made.

| file | what | retrieved |
|---|---|---|
| [calibrx-terms-2026-09-21.txt](calibrx-terms-2026-09-21.txt) | CalibrX terms and conditions, text extract | 2026-09-21 |
| [calibrx-pricing-2026-09-21.png](calibrx-pricing-2026-09-21.png) | CalibrX pricing and licence tiers | 2026-09-21 |

Conclusions drawn from these live in [../../LICENSES.md](../../LICENSES.md).
Nothing here is legal advice.

**These two files are CalibrX's own content**, quoted for record-
keeping. The CC-BY-SA-4.0 grant covering the rest of `docs/` stops at
this directory.

**Three questions are with `support@calibrx.io`, sent 2026-09-21** —
redistribution under an open licence, the `calibrx.io` trademark on
redistributed boards, and a suggestion that they support anisotropic
targets. Everything concluded below and in `LICENSES.md` is our
cautious reading pending their reply, not their position.

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

### Credits

5 per project, 1 per detection, 5 per camera model solved, uploads
free. The v4k_01 calibration cost about 11 credits of a 1000/month
allowance.

Worth noting for planning: **our own OpenCV pipeline consumes no
credits at all.** `anisotropy_scan.py` and `make_calibration.py` run
locally, so refitting the same frames a dozen ways — which is how the
board anisotropy was found — costs nothing. CalibrX is the independent
cross-check, not the working tool.

### One thing the pricing page does not settle

"Usable across your team" scopes **who may operate the service**, not
what may be done with files already owned. Redistribution rights come
from the terms' §4/§5 ownership grant, and ownership is not seat-
limited. The two statements answer different questions and do not
conflict — but if that reading ever mattered commercially, it is the
sentence to put to CalibrX directly.
