from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_requirements_do_not_install_ffmpeg_python_wrapper():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()

    assert requirements == [
        "streamlit==1.58.0",
        "pyarrow==23.0.1",
        "openai-whisper==20250625",
    ]


def test_test_requirements_are_pinned():
    requirements = (ROOT / "test-requirements.txt").read_text(encoding="utf-8").splitlines()

    assert requirements == [
        "pip==26.1.2",
        "pip-audit==2.10.0",
        "pytest==9.0.3",
        "ruff==0.15.16",
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
    contracts = (
        "permissions:\n  contents: read",
        "workflow_dispatch:",
        "timeout-minutes: 10",
        'python-version: ["3.10", "3.12"]',
        "fail-fast: false",
        "actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10",
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405",
        "python -m pip install --requirement test-requirements.txt",
        "python -m pip download --no-deps",
        '--dest "${RUNNER_TEMP}/runtime-artifacts"',
        "--requirement requirements.txt",
        "run: make check",
    )

    for contract in contracts:
        assert contract in workflow
    assert "@v" not in workflow


def test_make_check_audits_pinned_direct_runtime_dependencies():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "pip_audit --requirement requirements.txt --no-deps --disable-pip" in makefile
