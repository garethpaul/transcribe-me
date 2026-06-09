# Upload Bytes Validation

## Status: Completed

## Context

The Streamlit upload path expected `uploaded_file.getvalue()` to return bytes.
That is true for normal Streamlit uploads, but tests or future wrappers can
provide an object returning text or another unsupported type. Those values
reached the binary temporary-file write and raised a raw `TypeError` instead of
the app's upload validation error.

## Objectives

- Reject non-byte upload payloads before temporary file writes.
- Preserve existing empty and oversized upload validation.
- Keep invalid upload failures on the user-facing `UploadValidationError` path.

## Work Completed

- Updated `uploaded_audio_bytes()` to require bytes or bytearray data and
  normalize bytearray payloads to bytes.
- Added a focused regression test for non-byte upload content.
- Updated README, VISION, and CHANGES with the upload type guard.

## Verification

- `python3 -m pytest -q tests/test_app.py::test_write_uploaded_file_rejects_non_bytes_upload`
- `make lint`
- `make test`
- `make build`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Add manual verification notes for common audio formats and browser upload
  behavior.
- Document model download and ffmpeg requirements more explicitly in setup.
