# Changes

## 2026-06-08

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
