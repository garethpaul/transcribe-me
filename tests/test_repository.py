from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_requirements_do_not_install_ffmpeg_python_wrapper():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()

    assert requirements == [
        "streamlit==1.58.0",
        "pyarrow==24.0.0",
        "openai-whisper==20250625",
    ]


def test_test_requirements_are_pinned():
    requirements = (ROOT / "test-requirements.txt").read_text(encoding="utf-8").splitlines()

    assert requirements == [
        "pip==26.1.2",
        "pip-audit==2.10.1",
        "pytest==9.1.1",
        "ruff==0.15.18",
    ]


def test_streamlit_rejects_uploads_above_app_limit():
    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")

    assert "maxUploadSize = 25" in config


def test_local_secrets_and_tool_caches_are_ignored():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    for ignored_path in (".ruff_cache/", ".venv/", ".env", ".streamlit/secrets.toml"):
        assert ignored_path in gitignore


def test_ci_runs_complete_check_with_least_privilege():
    workflow = (ROOT / ".github" / "workflows" / "check.yml").read_text(encoding="utf-8")
    workflow_files = sorted((ROOT / ".github" / "workflows").glob("*"))
    contracts = (
        "permissions:\n  contents: read",
        "workflow_dispatch:",
        "concurrency:",
        "cancel-in-progress: true",
        "runs-on: ubuntu-24.04",
        "timeout-minutes: 10",
        'python-version: ["3.10", "3.12"]',
        "fail-fast: false",
        "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0",
        "persist-credentials: false",
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0",
        "python -m pip install --requirement test-requirements.txt",
        "python -m pip download --no-deps",
        '--dest "${RUNNER_TEMP}/runtime-artifacts"',
        "--requirement requirements.txt",
        "run: /usr/bin/make check",
        "run: /bin/sh scripts/test-makefile-root.sh",
    )

    for contract in contracts:
        assert contract in workflow
    assert "continue-on-error" not in workflow
    assert workflow_files == [ROOT / ".github" / "workflows" / "check.yml"]
    assert workflow.count("uses: actions/checkout@") == 1
    assert workflow.count("uses: actions/setup-python@") == 1
    assert workflow.count("permissions:") == 1
    assert "pull_request_target:" not in workflow
    assert "permissions: write-all" not in workflow
    assert not re.search(
        r"^[ \t]+[A-Za-z0-9_-]+:[ \t]+write(?:[ \t]+#.*)?$", workflow, re.MULTILINE
    )
    assert "@v" not in workflow


def test_make_check_audits_pinned_direct_runtime_dependencies():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "override ROOT := $(shell path=" in makefile
    assert 'env -u PYTHONPATH "$$PYTHON" -I -B -m pip check' in makefile
    assert 'pip_audit --requirement "$$ROOT/requirements.txt" --no-deps --disable-pip' in makefile


def test_make_recipes_do_not_discard_command_exit_status():
    """Cross-guard for the exit-status channel, independent of root-test and lint.

    root-test's failure injection runs inside `make check`'s blast radius, and the
    whole-line recipe pins live in check_docs_plans.py (dispatched by `lint`). If either
    of those recipe lines stopped propagating failures, this test -- dispatched by the
    separate `test` target -- still fails.
    """
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    recipe_lines = [line for line in makefile.splitlines() if line.startswith("\t")]
    assert recipe_lines, "Makefile must contain recipe lines"
    for line in recipe_lines:
        assert "|| true" not in line, f"recipe discards its exit status: {line!r}"
        assert not line.rstrip().endswith("; true"), f"recipe discards its exit status: {line!r}"
        assert not line.startswith("\t-"), f"recipe ignores errors via a leading '-': {line!r}"


def test_make_check_observes_failure_propagation_for_every_public_target():
    """The authority runner must inject real failures, not just observe dispatch."""
    runner = (ROOT / "scripts" / "test-makefile-root.sh").read_text(encoding="utf-8")

    assert "TRANSCRIBE_FAIL_MATCH" in runner
    assert "TRANSCRIBE_FAIL_SCRIPT" in runner
    assert "reported success while the command matching" in runner
    assert '[ "$injected" -eq 34 ]' in runner
    for match in (
        "format verify check|ruff format",
        "lint verify check|ruff check",
        "lint verify check|compileall",
        "lint verify check|check_docs_plans.py",
        "test verify check|pytest.main",
        "build verify check|py_compile",
        "audit check|pip check",
        "audit check|pip_audit",
    ):
        assert match in runner, f"failure injection is missing a case: {match}"


def test_make_check_runs_audio_boundary_mutations():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    mutation_script = ROOT / "scripts" / "test_audio_boundary_contract.py"

    assert '"$$ROOT/scripts/test_audio_boundary_contract.py"' in makefile
    assert mutation_script.is_file()
