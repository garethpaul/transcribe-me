# Tempfile Cleanup Gate

## Problem

The Streamlit app loaded the Whisper model at import time and wrote uploaded
audio to a `delete=False` temporary file without deleting it after
transcription. The repository also had no local verification command.

## TDD Evidence

1. Added tests with fake `streamlit` and `whisper` modules.
2. Ran `make test` before implementation changes and confirmed import loaded
   the model and no cleanup helper existed.
3. Refactored the app into import-safe helpers with `finally` cleanup and reran
   the full verification gate.

## Verification

- `make lint`
- `make test`
- `make build`
- `make verify`
- `git diff --check`
