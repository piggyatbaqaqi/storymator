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
from dataclasses import dataclass, field
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
        raise NotImplementedError

    def __str__(self) -> str:
        """Render back to the form keyd reads."""
        raise NotImplementedError

    def matches(self, vendor: str, product: str,
                *, is_keyboard: bool) -> bool:
        """True when this id selects that device, honouring ``k:``/``m:``."""
        raise NotImplementedError


@dataclass(frozen=True)
class Binding:
    """One ``key = action`` line of a layer."""

    key: str
    action: str

    @property
    def action_name(self) -> str | None:
        """``command`` for ``command(...)``; None for a bare key name."""
        raise NotImplementedError

    @property
    def action_arg(self) -> str | None:
        """The text inside the parentheses, or None for a bare key name."""
        raise NotImplementedError


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
        raise NotImplementedError

    def bindings(self, layer: str = "main") -> tuple[Binding, ...]:
        """The bindings of one layer, or () if it has none."""
        raise NotImplementedError

    def hook_paths(self) -> tuple[str, ...]:
        """Every program ``command(...)`` would run, in binding order."""
        raise NotImplementedError


def parse(text: str) -> KeydConfig:
    """Parse a keyd config.

    Raises ConfigError when the file does not begin with ``[ids]``, when
    a line falls outside any section, or when a line is neither a
    comment, a section header, an id nor ``key = action``.
    """
    raise NotImplementedError


def render(ids: Sequence[DeviceId | str], bindings: Sequence[Binding],
           *, layer: str = "main", header: str = "") -> str:
    """Render a config that ``parse`` round-trips.

    ``header`` is emitted as ``#`` comment lines above ``[ids]``.
    """
    raise NotImplementedError


def key_names(keyd: str = "keyd.rvaiya") -> frozenset[str]:
    """Ask the installed keyd for its key names, falling back to KEY_NAMES.

    The vendored set is what this machine's keyd 2.5.0 reports; asking
    the real binary keeps the check honest if keyd is upgraded.
    """
    raise NotImplementedError


def validate(config: KeydConfig,
             *, known_keys: Iterable[str] | None = None) -> list[str]:
    """Every problem with ``config``, as readable lines; () means good."""
    raise NotImplementedError


def check_hook_permissions(path: str) -> list[str]:
    """Problems with a ``command(...)`` target, which keyd runs as root.

    A hook that is writable by group or other, or that lives in a
    directory writable by group or other, is a local root escalation.
    """
    raise NotImplementedError


def find_id_conflicts(configs: Mapping[str, KeydConfig]) -> list[str]:
    """Device ids claimed by more than one config.

    keyd permits an id in only one file and ignores the duplicate, so a
    second config claiming ``8089:0019`` silently wins or loses.
    """
    raise NotImplementedError


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
