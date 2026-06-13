---
title: FFprobe Stdin Isolation
date: 2026-06-13
type: implementation-plan
status: completed
---

# FFprobe Stdin Isolation

## Status: Completed

## Summary

Make the bounded audio-duration probe explicitly non-interactive at the Python
subprocess descriptor layer. The probe must never inherit or wait on the
Streamlit process's standard input.

## Problem Frame

`probe_audio_duration` already avoids a shell and enforces a ten-second
timeout, but its `ffprobe` process still inherits stdin. Server-side media
probing has no legitimate use for interactive input, so leaving the descriptor
open adds avoidable process coupling and makes timeout handling responsible for
a condition that can be prevented.

## Requirements

- R1. Set subprocess stdin to `subprocess.DEVNULL` so the child cannot inherit
  the server process descriptor even if FFmpeg option handling changes.
- R2. Preserve the shell-free command, JSON-only duration output, ten-second
  timeout, sanitized failures, duration bound, cleanup, and lock release.
- R3. Extend focused tests and static contracts so descriptor inheritance
  fails the canonical gate.
- R4. Record the non-interactive child-process boundary in maintenance and
  security documentation.

## Key Technical Decisions

- **Enforce the descriptor boundary in Python.** `ffprobe` does not expose the
  separate `ffmpeg` tool's `-nostdin` option, while
  `stdin=subprocess.DEVNULL` portably prevents descriptor inheritance.
- **Keep the existing timeout.** Closing stdin prevents interaction but does
  not replace the bound on malformed or slow media parsing.
- **Do not wrap ffprobe.** The current explicit argument list remains the most
  reviewable and portable shape for this small application.

## Scope Boundaries

This change does not add a transcription timeout, background queue, sandbox,
protocol allowlist, new dependency, or live model test. It does not alter
Whisper's separate decoder subprocess or accepted audio behavior.

## Implementation Units

### U1. Close the ffprobe stdin channel

- **Files:** `app.py`
- Pass `stdin=subprocess.DEVNULL` to the existing bounded `subprocess.run`
  call without changing the reviewed ffprobe argument vector.

### U2. Enforce the subprocess contract

- **Files:** `tests/test_app.py`, `scripts/check_docs_plans.py`
- Update the exact subprocess regression and require descriptor isolation,
  timeout retention, and sanitized failure behavior.

### U3. Complete maintenance evidence

- **Files:** `README.md`, `SECURITY.md`, `VISION.md`, `CHANGES.md`,
  `docs/plans/2026-06-13-ffprobe-stdin-isolation.md`
- Document the boundary and record focused, full-gate, mutation, artifact, and
  secret verification after implementation.

## Risks And Mitigations

- `DEVNULL` is provided by Python's standard subprocess API and is independent
  of optional FFmpeg build features.
- A command-only test could miss descriptor inheritance. The regression asserts
  the subprocess keyword arguments independently from the command list.

## Verification

- Thirteen focused ffprobe and transcription-lifecycle tests passed on Python
  3.12.8.
- A disposable exact-source snapshot passed the full pinned `make check` gate
  under a 180-second timeout: Ruff formatting and linting, compilation, 71
  tests, `pip check`, and direct-pin `pip-audit` with no known vulnerabilities.
- The same bounded full gate passed from the repository and from an external
  working directory against the corrected completed plan record.
- Six hostile mutations covering descriptor inheritance, timeout retention,
  test contracts, documentation, and completed plan status were rejected.
- Source review confirmed that `-nostdin` belongs to the separate `ffmpeg` CLI,
  not ffprobe; the implementation therefore uses only Python's portable
  descriptor isolation and preserves the known-valid ffprobe argument vector.
- Python AST, workflow YAML, JSON/SVG structure, exact-path, generated-artifact,
  whitespace, and changed-line secret audits passed. A live ffprobe smoke test
  was not run because this host does not have the system executable installed.

## Sources

- Python subprocess documentation for the `DEVNULL` standard stream sentinel:
  https://docs.python.org/3/library/subprocess.html#subprocess.DEVNULL
- FFprobe's current option documentation and source-backed command surface:
  https://ffmpeg.org/ffprobe.html
