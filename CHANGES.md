# Changes

## 2026-06-09

- Fell back to the safe `.audio` suffix when uploaded filename inspection fails,
  with no-model regression coverage.
- Added file-uploader help text that advertises the 25 MB upload limit before
  users choose an audio file.
- Render successful transcripts as plain text and added no-network coverage for
  markdown-like transcript output.
- Routed malformed or unreadable upload objects through user-facing upload
  validation before loading Whisper.
- Added tests for missing and failing upload readers.
- Rejected non-byte upload payloads before temporary file writes.
- Added upload validation coverage for unexpected non-byte `getvalue()`
  results.
- Cleaned up temporary files after upload write failures and report a generic
  user-facing save error.
- Added transcript text validation for Whisper results before display.
- Added tests for trimmed, missing, non-string, and blank transcript text.

## 2026-06-08

- Added generic transcription failure handling with temp-file cleanup tests and
  user-facing Streamlit errors.
- Added upload content and size validation before temporary file writes, with
  user-facing Streamlit errors and focused tests.
- Added `make check` as the shared repository verification alias.
- Normalized uploaded audio suffixes to a supported lowercase set before
  writing temporary files.
- Added tests that cover supported upload suffixes, unsupported extensions, and
  missing-name fallback behavior.
- Added a Makefile verification gate for Python syntax checks and focused app
  tests.
- Refactored the Streamlit app so importing `app.py` does not load the Whisper
  model.
- Added temporary audio-file cleanup after transcription.
- Added generated Python artifact ignores and test dependency metadata.
- Added canonical `docs/plans` coverage and a docs-plan checker under
  `make check`.
