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
| `calibrx-reply-2026-09-21.eml` | Nassim Hammami / CalibrX | email to the operator, `Re: Accounts, a legal question, and a technical feature request` | 2026-09-21 | saved from the operator's mailbox, headers and body unaltered; the thread carries his reply and the questions it answers |
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

## Answered by CalibrX — asked 2026-09-21, replied the same day

Nassim Hammami, founder of CalibrX, answered all three items. His
reply is `calibrx-reply-2026-09-21.eml` in this directory, so the
wording below can be checked against the source rather than trusted.

1. **Redistribution.** Yes — and he goes further than the terms had
   to: *"I don't claim ownership of the underlying ChArUco pattern; my
   contribution through CalibrX is to make camera calibration
   accessible through a quick, clear workflow."* Our reading of the
   §4/§5 ownership split was right.
2. **Trademark.** *"You're welcome to publish them with the CalibrX
   branding intact or remove it — either is fine with me. An
   acknowledgment in your documentation is appreciated but not
   required."* The conservative rule adopted here without his input —
   strip the mark from modified boards — is withdrawn. We keep the
   boards as generated and credit CalibrX in
   [../calibrating-a-camera.md](../calibrating-a-camera.md).
3. **Anisotropic targets** *(a suggestion).* Accepted.

The permission to carry their branding rests on this message rather
than on anything CalibrX has published, which is why it is archived
here beside the terms.

He titles himself **founder**, not CEO, in both the body and the
signature block.
