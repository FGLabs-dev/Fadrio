# ADR-0003: Application console with vertical faders

- Status: Accepted
- Date: 2026-10-07
- Owner: `FAD-0502`

## Context

The user requested a Voicemeeter-like visual direction for an app they intend to use daily. Sections 34 and 40 of TECH_SPEC.md prescribe a narrow vertical utility and discourage imitation studio controls. The request authorizes a presentation change, while the application-centric model, dependency direction, volume semantics and product scope remain authoritative.

The first-party Voicemeeter Banana screenshot (https://vb-audio.com/Voicemeeter/banana.htm) was reviewed for channel grouping, vertical faders, aligned mute controls and readable numeric levels. No artwork or source from that product is bundled.

## Decision

Default to a 940 x 680 application console, with fixed-width application strips arranged horizontally. Small windows and long application lists scroll instead of compressing controls. Each logical application retains one 0–100% fader, identity/icon, explicit playback/mute state and shared audio command path. The same row objects, interaction freeze, reconnect behavior and mixed-volume semantics remain in use. Provide System/Light/Dark theme selection for the current session.

This deliberately changes the default geometry and row layout in TECH_SPEC.md sections 34/40. It does not introduce audio buses, DSP, routing, fake signal meters, dB gain labels, physical-input strips or unsupported output controls. The existing output-control placeholder is secondary footer text. Playback state continues to describe stream activity rather than measured signal amplitude.

## Consequences

The user gets a directly inspectable fader bank; keyboard tests and screenshots must qualify the vertical orientation, theme contrast and overflow behavior. The native ABI, Core, resolver and persistent schema are unchanged. Theme persistence, a compact layout mode, signal metering and the full supported-desktop/scaling matrix remain future work.
