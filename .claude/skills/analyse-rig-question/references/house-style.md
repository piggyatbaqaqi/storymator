# House style for a planning doc

The style is not decoration. Each convention below exists because the
docs get read months later by someone deciding whether to trust them.

## The template

```markdown
# <The finding, as a declarative sentence>

*<Kind>, YYYY-MM-DD. Short version: **<the verdict>** — measured, not
argued.*

## <A claim, not a label>

<Prose. Bold lead-in for the load-bearing sentence.>

| | measured | model |
|---|---:|---:|
| <quantity> | <value> | <value> |

## What follows

<What the operator should do, in priority order.>

## Status

<What is measured on this rig and what is a formula evaluated at its
constants. Then the cheapest experiment that would settle it.>
```

## The conventions, and why

* **The title is the finding, not the topic.** "The centroid throws away
  most of what a peg landmark tells you", not "Centroid analysis". The
  title is what shows up in a directory listing a year later, and a
  topic tells the reader nothing about whether to open it.
* **The italic line carries kind, date and verdict.** Kind is one of
  *feasibility*, *operator's observation*, *proposal*, *record*, or
  *analysis only* — it tells the reader immediately whether anything was
  built. Dates are absolute, never "last week".
* **Headings are claims.** "Two 2 x 2 boards is not enough" beats
  "Board sizing". A reader skimming headings should get the argument.
* **The verdict goes at the top.** The operator is deciding something.
* **Every number carries its provenance** — 95 flatbed scans, 48 ChArUco
  frames, six caliper readings, or "nominal, never measured", which is
  the most important provenance of all.
* **Measured-versus-model tables**, with the difference as its own row
  when the difference is the point.
* **Prohibitions get their reason inline.** "Never measure the printed
  50 mm bar" is followed by the serifs being worth 2.22 % on a quantity
  worth 1.27 %. A rule without its reason gets overridden by the next
  person who has a good idea.
* **Superseded text stays, marked.** `**Superseded reading below.**` or a
  `### Superseded:` heading. How a conclusion failed is what stops the
  next one failing the same way. Revisions append
  `# Revisited YYYY-MM-DD: <what changed>` after a `---`.
* **A `## Status` section that separates measured from computed**, and
  names the cheapest experiment that would settle the question. An
  analysis doc that does not say "nothing here is measured on this rig"
  will eventually be read as if it were.

## The commit message

The message is part of the record, not a pointer to it — `git log`
should yield the findings without opening the doc.

```
<The finding, as a declarative sentence — same claim as the title>

<Paragraph establishing what was asked and what the answer is, with
the numbers inline.>

Records that <finding>, <because ... with numbers>.

Records that <finding>. <The generalisable lesson, if there is one.>

Also: <the smaller findings, in one paragraph, semicolon-separated.>

Co-Authored-By: <the session's co-author line>
```

Prose paragraphs, not bullet lists. One finding per paragraph. Numbers
inline. If a finding retracts something, the retraction is the lede.

## Worked examples in the repository

Read these rather than working from the template alone:

* `git log -1 --format=%B f274fc7` — a retraction, and the model of how
  to say "the premise has failed".
* `git log -1 --format=%B 94a9475` — a feasibility answer that ends in a
  recommendation plus three separable smaller findings.
* `docs/planning/pose-from-pnp.md` — a doc with a revisited section
  appended rather than edited over.
* `docs/planning/sheet-flattening.md` — a doc written to this template
  from a one-line question.
