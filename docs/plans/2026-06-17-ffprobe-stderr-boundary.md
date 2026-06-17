# Discard Unused ffprobe Diagnostics

## Status: Planned

## Context

The duration preflight runs `ffprobe` with a ten-second timeout and sanitized
errors, but `capture_output=True` buffers both stdout and stderr in memory.
Only the small JSON duration response from stdout is consumed. Diagnostics are
never shown or logged, so malformed attacker-controlled media can make the
process retain unnecessary stderr output until exit or timeout.

## Requirements

- Keep `ffprobe` stdin disconnected with `subprocess.DEVNULL`.
- Capture stdout for the existing JSON duration result.
- Route stderr directly to `subprocess.DEVNULL` rather than a memory pipe.
- Preserve the ten-second timeout, exact command, duration validation, and
  stable user-facing failure message.
- Add mutation-sensitive static coverage that rejects restored combined
  capture, missing stdout capture, or buffered stderr.
- Update operator and contributor documentation without claiming that stdout,
  parser CPU, or Whisper inference is globally bounded.

## Implementation Units

### U1. Narrow ffprobe pipe ownership

- **Files:** `app.py`, `tests/test_app.py`
- **Outcome:** The probe retains only its required JSON stdout and discards
  unused diagnostics at the operating-system boundary.

### U2. Enforce the contract

- **Files:** `scripts/check_docs_plans.py`,
  `scripts/test_ffprobe_stderr_contract.py`, `Makefile`
- **Outcome:** Static and hostile mutations prevent accidental restoration of
  unbounded stderr capture.

### U3. Record limitations

- **Files:** `README.md`, `SECURITY.md`, `VISION.md`, `CHANGES.md`,
  `docs/plans/2026-06-17-ffprobe-stderr-boundary.md`
- **Outcome:** Documentation distinguishes discarded diagnostics from the
  existing duration, timeout, upload-size, and inference boundaries.

## Verification

- Run focused ffprobe tests and hostile mutations.
- Run repository and external-directory `make check`.
- Audit the exact diff, generated artifacts, and credential patterns.
- Require one bounded exact-head hosted snapshot after push.

## Scope Boundaries

- Do not change accepted formats, upload size, duration, timeout, ffprobe
  command semantics, transcript handling, model loading, or inference locking.
- Do not add logs containing ffprobe diagnostics or temporary paths.
- Do not implement a misleading thread-based Whisper timeout.
