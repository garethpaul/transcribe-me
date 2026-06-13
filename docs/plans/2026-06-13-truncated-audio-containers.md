---
title: "fix: Reject truncated audio container declarations"
type: fix
date: 2026-06-13
---

# Reject Truncated Audio Container Declarations

## Status: Completed

## Context

The upload gate recognizes WAV, M4A, and ID3-prefixed MP3 data from a small
signature. It does not currently verify that each header's declared container
or tag length fits within the uploaded bytes. Truncated declarations can pass
the early gate and reach temporary-file creation even though they cannot hold
the bytes they claim.

## Requirements

- R1. Reject a WAV whose RIFF size extends beyond the upload.
- R2. Reject an M4A whose initial `ftyp` box is shorter than its minimum fields
  or extends beyond the upload.
- R3. Require an ID3 tag to fit within the upload and be followed by a valid
  MP3 frame header.
- R4. Preserve supported WAV, M4A, ID3-prefixed MP3, and raw MP3 uploads.
- R5. Reject malformed data before temporary-file creation or model loading.
- R6. Protect each boundary with focused tests and static mutation contracts.

## Scope Boundaries

This change validates only bounded header declarations used by the existing
signature gate. It does not attempt full media parsing, replace ffmpeg, add
duration limits, or claim that accepted audio is safe or well formed.

## Implementation Units

### U1. Validate Declared Header Bounds

- **Goal:** Keep supported signatures while rejecting declared sizes that do
  not fit in the upload.
- **Files:** `app.py`
- **Approach:** Add small format-specific predicates for RIFF size, the initial
  ISO BMFF `ftyp` box, synchsafe ID3 size, and the existing MP3 frame-header
  fields. Route signature detection through those predicates.
- **Test scenarios:** Valid fixtures retain their suffix; truncated RIFF,
  oversized and undersized `ftyp`, truncated ID3, and ID3 without a following
  MP3 frame are rejected with the existing unsupported-audio message.
- **Verification:** Rejected inputs fail during validation before any write or
  transcription dependency is invoked.

### U2. Add Regression and Mutation Contracts

- **Goal:** Make the length checks durable without coupling tests to ffmpeg.
- **Files:** `tests/test_app.py`, `scripts/check_docs_plans.py`
- **Approach:** Use dependency-free byte fixtures with internally consistent
  declarations. Require the new predicates and focused negative tests in the
  repository checker.
- **Test scenarios:** Mutations removing each declared-length comparison or the
  ID3-following-frame requirement are rejected.
- **Verification:** Focused tests, the static checker, and hostile mutations
  fail for every weakened boundary.

### U3. Record the Validation Boundary

- **Goal:** Explain what the strengthened gate does and does not prove.
- **Files:** `README.md`, `SECURITY.md`, `VISION.md`, `CHANGES.md`,
  `docs/plans/2026-06-13-truncated-audio-containers.md`
- **Approach:** Document declared-size validation as defense in depth while
  retaining ffmpeg as the authoritative parser.
- **Test expectation:** Documentation is enforced by the completed-plan
  checker; no separate runtime behavior is introduced.
- **Verification:** The completed plan records the actual commands and results.

## Risks

- RIFF and ISO BMFF sizes use different byte order and size semantics.
- ID3 uses a four-byte synchsafe integer rather than a normal big-endian size.
- Overly broad parsing would reject valid variants, so checks remain limited to
  declarations already present in the recognized leading headers.

## Assumptions

- The complete uploaded bytes are available before signature validation.
- ffmpeg and Whisper remain responsible for complete format validation and
  decoding after the bounded preflight checks pass.

## Work Completed

- Required the RIFF-declared extent to fit within an uploaded WAV.
- Required the leading M4A `ftyp` box to contain its minimum fields and fit
  within the upload, while preserving size-zero boxes that extend to EOF.
- Parsed synchsafe ID3 lengths, optional ID3v2.4 footers, and the following MP3
  frame header before accepting tagged MP3 data.
- Reused the MP3 frame predicate for raw MP3/MPEG uploads.
- Replaced the truncated WAV fixture with an internally consistent minimal
  header and added valid padded/footer ID3 coverage.
- Added focused pre-tempfile rejection tests, static contracts, and maintenance
  documentation.

## Verification

- Python 3.12.8 with pytest 9.0.3 and Ruff 0.15.16
- `python -m pytest -q tests/test_app.py` (51 passed)
- Six hostile mutations covering RIFF, `ftyp`, ID3 extent, following-frame,
  helper, and regression-test contracts
- `make check`
- `git diff --check`

All behavior tests are dependency-free and use synthetic bytes; no user audio,
model download, ffmpeg process, or live transcription is involved.
