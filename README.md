# transcribe-me

<!-- README-OVERVIEW-IMAGE -->
![Project overview](docs/readme-overview.svg)

## Overview

`transcribe-me` is a small Streamlit application that transcribes uploaded audio
with OpenAI Whisper's local `base` model. Uploaded bytes are validated, written
to a temporary file only for transcription, rendered as plain text, and deleted
on both success and failure.

The project is an educational local-processing demo rather than a hosted
transcription service. It does not store transcripts or require an API key.
Local `.env` files and `.streamlit/secrets.toml` are ignored to prevent future
deployment credentials from being committed accidentally.

## Supported Environment

- Python 3.10 or 3.12
- On Linux, a `glibc 2.28+` environment capable of installing current
  manylinux wheels
- The `ffmpeg` and `ffprobe` executables on `PATH`
- Network access on first model use so Whisper can download the `base` weights
- WAV, MP3, MPEG audio, or M4A uploads up to 25 MB

The first transcription is slower because Whisper downloads and caches model
weights. Subsequent transcriptions reuse that local cache.

Runtime dependencies are pinned to Streamlit 1.58.0, PyArrow 24.0.0, and OpenAI
Whisper 20250625. PyArrow 24.0.0 remains outside the affected CVE-2026-25087
range and includes the CVE-2024-52338 fix. Its Linux wheels
target modern manylinux (`glibc 2.28+`).
The Streamlit and Whisper upgrades replace 2024/2023-era releases; the previous
Whisper build metadata fails under the documented Python 3.12 setup.

## Setup

