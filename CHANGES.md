# Changes

## 2026-06-08

- Added a Makefile verification gate for Python syntax checks and focused app
  tests.
- Refactored the Streamlit app so importing `app.py` does not load the Whisper
  model.
- Added temporary audio-file cleanup after transcription.
- Added generated Python artifact ignores and test dependency metadata.
