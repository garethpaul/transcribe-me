# Changes

## 2026-07-17 09:30 PDT - P1 - Observe verification failure propagation

### Summary

The Make authority harness asserted that every public target *dispatched* its
verification commands, but its stand-in interpreter always exited `0`, so no
check ever observed `make check` *gating*. Appending `|| true` to the `test:`
recipe kept every existing pin byte-identical and shipped a failing test suite
green: pytest printed `2 failed` and `make check` exited `0`. Added 34
failure-injection propagation cases, tab-anchored whole-line recipe pins, an
out-of-band CI observer step, and `continue-on-error` rejection.

### Work completed

- Injected per-invocation failures into every command `make check` dispatches and
  required the invoking target to report failure, replacing dispatch-only
  observation of the exit-status channel.
- Upgraded substring Makefile recipe contracts to tab-anchored whole-line pins so
  an appended `|| true`, `; true`, or leading `-` can no longer prefix-match.
- Added an independent out-of-band CI step running the authority harness, plus
  `test` target cross-guards, so a neutered `root-test` recipe cannot discard the
  observer's own verdict.

## 2026-06-26 10:12 PDT - P1 - Keep ffprobe output file-backed

### Summary

Replaced ffprobe's in-memory stdout pipe with a private temporary file so an
unexpected child-output volume is not buffered in application memory before
the existing 4 KiB accepted-metadata limit is enforced.

### Work completed

- Redirected fixed-shape ffprobe JSON to a private binary temporary file.
- Checked the complete file size before reading and decoding at most 4 KiB.
- Added regression and hostile-mutation coverage for restoring an in-memory
  pipe, removing the size check, or introducing an unbounded read.

### Threads

- None; the bounded change was implemented directly with focused TDD.

### Files changed

- `app.py` — made ffprobe stdout file-backed and bounded the metadata read.
- `tests/test_app.py` — exercised file-backed output, closure, and rejection.
- `scripts/test_audio_boundary_contract.py` — enforced the new memory boundary.
- `scripts/test_ffprobe_stderr_contract.py` — retained stderr discard coverage.
- `scripts/check_docs_plans.py` — synchronized source and test contracts.
- `README.md`, `SECURITY.md`, `VISION.md` — documented the precise boundary.
- `docs/plans/2026-06-26-file-backed-ffprobe-output.md` — recorded the work.

### Validation

- 28 focused ffprobe-duration tests passed.
- 13 hostile audio-boundary and four hostile stderr-boundary mutations passed.
- Full pinned repository and external-directory `make check` passed under
  Python 3.10.20 and Python 3.12.3 with 90 tests per invocation.
- Hosted Check run `28253655385` and CodeQL run `28253653906` passed on
  implementation commit `e16ed2142bcefcf4263464d1d6d081565567dce9`.

### Bugs / findings

- P1: `subprocess.PIPE` buffered all stdout before the former 4 KiB check ran.
- The ten-second subprocess timeout remains the total-output growth boundary;
  this change specifically bounds application-memory ingestion, not disk use.

### Blockers

- Codex review was attempted once and skipped after the local CLI returned HTTP
  401 for both WebSocket and HTTPS transports.

### Next action

- Require hosted checks on the exact PR head, merge that SHA, and confirm the
  default-branch checks remain green.

## 2026-06-26 03:55 PDT - P2 - Reject unsafe thread-only model timeout

### Summary

Reviewed the remaining total-processing-time roadmap item and rejected a
thread/future timeout because it cannot stop a running Whisper call and could
release the shared-model lock while inference still uses the cached model.

### Work completed

- Traced admission, lock ownership, temporary-file lifetime, probe bounds, and
  model invocation in `app.py` and the associated concurrency regressions.
- Confirmed that a real total model-call bound requires an isolated worker that
  can be terminated without violating cached-model or temporary-file ownership.

### Threads

- None; the review was completed directly to avoid speculative implementation.

### Files changed

- `CHANGES.md` — recorded the rejected unsafe approach and required next design.

### Validation

- Manual source and test review — confirmed the lock currently spans the full
  model call and cleanup, and that a returning thread timeout cannot cancel it.
- `python3 -I -B scripts/check_docs_plans.py` — passed.

### Bugs / findings

- P2: the documented 15-minute input bound is not a total processing deadline.
- A thread-only timeout would create a false guarantee and unsafe lock release.

### Blockers

- Safe enforcement needs a process-isolated inference design plus real-model
  smoke evidence for startup cost, termination, and cross-platform behavior.

### Next action

- Design and validate process-isolated inference before promising a total
  processing-time bound; do not add a non-cancelling thread timeout.

## 2026-06-21

- Narrowed Make authority claims to the sole checked-in Makefile path; caller-supplied makefiles, recipe replacements, target-specific shell overrides, and PATH-shadowed Python remain outside that boundary.
- Kept adversarial coverage for the checked-in Makefile path and pinned hosted
  verification dispatch to the absolute system Make binary.

## 2026-06-19

- Added fixed-shape first-audio-stream probing with a 4 KiB output cap and
  container, codec, channel, sample-rate, and duration validation before model
  work, including a combined 86.4-million decoded-sample ceiling.
