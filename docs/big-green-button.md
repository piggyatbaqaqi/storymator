# big_green_button

Capture the output of one dedicated USB button so that it drives our own
software instead of typing Return into whatever window happens to have
focus.

## The device

The button is a `LinTx USB Keyboard`, USB `8089:0019`, serial
`BEC8023D`.  It presents **two** input interfaces from the same
vendor:product pair:

| interface | kernel name                | handlers              |
|-----------|----------------------------|-----------------------|
| `input1`  | `LinTx USB Keyboard`       | `event24`, `kbd`      |
| `input1`  | `LinTx USB Keyboard Mouse` | `event25`, `mouse2`, `js0` |

Stable paths:

    /dev/input/by-id/usb-LinTx_USB_Keyboard_BEC8023D-if01-event-kbd
    /dev/input/by-id/usb-LinTx_USB_Keyboard_BEC8023D-if01-event-mouse

The second interface matters: it is why the keyd id in our config carries
the `k:` prefix.  keyd's own manual calls mouse management experimental
and warns that adding a mouse to an `[ids]` section "may break your
pointer".  `k:8089:0019` matches the keyboard interface only and leaves
`js0` alone.

Pressing the button emits `KEY_ENTER`.  The config also binds `kpenter`,
because cheap HID buttons are inconsistent about which of the two
Returns they report and binding both costs nothing.

## What the button actually emits

Measured with `evtest` on `/dev/input/event24`, with the operator
tapping once and holding once:

| value | meaning           | count over one 1.18 s hold |
|-------|-------------------|----------------------------|
| 1     | key down          | 1                          |
| 2     | kernel autorepeat | 28                         |
| 0     | key up            | 1                          |

So there are indeed three event *values*, but the repeat is not one
event -- the device advertises `EV_REP` with `REP_DELAY=250` ms and
`REP_PERIOD=33` ms, and the measured cadence was 34.1 ms.  A 0.11 s tap
produced no repeats at all; the 1.18 s hold produced 28.  Each of these
is preceded by an `EV_MSC`/`MSC_SCAN` and followed by an `EV_SYN`.

The scancode is always `70028` -- HID usage page 7, usage 0x28,
"Keyboard Return" -- and the keycode is always `KEY_ENTER` (28).  The
button never sent `KEY_KPENTER` (96) in testing.  The config binds
`kpenter` anyway: it is one line, it costs nothing, and it means a
firmware mode change or a replacement button cannot quietly start
leaking Returns into the keyboard stream.

## What keyd does with a press

This is the part that decides whether the design works, so it is worth
stating from the source rather than from hope.  keyd 2.5.0:

* **drops autorepeat before anything sees it.**  `src/device.c`, in
  `device_read_event`:

      /* Ignore repeat events. */
      if (ev.value == 2)
      	return NULL;

