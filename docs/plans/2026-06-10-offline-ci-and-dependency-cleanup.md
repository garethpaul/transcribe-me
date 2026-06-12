# Offline CI and Dependency Cleanup

Status: Completed

## Goal

Continuously verify upload/transcription behavior without downloading Whisper
models, installing heavyweight ML runtime packages, or contacting external
services.

## Changes

- Remove the unused `ffmpeg` Python package; Whisper requires the system FFmpeg
  executable rather than that unrelated module.
- Pin pytest and Ruff as verification dependencies.
- Add formatting, lint, test, bytecode, and repository-contract gates.
- Add a least-privilege GitHub Actions matrix for Python 3.10 and 3.12
  using immutable action pins without persisting checkout credentials.
- Download each direct runtime artifact in CI without installing Whisper's
  heavyweight transitive ML graph.
- Audit pinned direct runtime packages without invoking pip dependency
  resolution or installing the heavyweight ML graph, and support manual
  workflow runs for maintenance verification.
- Document the boundary between offline mocked tests and live Whisper runtime
  validation.

## Scope Boundaries

- Upgrade Streamlit and Whisper only after dependency resolution proves the
  replacements build on Python 3.12.
- Do not download a Whisper model or transcribe real user audio in CI.

## Verification

- `make check`
- `python -m ruff format --check .`
- `python -m ruff check .`
- Workflow YAML validation.
- Negative workflow mutations for extra workflows, unsafe triggers, write
  permissions, credential persistence, and duplicate action steps.
- Confirm no test performs network access or model loading.
