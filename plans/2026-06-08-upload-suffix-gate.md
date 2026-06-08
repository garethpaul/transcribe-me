# Upload Suffix Gate

## Problem

Uploaded audio was written to a temporary file using the last filename segment
after `.` as the suffix. That preserved arbitrary casing and unsupported
extensions from user-controlled upload names.

## TDD Evidence

1. Added tests for supported suffix normalization plus unsupported and missing
   suffix fallback.
2. Ran the focused app tests before implementation and confirmed uppercase and
   unsupported suffix handling failed.
3. Added a small suffix sanitizer backed by the app's allowed audio types and
   reran the full verification gate.

## Verification

- `make lint`
- `python3 -m pytest -q tests/test_app.py`
- `make test`
- `make build`
- `make verify`
- `git diff --check`