* **runs `command()` on key down only.**  `src/keyboard.c`, in
  `process_descriptor`:

      case OP_COMMAND:
      	if (pressed) {
      		execute_command(...);

* **does not wait for the command.**  `execute_command` double-forks;
  the parent waits only for the intermediate child, which exits
  immediately.  The hook therefore cannot stall the keyboard daemon,
  and it is reparented to init.

* **gives the command no stdio.**  `execute_command` reopens fds 0, 1
  and 2 on `/dev/null`.  There is nowhere for the hook to print, which
  is why it keeps a log file.

Net effect: **one hook invocation per physical press.**  Holding the
button down does nothing extra, and releasing it does nothing at all.
No debounce is needed anywhere.

## The hook's environment

keyd runs as a systemd service, so the hook inherits root's
environment: no `DISPLAY`, no `XAUTHORITY`, no `DBUS_SESSION_BUS_ADDRESS`,
no `HOME`.  A GUI command started that way fails with

    Authorization required, but no authorization protocol specified
    Error: Can't open display: :0

even though `/tmp/.X11-unix/X0` is world-accessible, because XWayland
still demands an authority cookie.

The hook asks the operator's own systemd user manager for the live
values:

    systemctl --user show-environment
    DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1116/bus
    DISPLAY=:0
    WAYLAND_DISPLAY=wayland-0
    XAUTHORITY=/run/user/1116/.mutter-Xwaylandauth.EZBBU3

GNOME imports those at login, so this tracks whatever is true now --
across reboots, across re-logins, and whichever display number XWayland
took.  The first version hardcoded `DISPLAY=:0` and globbed
`$XDG_RUNTIME_DIR/.mutter-Xwaylandauth.*`; both worked, but each was a
standing bet, the cookie's name being new every login and this machine
having an `X1` socket as well as `X0`.  That pair survives only as a
fallback for a press with no user manager to ask.

The values are passed to `env` as whole argv entries, never through
`eval`, so a space or a shell metacharacter in one cannot become code.
`hook_test.py` compares the child's real environment against
`show-environment` rather than against values of its own.

## Identification, replugging and reboots

**The button is identified by USB vendor:product, not by port.**  The
`[ids]` section says `k:8089:0019` and that is all keyd matches on.
Nothing in this design touches any of the things that *do* move:

| path | moves? | used here |
|------|--------|-----------|
| `/dev/input/event24` | yes, freely | no -- only reported by `check` |
| `/dev/input/by-path/pci-…-usb-0:10:1.1-event-kbd` | yes, encodes the port | no |
| `/dev/input/by-id/usb-LinTx_USB_Keyboard_BEC8023D-…` | no, encodes the serial | diagnostics only |
| `[ids] k:8089:0019` | no | **yes** |

Verified rather than assumed: the button was unplugged and moved to a
different socket, taking `Phys` from `usb-0000:80:14.0-7/input1` to
`usb-0000:80:14.0-10/input1`, and keyd re-matched it unprompted:

    DEVICE: removed  8089:0019:b9fb0960 LinTx USB Keyboard Mouse
    DEVICE: match    8089:0019:6f7af444  /etc/keyd/big-green-button.conf

keyd watches for device add and remove, so a replug needs no reload.

### The third component keyd logs

`keyd.rvaiya monitor` and the journal print ids as `8089:0019:6f7af444`.
That tail is **not** a port or a serial.  From `src/device.c`:

    snprintf(dev->id, sizeof dev->id, "%04x:%04x:%08x",
             info.vendor, info.product,
             generate_uid(num_keys, absmask, relmask, dev->name));

-- a djb2 hash of the key count, the abs/rel capability masks and the
device *name*.  It exists because one vendor:product can present
several interfaces, which is exactly our case: the keyboard hashes to
`6f7af444` and the mouse to `b9fb0960`.  So the 3-part form is also
port-independent and stable across reboots, and is safe to paste from
the journal if the 2-part form ever needs narrowing.  `DeviceId.parse`
accepts it, and `DeviceId.matches` ignores the hash, because we never
learn an attached device's hash and matching on it could only produce
false negatives.

### Reboots

Yes, it survives them.  Three things have to persist and all do:

* `/etc/keyd/big-green-button.conf` and `/opt/big-green-button/press`
  are ordinary files;
* `keyd.service` is `enabled`, so systemd starts it at boot; and
* the match is on vendor:product, which does not change.

The one thing that *is* new at every login is the session environment:
`XAUTHORITY` points at `.mutter-Xwaylandauth.<random>`, and the display
number is not guaranteed to be `:0` -- this machine has both an `X0`
and an `X1` socket in `/tmp/.X11-unix`.  The hook therefore asks the
operator's own systemd user manager for the live values instead of
remembering any of them.  See below.

### What would break it

* **A second device reporting `8089:0019`.**  It is a generic id, so
  another cheap HID button or keypad could share it, and keyd would
  grab that too and swallow its Return.  Narrow with the 3-part id from
  the journal if it happens.
* **A firmware mode change** that starts sending `kpenter` -- already
  bound, so this is covered.
* **Anything else grabbing the device first**, which is why
  `check` exists.

Note that piggy's membership of group `input` is *not* needed by this
design: keyd runs as root and opens the device itself, and the only
thing we read is world-readable `/proc/bus/input/devices`.  It can be
reverted if it was added only for this.

## Why keyd rather than our own daemon

The first design was a Python daemon that opened the event device,
took the exclusive grab (`EVIOCGRAB`) and published presses on a Unix
socket.  That works, but keyd 2.5.0 is already installed and running on
this machine, and it does the same two things we need:

* it takes the exclusive grab on the devices it manages, so the Return
  never reaches the normal keyboard stream; and
* `command(<shell command>)` runs an arbitrary command on a key press.

Together those are the whole feature, in a config file, with no daemon
of ours to supervise, no udev rule, and no grab to lose on replug.

The two approaches are **mutually exclusive**: whoever holds the grab
owns the device.  If keyd manages `8089:0019`, a daemon of ours cannot
also grab it, and vice versa.  We chose keyd, so there is no daemon.

## What keyd currently does

Nothing.  `/etc/keyd/` is empty, so keyd ignores every device:

    DEVICE: ignoring 8089:0019:6f7af444  (LinTx USB Keyboard)
    DEVICE: ignoring 8089:0019:b9fb0960  (LinTx USB Keyboard Mouse)

Adding our config is the first thing keyd on this machine will do.

## The config

`big_green_button/etc/big-green-button.conf`, installed to
`/etc/keyd/big-green-button.conf`:

    [ids]

    k:8089:0019

    [main]

    enter   = command(/usr/local/bin/big-green-button-press)
    kpenter = command(/usr/local/bin/big-green-button-press)

Both halves are load-bearing:

* `[ids]` **must** be the first section; keyd rejects the file
  otherwise.  A device id may appear in only one config file in
  `/etc/keyd/`, so two configs claiming `8089:0019` is an error we
  check for rather than discover in the journal.
* `command()` runs **as the user running keyd, which is root.**  See
  Security below.

### The "weird keystroke" alternative, and why it is not the default

The fallback we were willing to settle for was mapping the button to a
rare keystroke and catching that in another application:

    enter = f24

keyd accepts `f24` -- it is in `keyd.rvaiya list-keys`, and the kernel
has `KEY_F24` (194), which xkb calls keycode 202 / `<FK24>`.  But on
this machine that keystroke is **a dead end as shipped**:

* `<FK24>` is bound to the `F24` keysym only in
  `/usr/share/X11/xkb/symbols/fkeys`, in the `basic_13-24` variant.
* Nothing in `/usr/share/X11/xkb/symbols/` includes `fkeys`.  The
  default `pc` layout does not.

So keycode 202 reaches the GNOME Wayland compositor with no keysym, and
an application asked to bind "F24" has nothing to bind.  Making this
route work needs the xkb layout extended with `fkeys(basic_13-24)`
first -- a separate change to the session's keymap, not something this
config can do.

`command()` reaches our software directly and needs no keymap change,
so it is the default.  The `f24` line is kept in the config as a
comment for whoever wants the other route, with this caveat beside it.

## Security

`command()` runs as root.  Three consequences:

1. The hook must be root-owned and not writable by group or other, or
   any local user can run code as root by editing it.  This is checked
   by `keyd_config.check_hook_permissions`, and the check must walk
   *up* the path: a group-writable ancestor lets someone swap the whole
   directory, so the file's own mode is not enough.

   **It found something on the first run.**  The hook was installed to
   `/usr/local/bin/big-green-button-press`, and on this machine

       drwxrwxr-x root src /usr/local
       drwxrwxr-x root src /usr/local/bin

   with `getent group src` listing exactly one member -- the operator.
   That makes a root-run hook a standing local escalation: any process
   running as the operator (a compromised browser, a bad pip install)
   could plant code that runs as root at the next button press, without
   ever needing the sudo password.  The hook therefore lives in

       /opt/big-green-button/press

   because `/opt` is `root:root` 0755.  Tightening `/usr/local` instead
   would work, but that 0775 looks deliberate -- it is what lets the
   operator install into `/usr/local` without sudo -- so moving one
   file is the smaller change.  `button.HOOK_DIR` holds the decision
   and `button_test.py` pins it.
2. The hook should do as little as possible as root.  The example hook
   drops to the desk operator and execs the real work.
3. The hook path in the config must be absolute.  keyd runs it through
   a shell, so a relative path resolves against keyd's working
   directory, not ours.

`OPERATOR_CMD` and `LOG` can be overridden from the environment, which
is what lets `hook_test.py` drive the script without a button.  That is
not a privilege hole: keyd's environment comes from systemd rather than
from any user, and `OPERATOR_CMD` runs *after* privilege is dropped, so
an override buys the operator's rights and not root's.

## Installing

    sudo install -d -m 0755 -o root -g root /opt/big-green-button
    sudo install -m 0755 -o root -g root \
        big_green_button/hook/big-green-button-press \
        /opt/big-green-button/press
    sudo install -m 0644 -o root -g root \
        big_green_button/etc/big-green-button.conf \
        /etc/keyd/big-green-button.conf
    sudo keyd.rvaiya reload
    journalctl -eu keyd | tail        # expect "DEVICE: match" not "ignoring"

The `-o root -g root` is not decoration: `install` without it keeps the
invoking user's group, and the whole point of `/opt/big-green-button`
is that nothing but root can write it.  A healthy reload says

    DEVICE: match    8089:0019:6f7af444  /etc/keyd/big-green-button.conf
    DEVICE: ignoring 8089:0019:b9fb0960  (LinTx USB Keyboard Mouse)

-- the keyboard interface claimed, the mouse interface left alone.

`bin/big-green-button check` reports whether the button is attached,
which keyd config claims it, and whether the hook's permissions are
safe.

## Verifying

Press the button and confirm three things:

* the hook ran -- it logs to `/var/log/big-green-button.log`, and with
  the default `OPERATOR_CMD` an `xeyes` window appears;
* **no Return was typed** into the focused window.  Put the cursor in a
  text editor and press the button.  A newline appearing there means
  keyd did not match the device and the grab never happened; and
* **holding the button gives you one `xeyes`, not thirty.**  That is
  the autorepeat claim above; if you get a swarm, keyd is not in the
  path and something else is reading the device.

The panic sequence `backspace+escape+enter` terminates keyd if a config
ever locks up the machine's keyboard.  Worth knowing before editing
`/etc/keyd/` on a laptop whose internal keyboard keyd could also claim.

## Layout

    big_green_button/
      keyd_config.py        parse, render and validate keyd configs
      input_devices.py      read /proc/bus/input/devices, find the button
      etc/big-green-button.conf     the artifact installed to /etc/keyd/
      hook/big-green-button-press   the hook, installed to /opt/big-green-button/press
      hook_test.py          runs the hook for real; checks its child env
    bin/big-green-button    check / render / show the device

The Python exists to keep the config honest.  keyd reports a bad key
name or a malformed id as a line in the journal and then carries on
with a partly-applied keymap, which on a button that is supposed to
suppress Return fails silently in the dangerous direction.  The
validator turns that into a test failure.
