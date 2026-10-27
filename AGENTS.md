# Fadrio contributor rules

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

## Risk-based targeted tests (mandatory)
- Never run a full test suite, solution-wide build, repository-wide lint/typecheck, or repeated test cycles automatically for every edit. Conserve execution time and tokens.
- First assess changed files and realistic regression risk. For docs, copy, comments, formatting, and clearly non-behavioral changes, skip automated tests unless a specific gate requires them; inspect the diff.
- For code affecting behavior, choose only the smallest relevant existing tests/filters/packages/assemblies; run once at a meaningful checkpoint, not after every tiny change. Avoid redundant restores and installs.
- If no relevant automated test exists, perform a focused feasible check and report what remains unverified; do not run unrelated suites to claim coverage.
- Broaden testing only for significant shared/core refactors, security/privacy, migrations, releases, targeted failures suggesting wider impact, explicit requests, or mandatory CI/release gates. Explain the escalation.
- Treat generic existing “run tests/build before commit” wording as targeted, risk-based verification for changed code, except genuinely mandatory security/CI/release gates.
- Report checks performed, intentional skips, and residual risk. Never imply skipped tests passed.
