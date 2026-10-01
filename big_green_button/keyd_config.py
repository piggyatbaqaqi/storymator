"""Parse, render and validate the keyd config that owns the button.

keyd reports a bad key name or a malformed device id as a line in the
journal and then carries on with a partly-applied keymap.  For a config
whose whole job is to stop a key reaching the keyboard stream, that
fails in the dangerous direction: the button keeps typing Return and
nothing says so.  This module turns those mistakes into test failures.

``validate`` encodes this project's rules, not keyd's -- a wildcard
``[ids]`` section is legal keyd and rejected here, because on this
laptop it would also claim the internal keyboard.

The keyd dialect parsed here is the subset the button needs: an
``[ids]`` section of device ids, then layer sections of ``key =
action`` lines.  Layer options, ``[global]`` and the modifier
shorthands are preserved verbatim as bindings rather than interpreted.
"""

from __future__ import annotations

import re
import shlex
import stat
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Iterable, Mapping, Sequence

#: Action forms keyd accepts on the right of ``=``.  Anything else must
#: be a bare key name.
ACTIONS: Final[frozenset[str]] = frozenset({
    "clear", "clearm", "command", "layer", "layerm", "macro", "noop",
    "oneshot", "oneshotm", "overload", "overloadt", "overloadt2",
    "swap", "swapm", "timeout", "toggle", "togglem",
})

#: ``k:``/``m:`` restrict an id to keyboards or mice; bare matches both.
ID_KINDS: Final[frozenset[str]] = frozenset({"", "k", "m"})

_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:(?P<kind>[km]):)?(?P<vendor>[0-9a-fA-F]{4})"
    r":(?P<product>[0-9a-fA-F]{4})(?::(?P<hash>[0-9a-fA-F]+))?$")
_SECTION_RE: Final[re.Pattern[str]] = re.compile(r"^\[(?P<name>[^]]+)\]$")
_ACTION_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<name>[a-z0-9_]+)\((?P<arg>.*)\)$")


class ConfigError(ValueError):
    """The text is not a keyd config we can read."""


@dataclass(frozen=True)
class DeviceId:
    """One line of an ``[ids]`` section."""

    vendor: str
    product: str
    kind: str = ""
    hash: str = ""

    @classmethod
    def parse(cls, text: str) -> "DeviceId":
        """Parse ``8089:0019``, ``k:8089:0019`` or the 3-part monitor form."""
        match = _ID_RE.match(text.strip())
        if match is None:
            raise ConfigError(f"not a keyd device id: {text.strip()!r}")
        return cls(vendor=match.group("vendor").lower(),
                   product=match.group("product").lower(),
                   kind=match.group("kind") or "",
                   hash=(match.group("hash") or "").lower())

    def __str__(self) -> str:
        """Render back to the form keyd reads."""
        prefix = f"{self.kind}:" if self.kind else ""
        suffix = f":{self.hash}" if self.hash else ""
        return f"{prefix}{self.vendor}:{self.product}{suffix}"

    def matches(self, vendor: str, product: str,
                *, is_keyboard: bool) -> bool:
        """True when this id selects that device, honouring ``k:``/``m:``.

        The monitor's third component is ignored: we never learn an
        attached device's hash, so narrowing on it could only produce
        false negatives.
        """
        if (self.vendor, self.product) != (vendor.lower(), product.lower()):
            return False
        if self.kind == "k":
            return is_keyboard
        if self.kind == "m":
            return not is_keyboard
        return True


@dataclass(frozen=True)
class Binding:
    """One ``key = action`` line of a layer."""

    key: str
    action: str

    @property
    def action_name(self) -> str | None:
        """``command`` for ``command(...)``; None for a bare key name."""
        match = _ACTION_RE.match(self.action)
        return match.group("name") if match else None

    @property
    def action_arg(self) -> str | None:
        """The text inside the parentheses, or None for a bare key name."""
        match = _ACTION_RE.match(self.action)
        return match.group("arg") if match else None


def _program(command: str) -> str:
    """The program a ``command(...)`` argument would run."""
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    return words[0] if words else ""


