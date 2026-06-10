# Temporary Audio Cleanup Errors

Status: Completed

## Goal

Prevent temporary-file deletion failures from exposing local filesystem details
or overriding the app's user-safe upload and transcription error contracts.

## Implementation

- Centralize temporary audio deletion with missing-file tolerance.
- Convert other deletion failures to the caller's existing sanitized exception.
- Cover cleanup failures after successful inference and failed upload writes.
- Keep the cleanup contract enforced by the repository checker.

## Verification

- `python -m pytest -q`
- `make check`
- Mutation check: replacing the cleanup wrapper with a direct `os.unlink` must
  expose an `OSError` and fail the focused regression test.
