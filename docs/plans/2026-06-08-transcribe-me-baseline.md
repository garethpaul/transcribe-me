# Transcribe Me Baseline

## Status: Completed

## Context

`transcribe-me` is a Streamlit app that accepts an uploaded audio file and runs
a local Whisper transcription model. The maintenance baseline should keep
uploaded audio handling local, temporary, and explicit about suffix validation.

## Objectives

- Preserve the Streamlit upload-to-transcription flow.
- Avoid loading the Whisper model merely by importing `app.py`.
- Normalize upload suffixes before writing temporary files.
- Delete temporary audio files after transcription.
- Maintain completed maintenance plans under `docs/plans`.

## Work Completed

- Confirmed `make check` runs Python syntax checks and focused pytest coverage.
- Added canonical `docs/plans` coverage for the current upload/transcription
  baseline.
- Added a docs-plan checker under `make lint` that requires completed plans
  with `make check` verification.
- Updated README, VISION, and CHANGES to make the baseline discoverable.

## Verification

- `python3 -m py_compile app.py`
- `python3 scripts/check_docs_plans.py`
- `python3 -m pytest -q`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Document ffmpeg and first-run Whisper model download behavior.
- Add file size and duration guidance before public deployment.
