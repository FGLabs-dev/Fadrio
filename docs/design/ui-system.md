# UI system

The current mixer is a 940 x 680 application console, with a 420-pixel minimum width. Fixed-width logical-application strips arrange horizontally and scroll at small widths or with many applications. Each strip uses a vertical 0–100% fader, name/icon, textual activity state, large numeric level and an aligned mute action. The spacing scale is 4, 8, 12, 16, 24, and 32. See [ADR-0003](../decisions/ADR-0003-application-console-layout.md) for the user-requested change from the initial narrow utility.

System, light, and dark themes can be selected in the header for the current session. The visual tone is calm, readable and tactile: slate surfaces, restrained green track fill, and visible fader handles. Voicemeeter's aligned channel layout is the visual reference; all controls must correspond to implemented application behavior. There are no decorative signal meters, fictitious bus buttons or dB gain values.

Application rows eventually contain icon, name, volume, slider, mute, and contextual actions. PID and PipeWire node identifiers belong only in diagnostics.
