# Upload Write Cleanup

## Status: Completed

## Context

Upload validation happens before a temporary file is created, but disk write
errors can still occur after the temporary path exists. Those failures should
not leave uploaded audio bytes behind or expose local filesystem details to the
user.

## Objectives

- Clean up the temporary file path when writing uploaded bytes fails.
- Convert write failures into a generic `UploadValidationError`.
- Keep Whisper model loading from starting after upload write failures.
- Add focused tests for cleanup and user-facing error reporting.

## Work Completed

- Added `UPLOAD_WRITE_FAILURE_MESSAGE` for generic upload save failures.
- Wrapped temporary-file writes with cleanup for partially created paths.
- Added no-network tests for direct write cleanup and Streamlit error handling.
- Extended docs-plan checks to require the write-failure guard and tests.
- Updated README, VISION, CHANGES, and SECURITY guidance.

## Verification

- `python -m py_compile app.py tests/test_app.py scripts/check_docs_plans.py`
- `python -m pytest -q`
- `python scripts/check_docs_plans.py`
- `make lint`
- `make test`
- `make build`
- `make check`
- `git diff --check`

## Follow-Up Candidates

- Add setup notes for system ffmpeg availability and first-run model downloads.
- Add manual verification notes for common audio formats.
