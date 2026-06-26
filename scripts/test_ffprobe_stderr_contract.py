#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def contract_errors(source, tests):
    errors = []
    for fragment in (
        "stdin=subprocess.DEVNULL",
        "stdout=probe_output",
        "stderr=subprocess.DEVNULL",
        "timeout=FFPROBE_TIMEOUT_SECONDS",
    ):
        if fragment not in source:
            errors.append(f"ffprobe source contract is missing: {fragment}")
    if "capture_output=True" in source:
        errors.append("ffprobe must not buffer stderr through capture_output")
    for fragment in (
        '"stdin": subprocess.DEVNULL',
        'assert calls[0][1]["stdout"].closed',
        '"stderr": subprocess.DEVNULL',
        '"timeout": 10',
    ):
        if fragment not in tests:
            errors.append(f"ffprobe test contract is missing: {fragment}")
    return errors


def main():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tests = (ROOT / "tests" / "test_app.py").read_text(encoding="utf-8")
    baseline_errors = contract_errors(source, tests)
    if baseline_errors:
        raise SystemExit("baseline ffprobe stderr contract failed: " + "; ".join(baseline_errors))

    mutations = {
        "combined capture": (
            "stdout=probe_output,\n                stderr=subprocess.DEVNULL,",
            "capture_output=True,",
        ),
        "missing stdout capture": ("stdout=probe_output", "stdout=subprocess.DEVNULL"),
        "buffered stderr": ("stderr=subprocess.DEVNULL", "stderr=subprocess.PIPE"),
        "inherited stderr": ("stderr=subprocess.DEVNULL,", ""),
    }
    for name, (old, new) in mutations.items():
        mutated = source.replace(old, new, 1)
        if mutated == source:
            raise SystemExit(f"mutation setup failed for {name}")
        if not contract_errors(mutated, tests):
            raise SystemExit(f"ffprobe stderr contract accepted {name}")

    print(f"ffprobe stderr contract passed ({len(mutations)} mutations rejected)")


if __name__ == "__main__":
    main()
