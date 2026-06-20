#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def contract_errors(source, tests):
    errors = []
    source_contracts = (
        "MAX_FFPROBE_STDOUT_BYTES = 4096",
        "len(completed.stdout) > MAX_FFPROBE_STDOUT_BYTES",
        '"-select_streams",',
        '"a:0",',
        'codec_name.startswith("pcm_")',
        'elif suffix == ".m4a":',
        '"aac",',
        '"alac",',
        "1 <= channels <= MAX_AUDIO_CHANNELS",
        "1 <= sample_rate <= MAX_AUDIO_SAMPLE_RATE_HZ",
        "duration * channels * sample_rate > MAX_DECODED_SAMPLES",
        "os.lstat(audio_path)",
        "stat.S_IMODE(metadata.st_mode) & 0o077",
        "TRANSCRIPTION_ADMISSION = threading.BoundedSemaphore(2)",
        "TRANSCRIPTION_ADMISSION.acquire(blocking=False)",
    )
    for contract in source_contracts:
        if contract not in source:
            errors.append(f"audio boundary source contract is missing: {contract}")
    test_contracts = (
        "test_probe_audio_duration_rejects_oversized_stdout",
        "test_probe_audio_duration_rejects_unsafe_metadata",
        "test_probe_audio_duration_rejects_symlink_before_subprocess",
        "test_write_audio_bytes_creates_private_regular_file",
        "test_transcribe_uploaded_file_rejects_excess_admission_before_lock",
        "test_probe_audio_duration_accepts_synthetic_audio",
        "test_probe_audio_duration_rejects_synthetic_truncated_wav",
    )
    for contract in test_contracts:
        if contract not in tests:
            errors.append(f"audio boundary test contract is missing: {contract}")
    return errors


def main():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tests = (ROOT / "tests" / "test_app.py").read_text(encoding="utf-8")
    baseline_errors = contract_errors(source, tests)
    if baseline_errors:
        raise SystemExit("baseline audio boundary contract failed: " + "; ".join(baseline_errors))

    mutations = {
        "unbounded probe output": (
            "len(completed.stdout) > MAX_FFPROBE_STDOUT_BYTES",
            "len(completed.stdout) < MAX_FFPROBE_STDOUT_BYTES",
        ),
        "all-stream probing": ('"-select_streams",', '"-show_streams",'),
        "non-audio wav codec": ('codec_name.startswith("pcm_")', "bool(codec_name)"),
        "unsupported m4a codec": ('"alac",', '"opus",'),
        "unbounded channels": (
            "1 <= channels <= MAX_AUDIO_CHANNELS",
            "channels >= 1",
        ),
        "unbounded sample rate": (
            "1 <= sample_rate <= MAX_AUDIO_SAMPLE_RATE_HZ",
            "sample_rate >= 1",
        ),
        "unbounded decoded samples": (
            "duration * channels * sample_rate > MAX_DECODED_SAMPLES",
            "False",
        ),
        "symlink-following stat": ("os.lstat(audio_path)", "os.stat(audio_path)"),
        "world-readable temporary input": (
            "stat.S_IMODE(metadata.st_mode) & 0o077",
            "False",
        ),
        "unbounded request admission": (
            "TRANSCRIPTION_ADMISSION = threading.BoundedSemaphore(2)",
            "TRANSCRIPTION_ADMISSION = threading.Semaphore()",
        ),
        "blocking admission": (
            "TRANSCRIPTION_ADMISSION.acquire(blocking=False)",
            "TRANSCRIPTION_ADMISSION.acquire()",
        ),
    }
    for name, (old, new) in mutations.items():
        mutated = source.replace(old, new, 1)
        if mutated == source:
            raise SystemExit(f"mutation setup failed for {name}")
        if not contract_errors(mutated, tests):
            raise SystemExit(f"audio boundary contract accepted {name}")

    print(f"audio boundary contract passed ({len(mutations)} mutations rejected)")


if __name__ == "__main__":
    main()
