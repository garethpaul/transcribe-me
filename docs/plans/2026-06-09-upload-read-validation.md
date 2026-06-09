# Upload Read Validation

## Status: Completed

## Context

The upload validation path already handled empty, oversized, and non-byte
payloads, but it still assumed every upload-like object had a working
`getvalue()` reader. A malformed wrapper or a reader failure could surface a raw
exception instead of the app's user-facing upload validation error.

## Objectives

- Reject upload objects that do not expose a callable `getvalue()` reader.
- Convert upload reader failures into a generic upload validation message.
- Avoid loading Whisper for upload read failures.
- Keep local reader exception details out of the Streamlit error path.

## Work Completed

- Added a shared upload read failure message.
- Guarded `uploaded_audio_bytes()` against missing and failing readers before
  validating payload type, emptiness, and size.
- Added focused tests for missing readers, failing readers, and the
  Streamlit-facing unreadable upload path.
- Updated README, VISION, and CHANGES with the read-validation behavior.

## Verification

- `python3 -m pytest -q tests/test_app.py::test_write_uploaded_file_rejects_upload_without_getvalue tests/test_app.py::test_write_uploaded_file_rejects_upload_read_errors tests/test_app.py::test_main_rejects_unreadable_upload_before_loading_model`
- `python3 -m pytest -q tests/test_app.py`
- `python3 -m py_compile app.py`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Document first-run Whisper model download behavior and disk requirements.
- Add manual verification notes for common audio formats and expected duration.
