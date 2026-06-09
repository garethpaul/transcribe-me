# Upload Limit Help Text

## Status: Completed

## Context

The app enforces `MAX_UPLOAD_BYTES` before writing uploaded audio to a temporary
file, but the Streamlit file picker did not tell users about that limit before
they selected a file.

## Objectives

- Keep the backend 25 MB upload limit unchanged.
- Derive user-facing help text from the same limit constant.
- Show the limit in the file uploader UI.
- Add no-network and static coverage so the UI hint stays present.

## Work Completed

- Added `MAX_UPLOAD_MEGABYTES` and `UPLOAD_HELP_TEXT` derived from
  `MAX_UPLOAD_BYTES`.
- Passed `help=UPLOAD_HELP_TEXT` to `st.file_uploader`.
- Added a no-network Streamlit test for the upload limit help text.
- Extended `scripts/check_docs_plans.py` to preserve the uploader help guard.
- Updated README, VISION, and CHANGES.

## Verification

- Negative: `python3 -m pytest -q tests/test_app.py::test_main_file_uploader_documents_upload_limit`
  failed before the UI fix because no uploader help text was configured.
- `python3 -m pytest -q tests/test_app.py::test_main_file_uploader_documents_upload_limit`
- `python3 -m py_compile app.py`
- `python3 scripts/check_docs_plans.py`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Add setup notes for ffmpeg and first-run Whisper model downloads.
- Add manual verification notes for common browser upload flows.