@dataclass(frozen=True)
class KeydConfig:
    """A parsed keyd config file."""

    ids: tuple[DeviceId, ...] = field(default_factory=tuple)
    excluded: tuple[DeviceId, ...] = field(default_factory=tuple)
    wildcard: bool = False
    layers: Mapping[str, tuple[Binding, ...]] = field(default_factory=dict)

    def claims(self, vendor: str, product: str,
               *, is_keyboard: bool) -> bool:
        """True when keyd would manage that device under this config."""
        if any(i.matches(vendor, product, is_keyboard=is_keyboard)
               for i in self.ids):
            return True
        if not self.wildcard or not is_keyboard:
            # keyd's manual: the wildcard matches keyboards only.
            return False
        return not any(e.matches(vendor, product, is_keyboard=is_keyboard)
                       for e in self.excluded)

    def bindings(self, layer: str = "main") -> tuple[Binding, ...]:
        """The bindings of one layer, or () if it has none."""
        return self.layers.get(layer, ())

    def hook_paths(self) -> tuple[str, ...]:
        """Every program ``command(...)`` would run, once each, in order."""
        seen: list[str] = []
        for bindings in self.layers.values():
            for binding in bindings:
                if binding.action_name != "command":
                    continue
                program = _program(binding.action_arg or "")
                if program and program not in seen:
                    seen.append(program)
        return tuple(seen)


def parse(text: str) -> KeydConfig:
    """Parse a keyd config.

    Raises ConfigError when the file does not begin with ``[ids]``, when
    a line falls outside any section, or when a line is neither a
    comment, a section header, an id nor ``key = action``.
    """
    ids: list[DeviceId] = []
    excluded: list[DeviceId] = []
    wildcard = False
    layers: dict[str, list[Binding]] = {}
    section: str | None = None

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        # keyd ignores lines that BEGIN with a hash, and only those.
        if not line or line.startswith("#"):
            continue

        if line.startswith("[") or line.endswith("]"):
            match = _SECTION_RE.match(line)
            if match is None:
                raise ConfigError(
                    f"line {number}: not a section header: {line!r}")
            name = match.group("name").strip()
            if section is None and name != "ids":
                raise ConfigError(
                    f"line {number}: a keyd config must begin with [ids], "
                    f"not [{name}]")
            section = name
            if name != "ids":
                layers.setdefault(name, [])
            continue

        if section is None:
            raise ConfigError(
                f"line {number}: {line!r} comes before any section; a keyd "
                "config must begin with [ids]")

        if section == "ids":
            if line == "*":
                wildcard = True
            elif line.startswith("-"):
                excluded.append(DeviceId.parse(line[1:]))
            else:
                ids.append(DeviceId.parse(line))
            continue

        if "=" not in line:
            raise ConfigError(
                f"line {number}: not a binding: {line!r}")
        key, action = line.split("=", 1)
        layers[section].append(Binding(key.strip(), action.strip()))

    if section is None:
        raise ConfigError("empty config: a keyd config must begin with [ids]")

    return KeydConfig(
        ids=tuple(ids), excluded=tuple(excluded), wildcard=wildcard,
        layers={name: tuple(bs) for name, bs in layers.items()})


def render(ids: Sequence[DeviceId | str], bindings: Sequence[Binding],
           *, layer: str = "main", header: str = "") -> str:
    """Render a config that ``parse`` round-trips.

    ``header`` is emitted as ``#`` comment lines above ``[ids]``.
    """
    out: list[str] = []
    if header:
        out.extend(f"# {line}" if line else "#"
                   for line in header.splitlines())
    out.append("[ids]")
    out.append("")
    out.extend(str(i) for i in ids)
    out.append("")
    out.append(f"[{layer}]")
    out.append("")
    out.extend(f"{b.key} = {b.action}" for b in bindings)
    return "\n".join(out) + "\n"


