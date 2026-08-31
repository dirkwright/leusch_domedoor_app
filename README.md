# leusch_domedoor_app

Recovery and ongoing development of the "domedoor pi" — the Raspberry Pi that
drives the physical rotating dome doors (the "shutter doors") at this
observatory. The original SD card for this Pi failed; this repo starts from
the recovered/reconstructed application and its ongoing development,
including a new ASCOM Alpaca client integration with the separate dome
driver Pi.

## The two application files

- **`leusch_shutter_control_py3_weather_mirror_cover.py`** — the recovered
  original app, patched only enough to run again (SSH key auth to the dome
  Pi replacing a dead sshpass/plaintext-password path). Kept as a known-good
  fallback; **not** actively developed further.
- **`leusch_shutter_control_py3_weather_mirror_cover_ascom.py`** — the
  actively developed version. Talks to the dome Pi's real ASCOM Alpaca
  driver directly over HTTP instead of SSH-ing into standalone scripts, adds
  operator controls for the dome (connect, mirror cover, find home, track
  telescope, stop rotation), a 90-second door-motion timeout fault, and a
  structured session-logging system with a built-in log viewer.

Both are single-file Tkinter/`RPi.GPIO` scripts, run directly with
`python3 <file>.py` on the Pi. No pip install needed — stdlib only
(`tkinter`/`ttk`, `urllib`, `json`, `logging`, `concurrent.futures`).

## Hardware

### This Pi (domedoor pi) — BCM GPIO numbering

| Pin | Direction | Purpose |
| --- | --- | --- |
| GPIO 16 | input, active-high, pull-down | Door-open limit switch |
| GPIO 20 | input, active-high, pull-down | Door-closed limit switch |
| GPIO 21 | input, active-high, pull-down | Weather-event sensor |
| GPIO 5 | output | Motor drive, single PWM signal at 350Hz |

Motor duty-cycle values (tuned against real measured travel times during
this session — see "Significant states" below):
- **0%** = stop/idle
- **60.625%** = drive open (offset +10.625 from the 50% center)
- **43.625%** = drive close (offset −6.375 from the 50% center)

These are asymmetric on purpose: the door mechanism closes measurably faster
than it opens for the same offset magnitude, so open was tuned up and close
tuned down from an original symmetric ±17 offset. Real measured full-travel
times at the current values: **~58.5s open, ~45.3s close**.

The original (non-ASCOM) file also drove **GPIO 6** as a local mirror-cover
output alongside SSH calls to the dome Pi. The ASCOM version removes this
entirely — mirror-cover control now goes exclusively through the dome Pi's
Alpaca API (see below); there is no local GPIO for it anymore.

### The dome Pi — a separate physical machine, reached over the network

Not physically connected to this Pi at all — controlled only via its ASCOM
Alpaca HTTP API.

| Setting | Value |
| --- | --- |
| Host | `192.168.1.6` |
| Alpaca HTTP port | `5555` |
| Device number | `0` (single instance) |
| Device type | `Dome` (`/api/v1/dome/0/...`) |

Its own GPIO (BCM, on that Pi, not this one): home-position limit switch on
pin 17, VFD forward/reverse-enable on pins 23/24, mirror cover ("shutter" in
ASCOM terminology — see the terminology note below) on pin 26. It also polls
a SiTech telescope controller at `192.168.1.214:8079` over a raw socket for
its own telescope-tracking ("slaving") feature.

**Terminology note:** ASCOM's `IDome` interface calls the mirror cover the
"shutter" (`OpenShutter`/`CloseShutter`/`ShutterStatus`). That is *not* the
same thing as this project's "shutter doors" — this app's doors are the
physical rotating dome doors, a completely separate mechanism on this Pi,
never reachable through the dome Pi's Alpaca API at all. Don't conflate the
two when reading code or logs from either project.

## Significant states

**Door motion** (`door_opening_flag`/`door_closing_flag`/`door_opened_flag`/
`door_closed_flag`): safe default is closed at startup, matching the
physical default. A motion command is rejected (and logged with a reason)
if another motion is already in progress, if the target state is already
reached, or if a weather lockout or door fault is active.

**Door motion timeout fault** (`door_fault_flag`): if an open or close never
reaches its limit switch within 90 seconds, that's treated as a probable
mechanical fault (obstruction, jam, broken/misaligned limit switch, drive
coupling failure) — the motor is stopped, a red banner and modal popup tell
the operator what happened, **all** door motion is blocked (including the
automatic weather-triggered close), and it stays blocked until the operator
explicitly clicks "Clear Door Fault." Nothing clears it automatically, and
pressing Emergency Stop does not clear it either — those are deliberately
independent (see AGENTS.md).

**Dome connection/status** (ASCOM version only): `dome_connected`,
`dome_shutter_status` (mirror cover; `ShutterState` enum: 0=Open, 1=Closed,
2=Opening, 3=Closing, 4=Error), `dome_slewing`, `dome_at_home`,
`dome_at_park`, `dome_slaved` (telescope tracking), `dome_azimuth`. Polled
every 5s (everything except azimuth) and every 200ms (azimuth only, for a
live readout). A background worker thread handles all dome network calls so
a slow or unreachable dome Pi never blocks the door controls.

**Known safety fix — AbortSlew does not stop tracking:** confirmed by testing
(see logs from 2026-08-28) that calling the dome driver's `AbortSlew` while
`Slaved` (tracking) is on stops the *current* motion but the driver's own
background tracking thread resumes moving the dome again within seconds,
unattended. Both "Stop Dome Rotation" and "Find Dome Home" now explicitly
send `Slaved=False` first, before/alongside their main action.

**Shutdown safety:** exiting (via the Exit button *or* the window's close
button — both routed through the same path) disables tracking first if it's
on, then disconnects from the dome, before tearing anything else down. This
avoids leaving the dome driver's tracking thread running unattended after
this client is gone.

## Logging

Every run writes `logs/session_YYYYMMDD_HHMMSS.jsonl` — one file per
session, JSON-lines format (one JSON object per line), so it's both plain-
text-readable and machine-replayable. Fields: `ts` (ms precision), `t_rel_s`
(seconds since session start), `level` (`INFO` for discrete events, `DEBUG`
for high-frequency azimuth telemetry), `category`
(`system`/`door`/`weather`/`dome`/`alpaca`), `event`, plus event-specific
fields.

Covers: every operator command (accepted or rejected, with a reason), every
actual motor start/stop, every limit-switch transition (logged only on
change), every dome network call (attribute, params, latency, result/error),
every meaningful dome state change, and session start/end.

A "View Last Session Log" button in the app opens the previous completed
session's log in a separate, larger window — a filterable/sortable table
(`ttk.Treeview`), not a raw dump, with rows color-coded by category and
errors/emergency events highlighted in red.

## Known outstanding issue (not fixed here, by design)

The dome driver itself (a separate live service on the dome Pi, outside
this repo) has a bug: if `AbortSlew` interrupts a `FindHome` in progress, an
internal "homing in progress" guard flag never clears, and every subsequent
`FindHome` call fails with `RuntimeError: Cannot start FindHome: homing is
already in progress` until that driver process is restarted. Confirmed via
testing 2026-08-28. Left alone deliberately — it's production code on a
different physical machine, not something to patch or restart without the
operator's explicit go-ahead.
