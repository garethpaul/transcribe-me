#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
DOCS_PLANS = ROOT / "docs" / "plans"
CANONICAL_PLAN = DOCS_PLANS / "2026-06-08-transcribe-me-baseline.md"
UPLOAD_WRITE_PLAN = DOCS_PLANS / "2026-06-09-upload-write-cleanup.md"
UPLOAD_LIMIT_HINT_PLAN = DOCS_PLANS / "2026-06-09-upload-limit-help.md"
UPLOAD_NAME_PLAN = DOCS_PLANS / "2026-06-09-upload-name-fallback.md"
AUDIO_SIGNATURE_PLAN = DOCS_PLANS / "2026-06-10-audio-signature-and-ci.md"
CONCURRENCY_PLAN = DOCS_PLANS / "2026-06-10-transcription-concurrency.md"
CLEANUP_ERROR_PLAN = DOCS_PLANS / "2026-06-10-temp-cleanup-errors.md"


def main():
    failures = []

    if not CANONICAL_PLAN.exists():
        failures.append("docs/plans/2026-06-08-transcribe-me-baseline.md is missing")

    if not UPLOAD_WRITE_PLAN.exists():
        failures.append("docs/plans/2026-06-09-upload-write-cleanup.md is missing")
    if not UPLOAD_LIMIT_HINT_PLAN.exists():
        failures.append("docs/plans/2026-06-09-upload-limit-help.md is missing")
    if not UPLOAD_NAME_PLAN.exists():
        failures.append("docs/plans/2026-06-09-upload-name-fallback.md is missing")
    if not AUDIO_SIGNATURE_PLAN.exists():
        failures.append("docs/plans/2026-06-10-audio-signature-and-ci.md is missing")
    if not CONCURRENCY_PLAN.exists():
        failures.append("docs/plans/2026-06-10-transcription-concurrency.md is missing")
    if not CLEANUP_ERROR_PLAN.exists():
        failures.append("docs/plans/2026-06-10-temp-cleanup-errors.md is missing")

    plans = sorted(DOCS_PLANS.glob("*.md")) if DOCS_PLANS.exists() else []
    if not plans:
        failures.append("docs/plans must contain at least one completed plan")

    for plan_path in plans:
        plan = plan_path.read_text(encoding="utf-8")
        if "Status: Completed" not in plan or "make check" not in plan:
            failures.append(
                f"{plan_path.relative_to(ROOT)} must record completed status and make check verification"
            )

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
    for contract in (
        "def remove_audio_file(audio_path, cleanup_error):",
        "def detected_audio_suffix(data):",
        "def validated_audio_suffix(uploaded_file, data):",
        "def ensure_ffmpeg_available():",
        "data, suffix = validated_uploaded_audio(uploaded_file)",
        "TRANSCRIPTION_LOCK = threading.Lock()",
        "with TRANSCRIPTION_LOCK:",
    ):
        if contract not in app_source:
            failures.append(f"app.py must keep audio validation contract: {contract}")

    streamlit_config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    if "maxUploadSize = 25" not in streamlit_config:
        failures.append("Streamlit must reject uploads above the app's 25 MB limit")

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for contract in (
        "ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))",
        "env -u PYTHONPATH $(PYTHON) -m pip check",
        'pip_audit --requirement "$(ROOT)/requirements.txt" --no-deps --disable-pip',
    ):
        if contract not in makefile:
            failures.append(f"Makefile verification contract is missing: {contract}")

    workflow = (ROOT / ".github" / "workflows" / "check.yml").read_text(encoding="utf-8")
    if "workflow_dispatch:" not in workflow:
        failures.append("GitHub Actions must support manual verification runs")
    for contract in (
        "concurrency:",
        "cancel-in-progress: true",
        "runs-on: ubuntu-24.04",
        "actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3",
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0",
    ):
        if contract not in workflow:
            failures.append(f"GitHub Actions verification contract is missing: {contract}")

    tests_source = (ROOT / "tests" / "test_app.py").read_text(encoding="utf-8")
    if "test_write_uploaded_file_cleans_up_after_write_error" not in tests_source:
        failures.append("tests must cover temp-file cleanup after upload write errors")
    if "test_main_reports_upload_write_failure_without_raw_exception" not in tests_source:
        failures.append("tests must cover user-facing upload write errors")
    if "test_main_file_uploader_documents_upload_limit" not in tests_source:
        failures.append("tests must cover upload limit help text")
    if "test_write_uploaded_file_infers_suffix_when_name_fails" not in tests_source:
        failures.append("tests must cover content-derived suffixes when upload names fail")
    if "test_write_uploaded_file_rejects_extension_mismatch" not in tests_source:
        failures.append("tests must cover filename and content mismatches")
    if "test_transcribe_uploaded_file_checks_ffmpeg_before_loading_model" not in tests_source:
        failures.append("tests must cover missing ffmpeg before model loading")
    if "test_transcribe_uploaded_file_serializes_shared_model_calls" not in tests_source:
        failures.append("tests must cover serialized access to the cached Whisper model")
    if "test_transcribe_uploaded_file_sanitizes_temp_cleanup_errors" not in tests_source:
        failures.append("tests must cover sanitized transcription cleanup errors")
    if "test_write_uploaded_file_sanitizes_cleanup_errors_after_write_failure" not in tests_source:
        failures.append("tests must cover sanitized upload-write cleanup errors")

    if failures:
        print("Documentation plan checks failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Documentation plan checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
