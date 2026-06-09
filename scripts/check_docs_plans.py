#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
DOCS_PLANS = ROOT / "docs" / "plans"
CANONICAL_PLAN = DOCS_PLANS / "2026-06-08-transcribe-me-baseline.md"
UPLOAD_WRITE_PLAN = DOCS_PLANS / "2026-06-09-upload-write-cleanup.md"
UPLOAD_LIMIT_HINT_PLAN = DOCS_PLANS / "2026-06-09-upload-limit-help.md"


def main():
    failures = []

    if not CANONICAL_PLAN.exists():
        failures.append("docs/plans/2026-06-08-transcribe-me-baseline.md is missing")

    if not UPLOAD_WRITE_PLAN.exists():
        failures.append("docs/plans/2026-06-09-upload-write-cleanup.md is missing")
    if not UPLOAD_LIMIT_HINT_PLAN.exists():
        failures.append("docs/plans/2026-06-09-upload-limit-help.md is missing")

    plans = sorted(DOCS_PLANS.glob("*.md")) if DOCS_PLANS.exists() else []
    if not plans:
        failures.append("docs/plans must contain at least one completed plan")

    for plan_path in plans:
        plan = plan_path.read_text(encoding="utf-8")
        if "Status: Completed" not in plan or "make check" not in plan:
            failures.append(f"{plan_path.relative_to(ROOT)} must record completed status and make check verification")

    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    if "st.text(transcript)" not in app_source:
        failures.append("app.py must render transcript output as plain text")
    if (
        "UPLOAD_WRITE_FAILURE_MESSAGE" not in app_source
        or "os.unlink(audio_path)" not in app_source
    ):
        failures.append("app.py must clean up temp files after upload write failures")
    if "UPLOAD_HELP_TEXT" not in app_source or "help=UPLOAD_HELP_TEXT" not in app_source:
        failures.append("app.py must show the upload byte limit in the file uploader help")

    tests_source = (ROOT / "tests" / "test_app.py").read_text(encoding="utf-8")
    if "test_write_uploaded_file_cleans_up_after_write_error" not in tests_source:
        failures.append("tests must cover temp-file cleanup after upload write errors")
    if "test_main_reports_upload_write_failure_without_raw_exception" not in tests_source:
        failures.append("tests must cover user-facing upload write errors")
    if "test_main_file_uploader_documents_upload_limit" not in tests_source:
        failures.append("tests must cover upload limit help text")

    if failures:
        print("Documentation plan checks failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Documentation plan checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
