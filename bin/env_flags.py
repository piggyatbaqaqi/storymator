"""Let the environment supply argparse defaults: CLI, then environment.

Every optional flag on a parser reads ``<PREFIX>_<DEST>`` when it is not
given on the command line, so a flag added later is covered without
anyone remembering to.  See docs/bin-argparse-strict.md.

    parser = build_parser()
    apply_env(parser, "MEASURE_INK", exempt={"peg"})

Whatever can't sensibly take one value from a shell must be named in
``exempt``.  A repeatable flag is the usual case: argparse appends to its
default, so a value from the environment would be added to by the command
line rather than replaced by it.  ``apply_env`` raises on those instead
of skipping them, so that leaving one out is a decision somebody made.

This walks ``parser._actions``, which is private to argparse but has been
stable for as long as argparse has existed.
"""

from __future__ import annotations

import argparse
import os
from typing import Any, Callable, Collection, Iterator

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}
_BAD_VALUE = (ValueError, TypeError, argparse.ArgumentTypeError)


class _EnvText(str):
    """A default that came from the environment, so errors can say so."""


def _options(parser: argparse.ArgumentParser
             ) -> Iterator[tuple[argparse.ArgumentParser, argparse.Action]]:
    """Each optional flag and the parser owning it, subcommands included."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for sub in {id(p): p for p in action.choices.values()}.values():
                yield from _options(sub)
        elif (action.option_strings and not isinstance(
                action, (argparse._HelpAction, argparse._VersionAction))):
            yield parser, action


def _converter(action: argparse.Action, variable: str) -> Callable[[str], Any]:
    """The flag's own type, reporting environment values by variable.

    argparse only converts a string default when the flag was not given,
    so a bad value in the environment is never read if the command line
    overrides it.  argparse does not check a default against ``choices``,
    so that happens here.
    """
    original: Any = action.type

    def convert(text: str) -> Any:
        if not isinstance(text, _EnvText):
            return text if original is None else original(text)
        plain = str(text)
        try:
            value = plain if original is None else original(plain)
        except _BAD_VALUE as exc:
            raise argparse.ArgumentTypeError(
                f"{variable}={plain!r}: {exc}") from None
        if action.choices is not None and value not in action.choices:
            raise argparse.ArgumentTypeError(
                f"{variable}={plain!r}: not one of "
                f"{', '.join(map(str, action.choices))}")
        return value

    return convert


def apply_env(parser: argparse.ArgumentParser, prefix: str,
              exempt: Collection[str] = ()) -> None:
    """Point each optional flag's default at its environment variable."""
    options = list(_options(parser))
    unknown = set(exempt) - {action.dest for _, action in options}
    if unknown:
        raise ValueError(f"exempt names no such flag: {sorted(unknown)}")

    for owner, action in options:
        if action.dest in exempt:
            continue
        is_bool = isinstance(action, argparse._StoreTrueAction)
        is_plain = (type(action) is argparse._StoreAction
                    and action.nargs is None)
        if not (is_bool or is_plain):
            raise ValueError(
                f"{action.option_strings[0]} can't take one value from the "
                "environment; name it in exempt")

        variable = f"{prefix}_{action.dest.upper()}"
        text = os.environ.get(variable, "")
        if not text:
            continue
        action.required = False
        if is_bool:
            word = text.lower()
            if word not in _TRUE | _FALSE:
                owner.error(f"{variable}={text!r}: not a yes or a no")
            action.default = word in _TRUE
        else:
            action.type = _converter(action, variable)
            action.default = _EnvText(text)
