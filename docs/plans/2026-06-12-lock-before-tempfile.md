# Acquire Transcription Lock Before Temp File

## Status: Completed

## Context

The transcription path validated each upload and wrote as much as 25 MB to a
temporary file before waiting up to 30 seconds for the process-wide Whisper
lock. Concurrent sessions could therefore accumulate sensitive audio files on
disk even when only one request could enter model inference.

## Objectives

- Fail busy requests without creating temporary audio files.
- Preserve the finite lock wait and single-inference model boundary.
- Keep cleanup and lock release reliable after every acquired-lock outcome.
- Preserve upload-validation and user-facing error types.

## Work Completed

- Moved temporary-file creation inside the acquired transcription lock.
- Kept model inference and temporary-file cleanup inside the same protected
  lifecycle.
- Used nested `finally` blocks so cleanup failures cannot prevent lock release.
- Preserved `UploadValidationError` for temp-write failures and
  `TranscriptionError` for model, cleanup, and lock-contention failures.
- Added deterministic tests proving contention performs no write and an
  acquired lock is released after a write failure.
- Extended repository contracts and maintenance documentation.

## Verification

- `python -m pytest -q tests/test_app.py`
- `make check`
- Mutations restoring pre-lock temp writes or removing release/error coverage
- `git diff --check`

Tests use fake uploads, models, locks, and temporary files; no model download,
live transcription, or external service is used.
