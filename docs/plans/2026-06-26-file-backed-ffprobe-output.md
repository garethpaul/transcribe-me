# File-Backed ffprobe Output

## Status: Completed

## Goal

Keep ffprobe metadata out of unbounded in-memory subprocess buffering while
preserving the existing 4 KiB accepted-output boundary and ten-second timeout.

## Problem

`probe_audio_duration()` currently passes `stdout=subprocess.PIPE` to
`subprocess.run()`. The completed process therefore buffers all stdout before
the application checks `len(completed.stdout)`. The post-hoc size rejection is
not an in-memory cap and does not match the repository's bounded-output claim.

## Design

1. Capture stdout in a private binary temporary file instead of a pipe.
2. Preserve stdin isolation, stderr discard, the fixed ffprobe command, and
   the ten-second subprocess timeout.
3. Check the file size before reading metadata into memory.
4. Read at most 4 KiB and decode UTF-8 strictly before JSON parsing.
5. Add focused behavior and hostile mutation coverage, then run the complete
   Python 3.10/3.12, audit, and CodeQL gates.

## Verification

- Run all focused ffprobe-duration tests and hostile boundary mutations.
- Run repository and external-directory `make check` with pinned Python 3.10
  and Python 3.12 test environments.
- Audit the exact diff and require hosted checks on the exact PR head.

## Verification Results

- 28 focused ffprobe-duration tests passed.
- Thirteen hostile audio-boundary mutations and four hostile stderr-boundary
  mutations rejected regressions, including restored in-memory pipe capture and
  unbounded reads.
- Repository and external-directory `make check` passed under pinned Python
  3.10.20 and Python 3.12.3 environments: formatting, linting, documentation,
  90 tests, 17 hostile mutations, bytecode compilation, dependency checks, and
  the direct-runtime vulnerability audit were green in all four invocations.
- No Whisper model, production audio, live transcription, or browser session
  was exercised.

## Non-Goals

- Changing accepted audio formats or metadata validation.
- Changing the ffprobe executable, duration limit, or model behavior.
- Promising a total Whisper inference deadline.