- Required private regular temporary inputs and added synthetic WAV, MP3, M4A,
  and truncated-audio integration coverage.
- Bounded process admission to one active and one queued transcription request,
  with immediate stable rejection beyond that limit.
- Added eleven hostile mutation contracts for the audio ingestion boundary.
- Updated current compatible maintenance pins: PyArrow 24.0.0, pip-audit
  2.10.1, pytest 9.1.1, Ruff 0.15.18, and commit-pinned checkout v7.0.0.

## 2026-06-17

- Retained only ffprobe duration JSON stdout and discarded unused diagnostics
  instead of buffering stderr in application memory.

## 2026-06-13

- Disconnected ffprobe stdin from the Streamlit process while retaining the
  existing ten-second probe timeout.
- Added a 10-second `ffprobe` preflight that rejects invalid duration metadata
  and audio longer than 15 minutes before Whisper loads or transcribes.
- Rejected truncated RIFF, `ftyp`, and ID3 declarations before temporary-file
  creation while preserving supported WAV, M4A, and MP3 uploads.

## 2026-06-12

- Acquired the shared Whisper lock before writing temporary audio so contended
  requests fail without accumulating sensitive files on disk.
- Bounded waits for the process-wide Whisper inference lock so sessions fail
  with a stable busy response instead of retaining temporary audio indefinitely.
- Added deterministic coverage for timeout propagation, no model invocation on
  contention, temporary-file cleanup, and lock release after model outcomes.

## 2026-06-10

- Sanitized temporary-file deletion failures so filesystem details cannot leak
  after upload writes or transcription attempts.
- Serialized calls to the process-wide cached Whisper model and added a
  deterministic two-thread regression test for concurrent Streamlit sessions.
- Made Makefile targets independent of the caller's directory, added dependency
  consistency checks, and fixed CI to Ubuntu 24.04 with concurrency
  cancellation and version-labeled immutable actions.
- Rejected unsupported audio content and filename/content mismatches before
  model loading or temporary-file creation.
- Derived safe WAV, MP3/MPEG, and M4A temporary suffixes from header bytes when
  upload names are missing or unusable.
- Detected missing system ffmpeg before writing user audio or loading Whisper.
- Enforced the 25 MB limit at the Streamlit server boundary.
- Removed the unrelated Python `ffmpeg` wrapper and pinned the test dependency.
- Upgraded OpenAI Whisper from `20231117` to `20250625` so dependency resolution
  works on Python 3.12.
- Upgraded Streamlit from 1.33.0 to 1.58.0 after resolving its stable API surface
  and Python 3.12 dependencies.
- Pinned PyArrow 24.0.0, outside the CVE-2026-25087 range and containing the
  CVE-2024-52338 fix.
- Upgraded pytest to 9.0.3 to fix CVE-2025-71176 tmpdir handling.
- Upgraded Ruff from 0.6.9 to 0.15.16.
- Added Ruff formatting/linting, least-privilege Python 3.10/3.12 CI, and
  repository contract tests.
- Added CI resolution checks for each pinned direct runtime artifact.
- Added a direct-runtime vulnerability audit and manual GitHub Actions trigger
  without installing the heavyweight Whisper dependency graph.
- Disabled persisted checkout credentials and made the repository contracts
  reject duplicate workflows, unsafe triggers, write permissions, and duplicate
  action steps.
- Ignored local virtual environments, Ruff caches, environment files, and
  Streamlit secrets.

## 2026-06-09

- Added a safe filename-inspection fallback, later strengthened with
  content-derived audio suffixes.
- Added file-uploader help text that advertises the 25 MB upload limit before
  users choose an audio file.
- Render successful transcripts as plain text and added no-network coverage for
  markdown-like transcript output.
- Routed malformed or unreadable upload objects through user-facing upload
  validation before loading Whisper.
- Added tests for missing and failing upload readers.
- Rejected non-byte upload payloads before temporary file writes.
- Added upload validation coverage for unexpected non-byte `getvalue()`
  results.
- Cleaned up temporary files after upload write failures and report a generic
  user-facing save error.
- Added transcript text validation for Whisper results before display.
- Added tests for trimmed, missing, non-string, and blank transcript text.

## 2026-06-08

- Added generic transcription failure handling with temp-file cleanup tests and
  user-facing Streamlit errors.
- Added upload content and size validation before temporary file writes, with
  user-facing Streamlit errors and focused tests.
- Added `make check` as the shared repository verification alias.
- Normalized uploaded audio suffixes to a supported lowercase set before
  writing temporary files.
- Added tests that cover supported upload suffixes, unsupported extensions, and
  missing-name fallback behavior.
- Added a Makefile verification gate for Python syntax checks and focused app
  tests.
- Refactored the Streamlit app so importing `app.py` does not load the Whisper
  model.
- Added temporary audio-file cleanup after transcription.
- Added generated Python artifact ignores and test dependency metadata.
- Added canonical `docs/plans` coverage and a docs-plan checker under
  `make check`.
