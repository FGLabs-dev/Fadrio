# Fadrio contributor rules

## Mandatory work tracking

Tracking is part of implementation and must be correct before code is pushed.

- For every non-trivial bug fix, feature, behavior change, refactor, security change, packaging/release change, or user-facing documentation change, search `ROADMAP.md` and GitHub Issues before implementation.
- Reuse the existing owning `FAD-xxxx`, `BUG-xxxxx`, or `REL-xxxxx` item when it already covers the work. Do not create a duplicate merely to obtain a new ID.
- If no suitable tracked item exists, create/allocate the work according to the roadmap rules before treating implementation as active.
- A dedicated branch is optional unless another repository rule requires one; the current branch may own tracked work.
- Before every push, verify the active work has its canonical ID and GitHub issue linkage, that roadmap/project status still matches reality, and that required changelog/release evidence is updated.
- Every non-trivial pull request must reference the owning ID and link its GitHub issue with `Closes #N`, `Fixes #N`, `Resolves #N`, or `Refs #N` as appropriate.
- Never renumber or reuse existing IDs, and do not reconstruct tracking after a push when it could have been declared beforehand.
- Tiny typo/format-only edits may remain untracked when they do not change behavior, release output, evidence, or product scope. Any larger exception must state why tracking was skipped.

- Read `TECH_SPEC.md` before architectural or product changes. It is authoritative.
- Preserve the dependency direction and application-centric model in `TECH_SPEC.md`.
- `Fadrio.Core` must remain free of Avalonia, PipeWire, SQLite, Linux, Steam, and MIDI dependencies.
- Never replace native PipeWire integration with shell-command parsing.
- Keep raw node IDs and process IDs out of normal UI state.
- Add fixture tests for resolver changes.
- Treat disappearing processes, streams, and controllers as normal runtime conditions.
- Copy native callback data immediately; native callbacks must never touch Avalonia.
- Keep persistent identity stable and evidence-based. PID is diagnostic data only.
- Do not add telemetry, network listeners, root requirements, DSP, or routing features.
- Record material architectural deviations in `docs/decisions/`.
- Keep patches scoped, preserve user changes, and run `./scripts/test.sh` when native prerequisites are installed.
