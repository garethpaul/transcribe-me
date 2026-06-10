# Cached Whisper Model Concurrency

## Status: Completed

## Context

`st.cache_resource` shares one Whisper model across Streamlit sessions in a
process. Multiple sessions could call `model.transcribe` concurrently against
that shared model, creating avoidable CPU/GPU pressure and relying on model
internals to be thread-safe.

## Objectives

- Prevent overlapping inference calls against the cached model.
- Preserve upload validation, temporary-file cleanup, and error handling.
- Prove serialization with a deterministic concurrency regression test.
- Keep CI offline and free of Whisper model downloads.

## Work Completed

- Added a process-local `threading.Lock` dedicated to transcription.
- Wrapped only the model inference call so upload validation and file setup do
  not hold the shared lock.
- Added a two-worker test that blocks the first inference and proves the second
  cannot enter the model until the first releases it.
- Documented the lock as a reliability boundary rather than a production queue
  or multi-user isolation mechanism.
- Made Makefile paths independent of the caller's directory and added `pip
  check` with ambient `PYTHONPATH` removed.
- Fixed CI to Ubuntu 24.04, added concurrency cancellation, and annotated
  immutable action commits with their verified release versions.
- Extended repository contracts for the lock, concurrency test, Makefile, and
  hosted workflow.

## Verification

- Fresh isolated installation from `test-requirements.txt`.
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m pytest -q`
- `python -m pip check`
- `python -m pip_audit --requirement requirements.txt --no-deps --disable-pip`
- `make check`
- `make -f /path/to/transcribe-me/Makefile check`
- Mutations for a removed lock, removed concurrency test, floating runner,
  ambient dependency state, and missing dependency consistency checks
- `git diff --check`

The test suite uses fake Streamlit and Whisper modules. It does not download a
model, invoke ffmpeg, transcribe real audio, or contact an external service.
