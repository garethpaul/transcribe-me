---
title: FFprobe Stdin Isolation
date: 2026-06-13
type: implementation-plan
status: planned
---

# FFprobe Stdin Isolation

## Status: Planned

## Summary

Make the bounded audio-duration probe explicitly non-interactive at both the
FFmpeg command layer and the Python subprocess descriptor layer. The probe
must never inherit or wait on the Streamlit process's standard input.

## Problem Frame

`probe_audio_duration` already avoids a shell and enforces a ten-second
timeout, but its `ffprobe` process still inherits stdin and does not pass
FFmpeg's `-nostdin` option. Server-side media probing has no legitimate use for
interactive input, so leaving the channel open adds avoidable process coupling
and makes timeout handling responsible for a condition that can be prevented.

## Requirements

- R1. Pass `-nostdin` in the exact ffprobe command before the local input path.
- R2. Set subprocess stdin to `subprocess.DEVNULL` so the child cannot inherit
  the server process descriptor even if FFmpeg option handling changes.
- R3. Preserve the shell-free command, JSON-only duration output, ten-second
  timeout, sanitized failures, duration bound, cleanup, and lock release.
- R4. Extend focused tests and static contracts so either layer's removal
  fails the canonical gate.
- R5. Record the non-interactive child-process boundary in maintenance and
  security documentation.

## Key Technical Decisions

- **Use both controls.** `-nostdin` expresses intent to FFmpeg, while
  `stdin=subprocess.DEVNULL` enforces the descriptor boundary in Python.
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
- Add `-nostdin` to the argument vector and pass `stdin=subprocess.DEVNULL` to
  the existing bounded `subprocess.run` call.

### U2. Enforce the subprocess contract

- **Files:** `tests/test_app.py`, `scripts/check_docs_plans.py`
- Update the exact-command regression and require both non-interactive layers,
  timeout retention, and sanitized failure behavior.

### U3. Complete maintenance evidence

- **Files:** `README.md`, `SECURITY.md`, `VISION.md`, `CHANGES.md`,
  `docs/plans/2026-06-13-ffprobe-stdin-isolation.md`
- Document the boundary and record focused, full-gate, mutation, artifact, and
  secret verification after implementation.

## Risks And Mitigations

- Some FFmpeg builds may vary in optional features, but `-nostdin` is a generic
  tool option and `DEVNULL` is provided by Python's standard subprocess API.
- A command-only test could miss descriptor inheritance. The regression will
  assert the subprocess keyword arguments independently from the command list.

## Verification

- Focused ffprobe and transcription lifecycle tests.
- Full pinned `make check` from the repository and an external working
  directory with explicit timeouts.
- Hostile mutations for command isolation, descriptor isolation, timeout,
  tests, documentation, and completed plan status.
- Ruff, Python syntax, workflow YAML, structured-document, artifact,
  whitespace, intended-path, and changed-line secret audits.

## Sources

- FFmpeg tool documentation for disabling standard-input interaction:
  https://ffmpeg.org/ffprobe-all.html
- OpenAI Whisper's pinned decoder implementation, which already uses
  `-nostdin` for its separate ffmpeg invocation:
  https://github.com/openai/whisper/blob/main/whisper/audio.py
