# Upload Name Fallback

## Status: Completed

## Context

The uploaded filename is only used to choose a temporary-file suffix. If a
malformed upload object raised while exposing its `name`, suffix detection could
fail before the app reached its sanitized upload validation path.

## Objectives

- Treat uploaded filenames as optional metadata.
- Fall back to the existing `.audio` suffix when filename inspection fails.
- Keep upload bytes validation and temp-file cleanup unchanged.
- Add regression and static coverage for the fallback behavior.

## Work Completed

- Wrapped upload suffix detection in a defensive exception boundary.
- Added a no-model regression test for uploads whose `name` property raises.
- Extended `scripts/check_docs_plans.py` to require the fallback guard and test.
- Updated README, VISION, and CHANGES.

## Verification

- Negative: `python3 -m pytest -q tests/test_app.py` failed before the helper
  fix because a failing upload `name` property escaped as a raw exception.
- `python3 -m py_compile app.py`
- `python3 scripts/check_docs_plans.py`
- `python3 -m pytest -q tests/test_app.py`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Add a user-facing note that unsupported or unreadable filenames do not affect
  upload content validation.
- Consider a dedicated upload metadata sanitizer if more filename-derived
  behavior is added.
