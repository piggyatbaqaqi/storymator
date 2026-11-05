# Argparse strict mode for `bin/` and `fixes/` scripts

**Status: in force.** No storymator CLI in `bin/` has ever used
`parse_known_args()`. This document records the rule, why it exists, and
what is still outstanding.

## Problem

`parse_known_args()` silently swallows unknown flags instead of raising
`SystemExit`. This was learned in skol, where it bit at least twice:

- `bin/embed_treatments.py --doc-id <id> --force` silently dropped
  `--doc-id <id>` and ran a ~50 min full-database encoding (the expected
  single-doc mode didn't exist; the script accepted the typo).
- A `--rate-limit-max_ms` typo (underscore vs. dash) and a no-op
  `--skip-existing` were both swallowed without complaint.

The common shape: someone (operator or AI writing a runbook) believes a
flag does something, the script accepts it without protest, and the
behavior is the *default* — usually a long, expensive operation.

Hand-rolled argument handling has the same failure. Testing
`"--dry-run" in argv` means `--dry-rn` runs for real, which matters most
in a tool that removes things. So the rule is to use argparse, strictly.

## Design: one strict parser per script

Each script builds its parser in a function and parses once, inside a
`main(argv)` that tests can call:

```python
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--script-specific-flag', ...)
    return ap


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)     # strict
    ...
```

An unknown flag is rejected with `error: unrecognized arguments` and exit
code 2.

### Shared flags

There is no shared parser yet, because the tools share nothing worth one:
the only flag appearing in two of them is `--out`. When a second real
shared flag appears, hold the shared flags in an
`ArgumentParser(add_help=False)` and pass it through `parents=`, which is
how skol's `common_parser()` works.

A flag used by only one command does **not** belong in a shared parser,
however general its name sounds.

## Parameter priority

Each parameter resolves in this order:

1. CLI `--<parameter>`
2. Environment variable `<PREFIX>_<PARAMETER>`
3. Config file, if the tool has one
4. Hardcoded default

`<PREFIX>` names the tool or subsystem, so that a generic parameter name
cannot collide in a shared shell: `COLOUR_DROPOUT_WHITE_LEVEL`,
`BIG_GREEN_BUTTON_<NAME>`, `STORYMATOR_BACKUP_KEEP`, `COMFYUI_TEMP`.

Tools get the environment layer from `bin/env_flags.py`, one call at the
end of `build_parser()`:

```python
apply_env(ap, "MEASURE_INK", exempt={"peg"})
```

Every optional flag then reads `<PREFIX>_<DEST>`, so a flag added later
is covered without anyone remembering to. A bad value exits 2 and names
the variable; an empty one counts as unset. Booleans read
`1/true/yes/on` and `0/false/no/off`. Positional arguments have no
variable.

### Exemptions

`apply_env` raises on a repeatable flag unless it is exempted by name, so
leaving a flag out is always a decision somebody made:

| Flag | Why |
|---|---|
| `measure-ink --peg`, `collect-captures --kind` | Repeatable: argparse appends to its default, so the command line could not replace the environment's value |
| `collect-captures --dry-run`, `--allow-duplicates`, `colour-dropout --overwrite` | Safety switches, which should be typed where they can be seen |
| `collect-captures --note`, `--frame-note` | Data labels: a stale variable would silently mislabel new captures |
| `measure-punch-tolerance --self-test` | Picks what the tool does: a stale variable would skip the real work |
| `collect-captures --temp`, `--out` | Already read `COMFYUI_TEMP` and `CAPTURE_CORPUS` |
| `colour-dropout --dropped` | An output path for one run |

`fixes/prune-duplicate-captures` has no environment layer at all. It is a
one-off, and its only flag is a safety switch.

## The passthrough escape hatch

A script that genuinely forwards extras (e.g. a subprocess orchestrator)
keeps `parse_known_args()` and marks it:

```python
# pragma: argparse-passthrough -- <why this one can't be strict>
args, extras = parser.parse_known_args(main_argv)
```

Current holders: none.

Keep the wording exactly `argparse-passthrough` — the hygiene test keys
on it.

## Enforcement

`bin/argparse_strict_test.py` has three guards over every Python tool in
`bin/` and `fixes/`. Tools are extensionless and hyphenated, so they are
found by shebang; bash tools and `*_test.py` are left out.

- **static** — AST-walks each tool: any `parse_known_args` *call*
  (comments ignored) without the pragma fails, and so does a tool that
  never calls argparse at all.
- **environment** — each tool must call `apply_env`, except
  `fixes/prune-duplicate-captures`.
- **behavioral** — launches each tool with a bogus flag and asserts exit
  2. It first confirms statically that the tool parses with argparse,
  because a lenient tool handed a bogus flag runs for real. Timeouts and
  missing imports fail rather than skip: a guard that quietly stops
  checking is worse than a red test.

Bash tools reject unknown options by hand, with a catch-all in their
argument loop, as `bin/backup-storymator` does.

## Out of scope

- Migrating to click / typer / fire. `parse_args()` does the job.
- Auto-suggesting "did you mean --X?" — argparse doesn't do this
  natively; nice-to-have, not required.