def key_names(keyd: str = "keyd.rvaiya") -> frozenset[str]:
    """Ask the installed keyd for its key names, falling back to KEY_NAMES.

    The vendored set is what this machine's keyd 2.5.0 reports; asking
    the real binary keeps the check honest if keyd is upgraded.
    """
    try:
        done = subprocess.run([keyd, "list-keys"], capture_output=True,
                              text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return KEY_NAMES
    if done.returncode != 0:
        return KEY_NAMES
    names = {line.strip() for line in done.stdout.splitlines() if line.strip()}
    return frozenset(names) if names else KEY_NAMES


def validate(config: KeydConfig,
             *, known_keys: Iterable[str] | None = None) -> list[str]:
    """Every problem with ``config``, as readable lines; [] means good.

    Uses the vendored key table unless ``known_keys`` is given, so a
    validation never depends on keyd being installed.
    """
    keys = frozenset(known_keys) if known_keys is not None else KEY_NAMES
    problems: list[str] = []

    if not config.ids and not config.wildcard:
        problems.append("[ids] lists no device, so this config claims "
                        "nothing and keyd will ignore it")
    if config.wildcard:
        problems.append(
            "[ids] uses the wildcard '*', which claims every keyboard "
            "including this laptop's internal one; list ids explicitly")

    for layer, bindings in config.layers.items():
        seen: set[str] = set()
        for binding in bindings:
            where = f"[{layer}]"
            if binding.key in seen:
                problems.append(
                    f"{binding.key!r} is bound twice in {where}; keyd keeps "
                    "one of them and does not say which")
            seen.add(binding.key)

            if binding.key not in keys:
                problems.append(
                    f"unknown key name {binding.key!r} in {where}; keyd will "
                    "log it and skip the binding")

            name = binding.action_name
            if name is None:
                if (binding.action not in keys
                        and binding.action not in ACTIONS):
                    problems.append(
                        f"unknown action {binding.action!r} for "
                        f"{binding.key!r} in {where}")
                continue
            if name not in ACTIONS:
                problems.append(
                    f"unknown action {binding.action!r} for "
                    f"{binding.key!r} in {where}")
                continue
            if name == "command":
                program = _program(binding.action_arg or "")
                if not program.startswith("/"):
                    problems.append(
                        f"command path {program!r} for {binding.key!r} in "
                        f"{where} is not absolute; keyd runs it from its own "
                        "working directory")

    return problems


def check_hook_permissions(path: str) -> list[str]:
    """Problems with a ``command(...)`` target, which keyd runs as root.

    A hook that is writable by group or other, or that lives in a
    directory writable by group or other, is a local root escalation.
    A sticky directory is exempt: sticky is what stops another user
    replacing a file they do not own.
    """
    problems: list[str] = []
    target = Path(path)
    try:
        info = target.stat()
    except OSError:
        return [f"{path} does not exist"]

    if not info.st_mode & stat.S_IXUSR:
        problems.append(f"{path} is not executable")
    if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        problems.append(
            f"{path} is writable by group or other "
            f"(mode {stat.S_IMODE(info.st_mode):04o}); keyd runs it as root")
    if info.st_uid != 0:
        problems.append(
            f"{path} is owned by uid {info.st_uid}, not root; "
            "keyd runs it as root")

    for parent in target.resolve().parents:
        try:
            pinfo = parent.stat()
        except OSError:
            continue
        if (pinfo.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
                and not pinfo.st_mode & stat.S_ISVTX):
            problems.append(
                f"the directory {parent} is writable by group or other "
                f"(mode {stat.S_IMODE(pinfo.st_mode):04o}), so {path} can be "
                "replaced by someone who does not own it")

    return problems


def _kinds_overlap(one: str, two: str) -> bool:
    """A bare id selects both interfaces, so it overlaps k: and m: alike."""
    return one == two or "" in (one, two)


def _shared_claim(one: KeydConfig, two: KeydConfig) -> str | None:
    """A device both configs would claim, described, or None."""
    for a in one.ids:
        for b in two.ids:
            if ((a.vendor, a.product) == (b.vendor, b.product)
                    and _kinds_overlap(a.kind, b.kind)):
                return str(a)

    for wild, other in ((one, two), (two, one)):
        if not wild.wildcard:
            continue
        if other.wildcard:
            return "every keyboard"
        for b in other.ids:
            if b.kind == "m":
                continue        # the wildcard matches keyboards only
            if not any(e.matches(b.vendor, b.product, is_keyboard=True)
                       for e in wild.excluded):
                return str(b)
    return None


def find_id_conflicts(configs: Mapping[str, KeydConfig]) -> list[str]:
    """Device ids claimed by more than one config.

    keyd permits an id in only one file and ignores the duplicate, so a
    second config claiming ``8089:0019`` silently wins or loses.
    """
    problems: list[str] = []
    names = sorted(configs)
    for index, first in enumerate(names):
        for second in names[index + 1:]:
            shared = _shared_claim(configs[first], configs[second])
            if shared is not None:
                problems.append(
                    f"{first} and {second} both claim {shared}; keyd allows "
                    "a device id in one file only and ignores the duplicate")
    return problems


#: Key names reported by ``keyd.rvaiya list-keys`` on keyd 2.5.0.
KEY_NAMES: Final[frozenset[str]] = frozenset({
    '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-',
    '.', '/', '0', '1', '102nd', '2', '3', '4', '5', '6', '7', '8', '9',
    ':', ';', '<', '=', '>', '?', '@', 'A', 'B', 'C', 'D', 'E', 'F',
    'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
    'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_', '`',
    'a', 'again', 'apostrophe', 'auto', 'b', 'back', 'backslash',
    'backspace', 'bassboost', 'battery', 'bluetooth', 'bookmarks',
    'brightnessdown', 'brightnessup', 'c', 'calc', 'camera', 'cancel',
    'capslock', 'chat', 'close', 'closecd', 'coffee', 'comma',
    'compose', 'computer', 'config', 'connect', 'copy', 'cut', 'cycle',
    'cyclewindows', 'd', 'dashboard', 'delete', 'deletefile', 'display',
    'documents', 'dot', 'down', 'e', 'edit', 'ejectcd', 'ejectclosecd',
    'email', 'end', 'enter', 'equal', 'esc', 'escape', 'exit', 'f',
    'f1', 'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18',
    'f19', 'f2', 'f20', 'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5',
    'f6', 'f7', 'f8', 'f9', 'fastforward', 'file', 'finance', 'find',
    'fn', 'forward', 'forwardmail', 'front', 'g', 'grave', 'h',
    'hangeul', 'hanja', 'help', 'henkan', 'hiragana', 'home',
    'homepage', 'hp', 'i', 'insert', 'iso', 'iso-level3-shift', 'j',
    'k', 'katakana', 'katakanahiragana', 'kbdillumdown',
    'kbdillumtoggle', 'kbdillumup', 'kp0', 'kp1', 'kp2', 'kp3', 'kp4',
    'kp5', 'kp6', 'kp7', 'kp8', 'kp9', 'kpasterisk', 'kpcomma', 'kpdot',
    'kpenter', 'kpequal', 'kpjpcomma', 'kpleftparen', 'kpminus',
    'kpplus', 'kpplusminus', 'kprightparen', 'kpslash', 'l', 'left',
    'leftalt', 'leftbrace', 'leftcontrol', 'leftmeta', 'leftmouse',
    'leftshift', 'linefeed', 'm', 'macro', 'mail', 'media', 'menu',
    'micmute', 'middlemouse', 'minus', 'mouse1', 'mouse2', 'mouseback',
    'mouseforward', 'move', 'msdos', 'muhenkan', 'mute', 'n', 'new',
    'next', 'nextsong', 'noop', 'numlock', 'o', 'off', 'open', 'p',
    'pagedown', 'pageup', 'paste', 'pause', 'pausecd', 'phone', 'play',
    'playcd', 'playpause', 'power', 'prev', 'previoussong', 'print',
    'prog1', 'prog2', 'prog3', 'prog4', 'props', 'q', 'question', 'r',
    'record', 'redo', 'refresh', 'reply', 'rewind', 'rfkill', 'right',
    'rightalt', 'rightbrace', 'rightcontrol', 'rightmeta', 'rightmouse',
    'rightshift', 'ro', 's', 'save', 'scale', 'scrolllock', 'search',
    'semicolon', 'send', 'sendfile', 'setup', 'shop', 'slash', 'sleep',
    'sound', 'space', 'sport', 'stop', 'stopcd', 'suspend',
    'switchvideomode', 'sysrq', 't', 'tab', 'u', 'undo', 'unknown',
    'up', 'uwb', 'v', 'voicecommand', 'volumedown', 'volumeup', 'w',
    'wakeup', 'wlan', 'wwan', 'www', 'x', 'xfer', 'y', 'yen', 'z',
    'zenkakuhankaku', 'zoom', '{', '|', '}', '~'
})
