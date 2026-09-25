---
name: analyse-rig-question
description: Analyse a rig, optics, metrology or registration question for this project and record the answer as a finding — ground it in measured values from the repo, quantify it against the project's own error budget, write it into docs/planning/, commit, and report the disposition. Use this whenever the operator asks whether a rig change is worth doing, why a measurement is off, whether some target / landmark / lens / paper / disc arrangement would work, or any "can we", "should we", "is it enough", "why is this off" question about the camera, pegs, sheet, ChArUco targets, punch, or registration accuracy. Use it even when the question reads as idle curiosity or is phrased in one line, because the answer is a finding and findings get recorded rather than left in a chat log.
---

# Analysing a rig question

The answer to one of these questions is a **finding**, and a finding
that lives only in a chat log gets re-derived from scratch in a month —
usually less carefully, because the numbers that made it true were in
the transcript and the transcript is gone. This project's `docs/planning/`
is the record, its commit messages are the record's index, and the
operator's standing rule is that every finding gets a stated disposition.
So the deliverable is never just the answer in chat: it is the answer,
the doc, the commit, and the disposition.

The whole procedure is five steps, and the first one is where the value is.

## 1. Ground it in measured numbers, never nominal ones

**The most expensive bug in this project's history was a nominal value
that was never measured.** `centre_spacing_mm` sat at "4 inches exactly"
while the real bar was 1.54 % over, and because it set the scale it
doubled the peg residual on every frame in the corpus. The same shape of
error is waiting in every printed target, every paper dimension, and
every quantity that arrived as a specification rather than as a reading.

So before reasoning: find out what has actually been measured, and what
has only been assumed. `references/rig-constants.md` is a map of where
each class of number lives — read it rather than trusting any value
quoted in this file or recalled from a previous session, because these
values move (the peg spacing went through three values in one day).

Two habits that make the difference:

* **Say which is which.** When a number enters the analysis, mark it
  measured (and with what — 95 flatbed scans, 48 ChArUco frames, six
  caliper readings) or nominal. A conclusion resting on a nominal value
  is a conclusion with an unexploded charge under it, and saying so is
  what lets the operator go measure it.
* **Check whether an existing doc already answers this — and whether its
  premises still hold.** Retracting our own earlier conclusion is a
  first-class outcome here, not an embarrassment; `pose-from-pnp.md`'s
  "the premise has failed" and the retraction of the 4.0624 inch bar are
  both load-bearing history. What usually rots is not the arithmetic but
  the model: a Monte Carlo that added symmetric noise could not represent
  a *bias*, so it answered a question nobody had asked once the sheet
  turned out not to be flat. Ask what class of error the earlier work
  modelled before reusing its conclusion.

## 2. Quantify it against the project's own error budget

An answer of the form "that would help" is not usable. An answer of the
form "that removes 3 to 12 mm and costs 0.086 mm, against a 0.804 mm
threshold" is, and the difference is one short calculation.

Write the formula down, evaluate it at this rig's constants, and put the
result in a table next to the threshold. The threshold is derived, not
chosen: **3 × the measured punch tolerance**, because no real sheet can
beat its own punch. Reach for the mechanisms the project has already
established rather than inventing new ones — out-of-plane error projects
as `h·tanθ`, parallax as `r·h/Z`, and a chord across a curved span sags
by `s²/8R`. Most rig questions are one of those three in a new costume,
and using the established form makes the new result comparable with
every number already in the docs.

Run the arithmetic in a scratch script rather than in your head; a
transposed digit in a table that becomes the record is expensive, and
the script costs nothing. Then say plainly which figures are measured on
the rig and which are a formula evaluated at the rig's constants — the
`## Status` section exists for exactly this.

## 3. Decide where the finding goes

* **A new question gets a new doc**, `docs/planning/<topic>.md`.
* **A question that revises an existing conclusion gets a dated section
  appended to that doc**, `# Revisited YYYY-MM-DD: <what changed>` after
  a `---`. Do not edit the earlier text to make it look right. Mark the
  superseded passage in place (`**Superseded reading below.**`, or a
  `### Superseded:` heading) and leave the reasoning that failed
  visible, because knowing *how* a conclusion went wrong is what stops
  the next one going wrong the same way.
* **A finding that supersedes a test or a design decision says so by
  name**, the way `crown_test.py`'s docstring names the assertion it
  removes. Grep for what else asserts the old conclusion; a doc that
  contradicts a passing test is a trap.

## 4. Write it in the house voice

See `references/house-style.md` for the template and a worked example.
The short version: the title is the finding, not the topic; headings are
claims; every number carries its provenance; the verdict goes at the top;
and the doc ends with a `## Status` section separating what is measured
from what is computed.

## 5. Commit, then state the disposition

**Docs only.** If the analysis implies a code change, that is a separate
TDD cycle under this project's rules — failing test first, human
confirmation, commit, then implementation — and it does not ride along
in the doc commit. Recommending the change is part of the finding;
making it is the next piece of work.

The commit message is part of the record, not a pointer to it. First
line is the finding as a declarative sentence. Body is prose paragraphs,
one per finding, each carrying its numbers inline, in the form the
project already uses: *"Records that ..."*, *"Also notes that ..."*.
Someone reading `git log` should get the findings without opening the
doc. End with the session's `Co-Authored-By` line.

Then report the disposition in chat, per the operator's rule: what was
recorded (the class or identifier), where (file and section), and the
commit — a hash alone is not a disposition. Cover everything reported in
that response, and name anything you chose *not* to record with the
reason. "No code changed, so no tests were added or run" is a legitimate
and useful disposition line for an analysis-only commit.

## Failure modes worth naming

* **Answering from memory.** These questions are all about a specific
  rig whose numbers are in the repo and change. Read them.
* **Letting a thing report on itself.** The outline residual could not
  measure the sheet's curl while the outline also defined the plane. If
  the evidence for a quantity is the same artefact that was fitted to
  produce it, the finding is that you need an independent measurement.
* **Hedging instead of concluding.** The operator asks these questions to
  decide something. Give the verdict, then the caveats, then what would
  test it cheapest — the `## Status` section's last job is to name the
  one experiment that would settle it.
