#!/usr/bin/env python3
from pathlib import Path
import re
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
LOCK_TIMEOUT_PLAN = DOCS_PLANS / "2026-06-12-transcription-lock-timeout.md"
LOCK_BEFORE_TEMPFILE_PLAN = DOCS_PLANS / "2026-06-12-lock-before-tempfile.md"
TRUNCATED_AUDIO_PLAN = DOCS_PLANS / "2026-06-13-truncated-audio-containers.md"
FFPROBE_STDIN_PLAN = DOCS_PLANS / "2026-06-13-ffprobe-stdin-isolation.md"
FFPROBE_STDERR_PLAN = DOCS_PLANS / "2026-06-17-ffprobe-stderr-boundary.md"
FFPROBE_FILE_BACKED_PLAN = DOCS_PLANS / "2026-06-26-file-backed-ffprobe-output.md"
ROOT_OVERRIDE_PLAN = DOCS_PLANS / "2026-06-14-make-root-override-protection.md"
DEEP_REVIEW_PLAN = DOCS_PLANS / "2026-06-19-audio-ingestion-deep-review.md"
MAKE_AUTHORITY_PLAN = DOCS_PLANS / "2026-06-21-make-authority-isolation.md"

MAKE_BOUNDARY_README = (
    "Caller-supplied `MAKEFILES`, extra `-f` files, target-specific variables, shell "
    "overrides, and replaced public-target recipes are outside the local Make trust boundary."
)
MAKE_BOUNDARY_PYTHON = (
    "`python3` is resolved from the caller's `PATH` unless `PYTHON=/absolute/path` is supplied."
)
MAKE_BOUNDARY_STARTUP = (
    "Startup makefiles can execute while GNU Make is parsing, before the repository Makefile "
    "can reject them."
)
MAKE_BOUNDARY_CHANGES = (
    "Narrowed Make authority claims to the sole checked-in Makefile path; caller-supplied "
    "makefiles, recipe replacements, target-specific shell overrides, and PATH-shadowed "
    "Python remain outside that boundary."
)

