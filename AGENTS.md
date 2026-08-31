# Project instructions

This is the domedoor Pi's shutter-door controller: a recovered/patched
Raspberry Pi application that drives real hardware (a rotating dome-door
motor) and talks to a separate dome Pi's ASCOM Alpaca driver over the
network. It exists because this Pi's previous SD card failed; treat it as
a recovery-in-progress, not a finished product.

## Objectives

1. Drive the physical shutter doors (open/close/emergency-stop) safely via
   GPIO/PWM on this Pi.
2. Act as an ASCOM Alpaca *client* to the separate dome Pi's real driver —
   connect, mirror-cover open/close, find home, telescope tracking, stop
   rotation — without ever reimplementing that driver's own logic locally.
3. Give the operator (a safety engineer, typically testing with a hand on
   the emergency stop) enough live feedback and complete logging to
   reconstruct exactly what happened after any test, especially whenever
   physical hardware was allowed to move.

## Priorities

1. Hardware safety
2. Correctness of what gets logged (it's the primary record of physical
   behavior after the fact, not just the code)
3. Clear, hard-to-miss operator feedback for anything abnormal
4. Minimal dependencies (this Pi's SD card can fail again; stdlib only)
5. Everything else

## Development rules

- Never touch the dome driver code on the dome Pi (a separate, live
  production service on different hardware) without the operator's
  explicit go-ahead — even after finding a real bug in it (see the "known
  outstanding issue" in README.md). Document it, don't patch or restart it
  unasked.
- Before changing the *original* (non-ASCOM) recovered file, don't — fork
  into a new variant first and leave the original as a known-good
  fallback. This is why the ASCOM-enabled app is a separate file rather
  than an in-place rewrite.
- `AbortSlew` does not stop dome tracking (`Slaved`). Any dome "stop"
  action must explicitly send `Slaved=False` too, or the driver's own
  background tracking thread resumes motion within seconds on its own.
  Confirmed by testing, not theory — the dome visibly started moving again
  ~7s after an abort with tracking left on.
- Keep independent stop paths independent. The door's Emergency Stop is a
  local, GPIO-only, no-network-dependency action and must stay that way —
  never make it depend on a call to the dome Pi. The dome's own "Stop
  Rotation" is a separate button for a separate hazard. Don't merge them
  just to reduce button count.
- Any long-running physical motion needs a maximum-duration guard. When it
  trips, treat it as a probable mechanical fault: stop the actuator, latch
  a persistent fault state that blocks *all* further motion on that
  actuator (including any indirect/automatic trigger path, e.g. the
  weather auto-close), force an operator acknowledgment (a modal, not just
  a log line), and require an explicit clear action. Never auto-clear, and
  never let Emergency Stop double as the clear action — those stay
  conceptually separate too. (The door-motion-timeout fault is the
  reference implementation for this pattern.)
- Never assume a command completed just because the request succeeded.
  Confirm with a follow-up read of actual state where practical (e.g. this
  app re-fetches `ShutterStatus` after commanding it, even though the
  driver applies it synchronously).
- Verify third-party/hardware behavior empirically before relying on it —
  this project's own reference copy of the dome driver had already
  diverged from what's actually deployed (a `FindHome` re-entrancy guard
  that exists live but not in the repo's copy). Test against the real
  thing; don't trust a committed copy or documentation alone when it's
  safety-relevant.
- Shutdown must leave the dome in a safe state, not just close the window:
  disable tracking (if on) before disconnecting, and route *both* the Exit
  button and the OS window-close (X) button through the same shutdown
  path — don't let one bypass it.
- No new pip dependencies without a strong reason. Everything so far
  (`tkinter`/`ttk`, `urllib`, `json`, `logging`, `concurrent.futures`) is
  stdlib. This Pi's SD card can fail again; keep the footprint minimal so
  recovery stays simple next time too.
- Log every operator command (accepted *or* rejected, with why), every
  actual physical actuation, every state transition (on change only, not
  every poll tick), and every network call's outcome/latency. Logs get
  read by a human afterward to answer "did this behave safely" — treat
  missing coverage on a new feature as a bug, not a nice-to-have. Tag
  high-frequency telemetry (e.g. azimuth polling) at `DEBUG` so it doesn't
  drown out discrete events in a casual read, but never drop it either.
- Never commit or push a credential, even to a private repo, and never let
  one get typed into a command that echoes back into a visible transcript.
  If one is ever exposed, say so immediately and get it revoked — don't
  stay quiet about it (this happened once during this project's setup; it
  was caught and revoked).
- Keep the GUI window height comfortably under 1080px (a standard HD
  display's height) — this has come up repeatedly as features were added.
  Budget new rows against that; don't just grow the window unchecked.

## Before adding a new physical-motion feature, check

1. Does it need its own timeout/fault guard, or does an existing one
   already cover it?
2. What's the safe default/reset state if it errors mid-action?
3. Does it interact with another actuator's stop path? (Default answer:
   no — keep them independent unless there's a specific shared hazard.)
4. Will it be observable in the session log after the fact, both when it
   succeeds and when it's rejected?
5. Does it need a live, hard-to-miss operator indicator (not just a log
   line) if it represents a fault state?

## After making a change

- Run `python3 -m py_compile <file>.py` and
  `ruff check --select F821,E9 <file>.py` on whichever file changed — this
  repo has no CI, so this is the only automated safety net. Note: with
  `from tkinter import *` present, ruff will not flag a genuinely
  undefined name if it merely *resembles* something the star-import could
  plausibly provide — manually verify any new widget name is actually
  created somewhere, don't rely on the linter alone for that.
- Test on the real Pi/hardware whenever the change touches an actuator. If
  that's not possible from wherever the change is being made, say so
  explicitly rather than reporting success.
- After any hardware test, read the resulting session log and confirm it
  matches what should have happened — this project treats the log as the
  primary evidence for physical behavior, not code review alone.
- If a new significant rule or gotcha was learned in the process, add it
  here — this file should keep growing as understanding does, the same
  way it grew throughout this project's recovery.
