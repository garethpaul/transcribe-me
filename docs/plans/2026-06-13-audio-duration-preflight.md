# Audio Duration Preflight

## Status: Completed

## Context

The 25 MB upload limit bounds storage but not decoded audio duration. A highly
compressed file can therefore hold hours of audio and occupy the process-wide
Whisper slot, CPU, and memory for an excessive period.

## Priority

Duration is an input property that can be rejected before loading or invoking
Whisper. A bounded media probe reduces denial-of-service exposure while
preserving the existing upload, lock, temporary-file, and cleanup boundaries.

## Requirements

- R1. Probe accepted temporary audio with `ffprobe` before model loading or
  transcription.
- R2. Reject audio longer than a named finite duration with a stable generic
  user-facing error.
- R3. Bound the probe subprocess with a named finite timeout.
- R4. Treat missing, malformed, non-finite, non-positive, or failed probe
  results as generic transcription failures without exposing local paths or
  subprocess output.
- R5. Keep probing inside the acquired transcription lock and preserve temp
  cleanup and lock release for every probe outcome.
- R6. Tests, documentation, and the repository checker must preserve the
  duration and timeout contracts.

## Implementation Units

### U1. Add bounded duration probing

- **Files:** `app.py`
- Resolve both ffmpeg tools before accepting model work.
- Run `ffprobe` without a shell, parse its JSON output, and enforce named
  duration and subprocess timeout limits before model loading.

### U2. Add deterministic lifecycle tests

- **Files:** `tests/test_app.py`
- Cover the exact command and timeout, accepted duration, excessive duration,
  malformed output, probe failure, timeout, no model loading after rejection,
  and cleanup/lock release.

### U3. Preserve maintenance contracts

- **Files:** `scripts/check_docs_plans.py`, `README.md`, `SECURITY.md`,
  `VISION.md`, `CHANGES.md`
- Document the duration boundary and enforce its source and test contracts.

## Scope Boundaries

- Do not attempt to terminate Whisper after transcription begins.
- Do not add a background queue, external service, or new Python dependency.
- Do not change supported formats, the Whisper model, or the upload byte cap.

## Verification

- Python 3.12.8 passed all 71 tests, including bounded command construction,
  accepted, invalid, excessive, failed, and timed-out probe outcomes.
- `make check PYTHON=/tmp/transcribe-duration-venv/bin/python` passed Ruff
  formatting/linting, compilation, completed-plan checks, all tests, isolated
  `pip check`, and direct-pin `pip-audit`.
- Hostile mutations removing the probe, duration bound, timeout, cleanup, or
  regression-test contracts were rejected.
- `git diff --check` and focused secret/artifact review passed.