# Whole-line, tab-anchored recipe pins. A substring pin is a PREFIX pin: it still matches
# after ` || true`, `; true`, or a leading `-` is appended, all of which discard the
# command's exit status while the command still runs and still logs a dispatch. Every
# command `make check` relies on must appear as an EXACT line, exactly once.
MAKEFILE_RECIPE_LINES = (
    '\tcd "$$ROOT" && "$$PYTHON" -I -B -m ruff format --check .',
    '\tcd "$$ROOT" && "$$PYTHON" -I -B -m ruff check .',
    '\t"$$PYTHON" -I -B -m compileall -q "$$ROOT/app.py" "$$ROOT/scripts" "$$ROOT/tests"',
    '\t"$$PYTHON" -I -B "$$ROOT/scripts/check_docs_plans.py"',
    '\t"$$PYTHON" -I -B "$$ROOT/scripts/test_ffprobe_stderr_contract.py"',
    '\t"$$PYTHON" -I -B "$$ROOT/scripts/test_audio_boundary_contract.py"',
    '\tcd "$$ROOT" && "$$PYTHON" -I -B -c \'import sys, pytest; sys.path.insert(0, "."); '
    'raise SystemExit(pytest.main(["-q"]))\'',
    '\t"$$PYTHON" -I -B -m py_compile "$$ROOT/app.py"',
    '\tenv -u PYTHONPATH "$$PYTHON" -I -B -m pip check',
    '\tenv -u PYTHONPATH "$$PYTHON" -I -B -m pip_audit --requirement '
    '"$$ROOT/requirements.txt" --no-deps --disable-pip',
    '\t/bin/sh "$$ROOT/scripts/test-makefile-root.sh"',
    '\t/bin/sh "$$ROOT/scripts/test-makefile-boundary.sh"',
)
MAKEFILE_RULE_LINES = (
    "format:",
    "lint:",
    "test:",
    "build:",
    "audit:",
    "root-test:",
    "verify: root-test format lint test build",
    "check: verify audit",
)


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
    if not LOCK_TIMEOUT_PLAN.exists():
        failures.append("docs/plans/2026-06-12-transcription-lock-timeout.md is missing")
    if not LOCK_BEFORE_TEMPFILE_PLAN.exists():
        failures.append("docs/plans/2026-06-12-lock-before-tempfile.md is missing")
    if not TRUNCATED_AUDIO_PLAN.exists():
        failures.append("docs/plans/2026-06-13-truncated-audio-containers.md is missing")
    if not FFPROBE_STDIN_PLAN.exists():
        failures.append("docs/plans/2026-06-13-ffprobe-stdin-isolation.md is missing")
    if not FFPROBE_STDERR_PLAN.exists():
        failures.append("docs/plans/2026-06-17-ffprobe-stderr-boundary.md is missing")
    if not FFPROBE_FILE_BACKED_PLAN.exists():
        failures.append("docs/plans/2026-06-26-file-backed-ffprobe-output.md is missing")
    if not ROOT_OVERRIDE_PLAN.exists():
        failures.append("docs/plans/2026-06-14-make-root-override-protection.md is missing")
    if not DEEP_REVIEW_PLAN.exists():
        failures.append("docs/plans/2026-06-19-audio-ingestion-deep-review.md is missing")
    if not MAKE_AUTHORITY_PLAN.exists():
        failures.append("docs/plans/2026-06-21-make-authority-isolation.md is missing")
    make_authority_runner = ROOT / "scripts" / "test-makefile-root.sh"
    if not make_authority_runner.exists() or not (make_authority_runner.stat().st_mode & 0o111):
        failures.append("scripts/test-makefile-root.sh must exist and be executable")
    make_boundary_runner = ROOT / "scripts" / "test-makefile-boundary.sh"
    if not make_boundary_runner.exists() or not (make_boundary_runner.stat().st_mode & 0o111):
        failures.append("scripts/test-makefile-boundary.sh must exist and be executable")

    plans = sorted(DOCS_PLANS.glob("*.md")) if DOCS_PLANS.exists() else []
    if not plans:
        failures.append("docs/plans must contain at least one completed plan")

    for plan_path in plans:
        plan = plan_path.read_text(encoding="utf-8")
        if "Status: Completed" not in plan or "make check" not in plan:
            failures.append(
                f"{plan_path.relative_to(ROOT)} must record completed status and make check verification"
            )

    documentation_contracts = {
        "README.md": (
            "null device instead of inherited",
            "private temporary file",
            "at most 4 KiB into memory",
        ),
        "SECURITY.md": (
            "null device rather than inherited",
            "Probe stdout is written to a private",
            "read into memory only when it is at",
        ),
        "VISION.md": (
            "Keep media-probe subprocesses non-interactive",
            "Keep ffprobe metadata file-backed",
        ),
    }
    for relative_path, contracts in documentation_contracts.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for contract in contracts:
            if contract not in text:
                failures.append(f"{relative_path} must document ffprobe boundary: {contract}")

    boundary_contracts = {
        "README.md": (MAKE_BOUNDARY_README, MAKE_BOUNDARY_PYTHON),
        "docs/plans/2026-06-21-make-authority-isolation.md": (
            MAKE_BOUNDARY_STARTUP,
            "It also does not claim to sandbox arbitrary caller-supplied Make programs.",
        ),
        "CHANGES.md": (MAKE_BOUNDARY_CHANGES,),
    }
    for relative_path, contracts in boundary_contracts.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for contract in contracts:
            if contract not in text:
                failures.append(f"{relative_path} must document Make boundary: {contract}")
    forbidden_make_overclaims = {
        "README.md": (
            "isolated Make startup, shell, trusted-Python, and target authority across every gate",
        ),
        "CHANGES.md": (
            "Isolated Make verification authority from caller-controlled roots, shells, startup files",
        ),
    }
    for relative_path, overclaims in forbidden_make_overclaims.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for overclaim in overclaims:
            if overclaim in text:
                failures.append(f"{relative_path} still overclaims Make boundary: {overclaim}")

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
        "def has_complete_riff_header(data):",
        "riff_size + 8 <= len(data)",
        "def has_complete_ftyp_box(data):",
        "16 <= box_size <= len(data)",
        "def id3_audio_offset(data):",
        "audio_offset > len(data)",
        "has_mp3_frame_header(data, audio_offset)",
        "def validated_audio_suffix(uploaded_file, data):",
        "def ensure_ffmpeg_available():",
        "def ensure_ffprobe_available():",
        "MAX_AUDIO_DURATION_SECONDS = 15 * 60",
        "MAX_FFPROBE_STDOUT_BYTES = 4096",
        "MAX_AUDIO_CHANNELS = 2",
        "MAX_AUDIO_SAMPLE_RATE_HZ = 96_000",
        "MAX_DECODED_SAMPLES = 86_400_000",
        "def probe_audio_duration(audio_path, ffprobe_path):",
        "def validate_probe_metadata(metadata, audio_path):",
        "def ensure_private_regular_audio_file(audio_path):",
        "stdin=subprocess.DEVNULL",
        'with tempfile.TemporaryFile(mode="w+b") as probe_output:',
        "stdout=probe_output",
        "stderr=subprocess.DEVNULL",
        "timeout=FFPROBE_TIMEOUT_SECONDS",
        "probe_output.seek(0, os.SEEK_END)",
        "probe_output.tell() > MAX_FFPROBE_STDOUT_BYTES",
        "probe_output.read(MAX_FFPROBE_STDOUT_BYTES)",
        "duration > MAX_AUDIO_DURATION_SECONDS",
        "duration * channels * sample_rate > MAX_DECODED_SAMPLES",
        "data, suffix = validated_uploaded_audio(uploaded_file)",
        "TRANSCRIPTION_LOCK = threading.Lock()",
        "TRANSCRIPTION_ADMISSION = threading.BoundedSemaphore(2)",
        "TRANSCRIPTION_LOCK_TIMEOUT_SECONDS = 30",
        "def transcribe_with_lock(model, data, suffix, ffprobe_path):",
        "TRANSCRIPTION_LOCK.acquire(timeout=TRANSCRIPTION_LOCK_TIMEOUT_SECONDS)",
        "audio_path = write_audio_bytes(data, suffix)",
        "probe_audio_duration(audio_path, ffprobe_path)",
        "if audio_path is not None:",
        "TRANSCRIPTION_LOCK.release()",
    ):
        if contract not in app_source:
            failures.append(f"app.py must keep audio validation contract: {contract}")

    if "capture_output=True" in app_source or "stdout=subprocess.PIPE" in app_source:
        failures.append("ffprobe must not capture unused stderr in memory")

    if not re.search(r"^FFPROBE_TIMEOUT_SECONDS = 10$", app_source, re.MULTILINE):
        failures.append("app.py must keep the exact 10-second ffprobe timeout")

    streamlit_config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    if "maxUploadSize = 25" not in streamlit_config:
        failures.append("Streamlit must reject uploads above the app's 25 MB limit")

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    root_declaration = "override ROOT := $(shell path='$(subst ','\"'\"',$(value MAKEFILE_LIST))'"
    root_assignments = re.findall(r"^(?:override\s+)?ROOT\s*[:+?]?=", makefile, re.MULTILINE)
    if len(root_assignments) != 1 or makefile.count(root_declaration) != 1:
        failures.append("Makefile must contain exactly one protected repository-root declaration")
    python_declaration = "PYTHON ?= python3\noverride PYTHON := $(value PYTHON)\nexport PYTHON"
    if makefile.count(python_declaration) != 1 or makefile.find(python_declaration) > makefile.find(
        root_declaration
    ):
        failures.append(
            "Makefile must freeze the Python override before resolving the protected root"
        )
    makefile_lines = makefile.splitlines()
    for recipe_line in MAKEFILE_RECIPE_LINES:
        occurrences = makefile_lines.count(recipe_line)
        if occurrences != 1:
            failures.append(
                "Makefile must dispatch this command as an exact, unmodified line "
                f"exactly once (found {occurrences}): {recipe_line!r}"
            )
    for rule_line in MAKEFILE_RULE_LINES:
        occurrences = makefile_lines.count(rule_line)
        if occurrences != 1:
            failures.append(
                "Makefile must declare this rule as an exact line exactly once "
                f"(found {occurrences}): {rule_line!r}"
            )
    for contract in (
        ".DEFAULT_GOAL := check",
        ".PHONY: __repository-make-authority audit build check format lint root-test test verify",
        "PYTHON must be a literal executable path, not Make syntax",
        "override SHELL := /bin/sh",
        "MAKEFLAGS must not be overridden for repository verification",
        "non-executing or error-ignoring MAKEFLAGS are not supported",
        "MAKEFILES must be empty",
        "MAKEFILE_LIST must not be overridden",
        "repository Makefile must be loaded alone",
        "audit build check format lint root-test test verify: __repository-make-authority",
        "root-test:",
        '"$$ROOT/scripts/test-makefile-root.sh"',
        '"$$ROOT/scripts/test-makefile-boundary.sh"',
        "verify: root-test format lint test build",
        "check: verify audit",
        'cd "$$ROOT" && "$$PYTHON" -I -B -m ruff format --check .',
        'cd "$$ROOT" && "$$PYTHON" -I -B -m ruff check .',
        '"$$PYTHON" -I -B -m compileall -q "$$ROOT/app.py" "$$ROOT/scripts" "$$ROOT/tests"',
        '"$$PYTHON" -I -B "$$ROOT/scripts/check_docs_plans.py"',
        '"$$PYTHON" -I -B "$$ROOT/scripts/test_audio_boundary_contract.py"',
        'cd "$$ROOT" && "$$PYTHON" -I -B -c \'import sys, pytest; sys.path.insert(0, "."); raise SystemExit(pytest.main(["-q"]))\'',
        '"$$PYTHON" -I -B -m py_compile "$$ROOT/app.py"',
        'env -u PYTHONPATH "$$PYTHON" -I -B -m pip check',
        'pip_audit --requirement "$$ROOT/requirements.txt" --no-deps --disable-pip',
    ):
        if contract not in makefile:
            failures.append(f"Makefile verification contract is missing: {contract}")

    if "docs/plans/2026-06-14-make-root-override-protection.md" not in (
        ROOT / "README.md"
    ).read_text(encoding="utf-8"):
        failures.append("README.md must index Make root override protection evidence")
    if "docs/plans/2026-06-21-make-authority-isolation.md" not in (ROOT / "README.md").read_text(
        encoding="utf-8"
    ):
        failures.append("README.md must index Make authority isolation evidence")

    workflow = (ROOT / ".github" / "workflows" / "check.yml").read_text(encoding="utf-8")
    workflow_files = sorted((ROOT / ".github" / "workflows").glob("*"))
    if workflow_files != [ROOT / ".github" / "workflows" / "check.yml"]:
        failures.append("GitHub Actions must contain only the reviewed check workflow")
    if "workflow_dispatch:" not in workflow:
        failures.append("GitHub Actions must support manual verification runs")
    for contract in (
        "concurrency:",
        "cancel-in-progress: true",
        "runs-on: ubuntu-24.04",
        "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0",
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0",
        "run: /usr/bin/make check",
        "run: /bin/sh scripts/test-makefile-root.sh",
    ):
        if contract not in workflow:
            failures.append(f"GitHub Actions verification contract is missing: {contract}")
    # The failure-injection observer runs inside `make check`'s own blast radius: if the
    # root-test recipe line stops propagating its exit status, the observer still prints its
    # diagnosis but `make check` reports success. A second, independent CI step runs the same
    # observer out of band, where no Makefile recipe can discard its verdict.
    if "continue-on-error" in workflow:
        failures.append("GitHub Actions must not discard a step verdict with continue-on-error")
    if workflow.count("uses: actions/checkout@") != 1:
        failures.append("GitHub Actions must contain exactly one checkout step")
    if workflow.count("uses: actions/setup-python@") != 1:
        failures.append("GitHub Actions must contain exactly one Python setup step")
    if workflow.count("permissions:") != 1 or "permissions:\n  contents: read" not in workflow:
        failures.append("GitHub Actions must keep one top-level read-only permissions block")
    if "persist-credentials: false" not in workflow:
        failures.append("GitHub Actions checkout must not persist credentials")
    if "pull_request_target:" in workflow or "permissions: write-all" in workflow:
        failures.append("GitHub Actions must not use privileged triggers or write-all")
    if re.search(r"^[ \t]+[A-Za-z0-9_-]+:[ \t]+write(?:[ \t]+#.*)?$", workflow, re.MULTILINE):
        failures.append("GitHub Actions must not grant write permissions")

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
    if (
        "test_write_uploaded_file_rejects_truncated_audio_declarations_before_tempfile"
        not in tests_source
    ):
        failures.append("tests must reject truncated audio declarations before tempfile writes")
    if "test_transcribe_uploaded_file_checks_ffmpeg_before_loading_model" not in tests_source:
        failures.append("tests must cover missing ffmpeg before model loading")
    if "test_transcribe_uploaded_file_checks_ffprobe_before_tempfile" not in tests_source:
        failures.append("tests must cover missing ffprobe before temporary-file creation")
    if "test_probe_audio_duration_uses_bounded_json_probe" not in tests_source:
        failures.append("tests must cover the bounded ffprobe command")
    for contract in (
        '"stdin": subprocess.DEVNULL',
        'assert calls[0][1]["stdout"].closed',
        '"stderr": subprocess.DEVNULL',
    ):
        if contract not in tests_source:
            failures.append(f"tests must cover ffprobe pipe isolation: {contract}")
    if "test_probe_audio_duration_rejects_excessive_duration" not in tests_source:
        failures.append("tests must cover the maximum audio duration")
    if "test_probe_audio_duration_sanitizes_probe_failures" not in tests_source:
        failures.append("tests must sanitize ffprobe failures")
    if "test_transcribe_uploaded_file_rejects_long_audio_before_model_load" not in tests_source:
        failures.append("tests must reject long audio before model loading")
    if "test_transcribe_uploaded_file_serializes_shared_model_calls" not in tests_source:
        failures.append("tests must cover serialized access to the cached Whisper model")
    if (
        "test_transcribe_uploaded_file_bounds_lock_wait_before_tempfile_creation"
        not in tests_source
    ):
        failures.append("tests must cover bounded lock waiting before temp-file creation")
    if "test_transcribe_uploaded_file_releases_lock_after_write_failure" not in tests_source:
        failures.append("tests must cover lock release after temp-file write failure")
    if "test_transcribe_uploaded_file_releases_acquired_lock" not in tests_source:
        failures.append("tests must cover lock release after model calls")
    if "test_main_reports_busy_transcription_message" not in tests_source:
        failures.append("tests must cover the user-facing lock timeout message")
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
