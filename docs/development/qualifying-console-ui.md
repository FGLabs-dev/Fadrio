# FAD-0502 application console qualification

Recorded 2026-10-07 on GNOME Wayland through XWayland with normal host fonts. The accepted geometry change is in ADR-0003. This advances application controls; output controls and REL-00006 remain open.

## Observed behavior

The 940 × 680 console has a horizontally scrollable bank of 184-pixel logical application strips, vertical 0–100% faders, aligned mute buttons, icon/initial fallback, textual activity and mixed-volume help. At 420 × 680 the bank scrolls without compressing the controls. System/Light/Dark selection changes presentation only and lasts for this session. The light-theme thumb and active mute text retain contrast against their surfaces. Formal accessibility conformance remains unqualified.

`./scripts/capture-console.sh` creates a private PipeWire daemon, isolated XDG directories and five real silent playback streams. Its fixture-only native ABI client seeds levels with acknowledged commands; it does not change the production backend. The Browser fixture's 20% and 80% streams group into one 50% mixed strip. Chat is 60%, Game 78%, and Music 35% muted. CLI snapshots confirm four logical applications. The icon is project-owned; missing fixture icons use initials. Nothing modifies ordinary host audio.

Actual owned-window captures:

- [Dark, 940 × 680](../screenshots/fad-0502-console-dark.png)
- [Light, 940 × 680](../screenshots/fad-0502-console-light.png)
- [Light, 420 × 680](../screenshots/fad-0502-console-narrow.png)

## Validation

- `FADRIO_RUN_PIPEWIRE_INTEGRATION=1 ./scripts/test.sh`: 111 managed tests (25 UI), two native tests and isolated PipeWire integration passed.
- New meaningful UI cases check validated theme changes without audio commands and logical counts across multi-session updates, gesture freeze, release and disconnect.
- `./scripts/test-ui-interactions.sh`: actual vertical drag to 37%, Home + ten Up keys to 10%, mute, repeated with a header-only malformed PNG, daemon disconnect during drag, restart and recovered commands. Final run passed all three control scenarios.
- `dotnet format Fadrio.slnx --verify-no-changes --no-restore`, six Python roadmap tests, roadmap audit and `git diff --check` passed.
- Final themed render/build and the four-application capture passed after palette/scale/mute refinements.

The input harness finds the first vertical fader from the longest contiguous rendered track, activates the owned window through EWMH, verifies keyboard focus and polls backend state after asynchronous commands. The percentage scale is not a signal/dB meter. Core and the production native bridge are unchanged.

## Remaining gates

No claim is made for native Wayland, KDE, fractional scaling, screen readers, installed packaging or a long-running session. Theme persistence, output controls, durable mixer policies, tray and pinned inactive applications are still pending. The original BUG-00004 startup stall did not reproduce, and its cause is unknown; no fonts or host caches were removed. The October 6 portrait capture and qualification remain historical evidence for the earlier icon slice.
