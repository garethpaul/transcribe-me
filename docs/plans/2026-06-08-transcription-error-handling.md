# Transcription Error Handling

## Status: Completed

## Context

Upload validation failures already produced user-facing Streamlit errors, and
temporary files were removed after successful transcription. If Whisper, ffmpeg,
or model loading failed, the raw exception could still bubble out of the app and
expose local details instead of giving the user a generic recovery message.

## Objectives

- Preserve local Whisper transcription behavior for valid files.
- Keep temporary-file cleanup on transcription failures.
- Report transcription failures through a generic Streamlit error.
- Avoid exposing raw local exception details or temp paths in the UI.

## Work Completed

- Added a `TranscriptionError` wrapper for model load, transcription, and
  missing-text result failures.
- Updated `main()` to show a generic Streamlit error for transcription failures.
- Added tests for UI error reporting, temp-file cleanup after failures, and
  missing text results.
- Updated README, VISION, and CHANGES.

## Verification

- `python3 -m pytest -q tests/test_app.py`
- `python3 -m py_compile app.py`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Add duration guidance for supported audio files.
- Add manual verification notes for common audio formats and ffmpeg setup.
