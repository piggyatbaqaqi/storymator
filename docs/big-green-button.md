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
still demands an authority cookie.  On this GNOME Wayland session that
cookie lives at

    /run/user/1116/.mutter-Xwaylandauth.EZBBU3

and **the suffix is regenerated at every login**, so the hook globs
`$XDG_RUNTIME_DIR/.mutter-Xwaylandauth.*` rather than hardcoding it.
It also sets `DISPLAY`, `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS`
and `HOME` before handing off.  `hook_test.py` asserts each of those on
the child's real environment.

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
   by `keyd_config.check_hook_permissions`.
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

    sudo install -m 0644 big_green_button/etc/big-green-button.conf \
        /etc/keyd/big-green-button.conf
    sudo install -m 0755 big_green_button/hook/big-green-button-press \
        /usr/local/bin/big-green-button-press
    sudo keyd.rvaiya reload
    journalctl -eu keyd | tail        # expect "DEVICE: match" not "ignoring"

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
      hook/big-green-button-press   the hook, installed to /usr/local/bin
      hook_test.py          runs the hook for real; checks its child env
    bin/big-green-button    check / render / show the device

The Python exists to keep the config honest.  keyd reports a bad key
name or a malformed id as a line in the journal and then carries on
with a partly-applied keymap, which on a button that is supposed to
suppress Return fails silently in the dangerous direction.  The
validator turns that into a test failure.
