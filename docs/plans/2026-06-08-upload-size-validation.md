# Upload Size Validation

## Status: Completed

## Context

The app normalized upload suffixes and deleted temporary files after
transcription, but it still wrote empty or arbitrarily large upload payloads to
disk before Whisper validation. Uploaded audio can be sensitive and expensive to
process, so obvious invalid inputs should be rejected before a temp file is
created.

## Objectives

- Preserve the Streamlit upload-to-transcription flow.
- Reject empty uploads before writing temporary files.
- Bound upload bytes before writing temporary files or invoking Whisper.
- Surface validation errors in the Streamlit UI.
- Cover validation with fake Streamlit/Whisper tests.

## Work Completed

- Added `MAX_UPLOAD_BYTES` and `UploadValidationError`.
- Added upload byte validation before temp-file writes.
- Added Streamlit error handling for upload validation failures.
- Added tests for empty and oversized uploads without loading Whisper.
- Updated README, VISION, and CHANGES.

## Verification

- `python3 -m py_compile app.py`
- `python3 scripts/check_docs_plans.py`
- `python3 -m pytest -q`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Document the default upload byte limit in the README running section.
- Add duration guidance for supported audio files.
