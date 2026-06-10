# Audio Signature Validation and CI

## Status: Completed

## Context

The uploader limited visible filename extensions, but backend processing trusted
that metadata and passed any non-empty bytes to Whisper and ffmpeg. Missing or
unsupported names were written with a generic `.audio` suffix. The Python
requirements also installed an unrelated `ffmpeg` wrapper even though Whisper
needs the system ffmpeg executable. Existing safety tests were not enforced by
hosted CI.

## Objectives

- Reject unsupported or mismatched content before temp-file creation.
- Derive a supported suffix from audio header bytes when name metadata is absent.
- Detect a missing ffmpeg executable before model loading or temp-file writes.
- Enforce the 25 MB upload limit before Streamlit hands bytes to the app.
- Remove the unrelated Python ffmpeg wrapper dependency.
- Replace the Whisper pin that fails to build on Python 3.12.
- Upgrade the two-year-old Streamlit framework pin after compatibility checks.
- Constrain Streamlit's PyArrow dependency to the first release fixing the
  known IPC use-after-free advisory.
- Run the complete repository check across supported Python versions in CI.

## Work Completed

- Added bounded header checks for WAV, MP3/MPEG, and M4A uploads.
- Reject filename extensions that disagree with detected content.
- Infer a safe supported suffix when filenames are missing, malformed, or
  unavailable.
- Validate content before model loading and check ffmpeg before writing user
  audio to disk.
- Added a Streamlit server upload cap aligned with the app's 25 MB limit.
- Removed `ffmpeg==1.4`, upgraded Streamlit to `1.58.0` and Whisper to
  `20250625`, pinned PyArrow to fixed release `23.0.1`, upgraded pytest to
  fixed release `9.0.3`, pinned current Ruff 0.15.16, and documented ffmpeg as a system
  prerequisite.
- Added focused regression coverage and a least-privilege GitHub Actions matrix.

## Verification

- `python3 -m pytest -q`
- `make check`
- Negative audio-signature and workflow mutation checks
- `python3 -m pip install --dry-run -r requirements.txt -r test-requirements.txt`
- `git diff --check`
