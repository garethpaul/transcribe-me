# Changes

## 2026-06-10

- Rejected unsupported audio content and filename/content mismatches before
  model loading or temporary-file creation.
- Derived safe WAV, MP3/MPEG, and M4A temporary suffixes from header bytes when
  upload names are missing or unusable.
- Detected missing system ffmpeg before writing user audio or loading Whisper.
- Enforced the 25 MB limit at the Streamlit server boundary.
- Removed the unrelated Python `ffmpeg` wrapper and pinned the test dependency.
- Upgraded OpenAI Whisper from `20231117` to `20250625` so dependency resolution
  works on Python 3.12.
- Upgraded Streamlit from 1.33.0 to 1.58.0 after resolving its stable API surface
  and Python 3.12 dependencies.
- Pinned PyArrow 23.0.1, the first release fixing CVE-2026-25087 and also
  containing the CVE-2024-52338 fix.
- Upgraded pytest to 9.0.3 to fix CVE-2025-71176 tmpdir handling.
- Upgraded Ruff from 0.6.9 to 0.15.16.
- Added Ruff formatting/linting, least-privilege Python 3.10/3.12 CI, and
  repository contract tests.
- Added CI resolution checks for each pinned direct runtime artifact.
- Ignored local virtual environments, Ruff caches, environment files, and
  Streamlit secrets.

## 2026-06-09

- Added a safe filename-inspection fallback, later strengthened with
  content-derived audio suffixes.
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