```bash
git clone https://github.com/garethpaul/transcribe-me.git
cd transcribe-me
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install ffmpeg with your operating system package manager, then confirm its
transcription and probing tools are available:

```bash
ffmpeg -version
ffprobe -version
```

The similarly named Python `ffmpeg` package is not required by Whisper and is
intentionally not installed.

## Run

```bash
python -m streamlit run app.py
```

The app advertises and enforces a 25 MB upload limit. It checks common WAV,
MP3/MPEG, and M4A header bytes and their leading declared sizes before creating
a temporary file. If filename
metadata is absent or unusable, the temporary suffix is derived from content;
if a supported filename extension conflicts with detected content, the upload
is rejected. Before Whisper loads, `ffprobe` gets at most 10 seconds to inspect
only the first audio stream and confirm the expected container/codec pair, a
finite positive duration no longer than 15 minutes, at most two channels, and a
sample rate no higher than 96 kHz. The combined duration/channel/rate budget is
capped at 86.4 million decoded samples. Its stdin uses the null device instead of inherited
Streamlit process input. The probe's fixed-shape JSON
stdout is capped at 4 KiB, and unused stderr is discarded rather than buffering
attacker-influenced diagnostics in memory.

## Testing and Verification

Install the pinned test dependencies:

```bash
python -m pip install -r test-requirements.txt
```

Run the complete gate:

```bash
make check
```

Available targets:

- `make format` verifies Ruff formatting.
- `make lint` runs Ruff, compiles application, test, and checker modules, and
  validates the completed maintenance plans.
- `make test` runs the dependency-free pytest suite with fake Streamlit and
  Whisper modules.
- `make build` runs the static build gate.
- `make audit` checks the pinned direct runtime dependencies without installing
  or resolving the heavyweight Whisper and PyTorch dependency graph, and checks
  the installed verification environment for dependency conflicts.
- `make verify` combines lint, test, and build.
- `make check` is the canonical local and CI command, including the
  direct-runtime audit.

The tests cover upload type and size limits, content signatures, filename and
content mismatches, inferred suffixes, sanitized temp-file cleanup failures,
missing ffmpeg/ffprobe, bounded container/codec metadata probing, synthetic
WAV/MP3/M4A fixtures, private regular temporary files, bounded request
admission, serialized access to the cached Whisper model, transcription
failures, transcript validation,
plain-text output, dependency metadata,
Streamlit upload configuration, and CI contracts. GitHub Actions runs `make check` on Python
3.10 and 3.12 with Ubuntu 24.04, read-only permissions, concurrency
cancellation, immutable action references, credential-free checkout, and a
manual trigger. Repository contracts reject extra workflows, unsafe
pull-request triggers, write permissions, and duplicate checkout or Python
setup steps. CI also downloads each pinned direct runtime artifact for both
Python versions without installing the heavyweight ML dependency graph.

## Repository Layout

- `app.py` — Streamlit UI, upload validation, temporary-file handling, and
  Whisper transcription
- `.streamlit/config.toml` — server-side upload limit
- `.github/workflows/check.yml` — hosted verification
- `requirements.txt` — pinned runtime dependencies
- `test-requirements.txt` — pinned test dependency
- `tests/` — focused behavior and repository-contract tests
- `scripts/check_docs_plans.py` — maintenance-plan and safety-contract checker
- `docs/plans/` — completed engineering plans
- `SECURITY.md` — private vulnerability reporting guidance
- `VISION.md` — project direction and contribution guardrails

## Privacy and Security

Audio is sensitive user-provided data. The app does not intentionally send
uploads or transcripts to an external service, but a remotely deployed
Streamlit server still receives the upload. Temporary files are deleted after
transcription and after handled failures; do not treat this demo as a
high-assurance confidential-audio system without reviewing the host, filesystem,
logs, model cache, and process isolation.

Streamlit caches one Whisper model per process. A bounded process-local
admission gate permits one active request and at most one queued request;
additional sessions receive a stable busy response immediately. Transcription
calls are serialized through a process-local lock so concurrent sessions cannot
invoke the shared model at the same time. This protects shared model resources
but is not a production job queue or per-user isolation boundary. The single
queued session waits at most 30 seconds for that lock without creating a
temporary upload or invoking Whisper.

Header and declared-size checks are a bounded defense-in-depth filter, not a
proof that an entire media file is well formed. ffmpeg and Whisper remain the
authoritative parsers. Temporary inputs must remain private regular files. The
metadata probe rejects missing audio, unexpected container/codec pairs,
oversized output, excessive duration, more than two channels, and sample rates
above 96 kHz, including combinations above 86.4 million decoded samples, before
loading or invoking Whisper.
Do not commit real user audio or transcripts.

## Known Limitations

- Live Whisper inference is not exercised in CI because it requires ffmpeg,
  model weights, significant compute, and a real audio fixture.
- The 15-minute duration limit bounds accepted input length but does not stop a
  model call that stalls or otherwise bound total processing time.
- Format detection checks common leading bytes and cannot eliminate malicious
  media-parser risk.
- There is no authentication, multi-user isolation, persistence model, job
  queue, cancellation control, or production deployment configuration.
- Concurrent sessions wait up to 30 seconds for the single process-local
  transcription lock; this bounds queued request retention but does not stop a
  model call that is already running.

## Maintenance Notes

- See `docs/plans/2026-06-08-transcribe-me-baseline.md` for the canonical upload
  and temporary-file baseline.
- See `docs/plans/2026-06-10-audio-signature-and-ci.md` for content validation,
  ffmpeg dependency correction, request limits, and hosted verification.
- See `docs/plans/2026-06-13-truncated-audio-containers.md` for bounded RIFF,
  `ftyp`, and ID3 declaration checks.
- See `docs/plans/2026-06-13-audio-duration-preflight.md` for the bounded
  `ffprobe` and 15-minute input contract.
- See `docs/plans/2026-06-17-ffprobe-stderr-boundary.md` for the discarded
  diagnostic-output boundary.
- See `docs/plans/2026-06-10-transcription-concurrency.md` for serialized access
  to the cached Whisper model.
- See `docs/plans/2026-06-12-transcription-lock-timeout.md` for the bounded
  shared-model wait and cleanup contract.
- See `docs/plans/2026-06-12-lock-before-tempfile.md` for lock acquisition
  before sensitive temporary audio is written.
- See `docs/plans/2026-06-14-make-root-override-protection.md` for repository-
  anchored Make verification under hostile root assignments.
- See `docs/plans/2026-06-21-make-authority-isolation.md` for isolated Make
  startup, shell, trusted-Python, and target authority across every gate.
- See `CHANGES.md` for the maintenance history.

## Contributing

Keep changes focused on upload handling, transcription behavior, dependencies,
errors, or documentation. Add tests for behavior changes, run `make check`, keep
processing local by default, and never commit user recordings, transcripts,
credentials, or model artifacts.
