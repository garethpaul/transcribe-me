# Transcription Lock Wait Timeout

## Status: Completed

## Context

The cached Whisper model is protected by a process-wide lock because Streamlit
sessions share the model. That prevents overlapping inference, but lock
acquisition is currently unbounded. If one inference stalls, every later
session can remain blocked indefinitely while its validated audio remains in a
temporary file.

## Priority

Uploaded audio is sensitive and transcription is CPU/GPU intensive. A bounded
wait limits per-request resource retention and gives users a predictable retry
path without weakening the existing single-inference safety boundary.

## Prioritized Engineering Backlog

1. Bound waiting for the shared transcription lock and clean up timed-out
   uploads now.
2. Add an explicit audio-duration or processing-time bound in a separate media
   validation pass.
3. Consider a real bounded job queue with cancellation and progress state if
   the sample evolves into a multi-user service.

## Requirements

- R1. A session must wait no longer than a named finite timeout to enter shared
  model inference.
- R2. Lock contention must raise a stable `TranscriptionError` message without
  invoking the model.
- R3. Any temporary upload must still be removed after lock timeout.
- R4. Acquired locks must be released after both successful and failed model
  calls.
- R5. Existing upload validation, transcript normalization, and user-safe error
  handling must remain unchanged.
- R6. Tests, docs, and the repository checker must preserve the bounded wait.

## Implementation Units

### U1. Bound shared-model lock acquisition

- **Files:** `app.py`
- Add a named lock wait duration and stable busy message.
- Acquire with a timeout, fail before model invocation on contention, and
  release in `finally` only after successful acquisition.

### U2. Add deterministic lifecycle tests

- **Files:** `tests/test_app.py`
- Use fake locks to prove the timeout value, no model call on contention,
  cleanup of the temporary file, and release after success and failure.

### U3. Preserve maintenance contracts

- **Files:** `scripts/check_docs_plans.py`, `README.md`, `SECURITY.md`,
  `VISION.md`, `CHANGES.md`
- Document the process-local bounded wait and enforce its source and test
  contracts under `make check`.

## Scope Boundaries

- Do not terminate or interrupt an inference already running in another thread.
- Do not introduce a background queue, task broker, or cross-process lock.
- Do not change the Whisper model, upload limit, or supported audio formats.

## Verification

- `.venv/bin/python -m pytest -q tests/test_app.py`
- `make check PYTHON=.venv/bin/python`
- `.venv/bin/python -m pip check`
- `.venv/bin/python -m pip_audit --requirement requirements.txt --no-deps --disable-pip`
- `git diff --check`
- Mutations restoring an unbounded context-manager acquisition or omitting lock
  release must fail focused tests and the repository checker.
