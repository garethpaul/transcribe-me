## Transcribe Me Vision

Transcribe Me is a Streamlit app that accepts an uploaded audio file and runs a
local Whisper transcription model.

The repository is useful as a minimal speech-to-text demo with clear
dependencies, file upload, temporary-file handling, and transcription display.

The goal is to keep transcription local, understandable, and explicit about
runtime cost, file handling, and model assumptions.

The current focus is:

Priority:

- Preserve the Streamlit upload-to-transcription flow
- Keep Whisper model choice visible
- Treat uploaded audio as sensitive user-provided data
- Normalize uploaded file suffixes before temp-file writes
- Treat uploaded filenames as optional metadata and derive suffixes from audio
  content when metadata is unavailable
- Reject unsupported audio headers and filename/content mismatches before
  parser or model invocation
- Reject unreadable, empty, oversized, and non-byte uploads before writing
  temporary files
- Enforce upload limits at both Streamlit and application boundaries
- Fail clearly when the required system ffmpeg executable is unavailable
- Clean up temporary files when upload writes fail
- Keep temporary-file deletion failures behind user-safe error messages
- Report transcription failures without leaking local exception details
- Validate and trim model transcript text before display
- Display transcripts as plain text
- Serialize inference against the process-wide cached Whisper model
- Bound waits for the shared model lock before creating temporary audio
- Keep completed maintenance plans under `docs/plans`
- Maintain minimal dependencies

Next priorities:

- Add an explicit processing-time or audio-duration bound
- Add a bounded job queue with user-visible waiting and cancellation state
- Add manual live-inference verification with synthetic audio
- Review Streamlit and Whisper upgrades with real model smoke tests

Contribution rules:

- One PR = one focused upload, transcription, dependency, error, or documentation change.
- Do not commit user audio or transcripts.
- Keep network/model download behavior documented.
- Add manual verification notes for supported file types.

## Security And Responsible Use

Canonical security policy and reporting:

- [`SECURITY.md`](SECURITY.md)

Audio can contain private speech and ambient information. The app should keep
processing local by default, avoid retaining temporary files, and make any
external model or service calls explicit.

## What We Will Not Merge (For Now)

- Committed audio samples from real users
- Silent upload of audio or transcripts
- Persistent transcript storage without a privacy model
- Displaying non-string or blank transcription results as successful output
- Upload filename handling that can bypass sanitized validation paths
- Arbitrary upload bytes reaching ffmpeg solely because of filename metadata
- Hidden telemetry

This list is a roadmap guardrail, not a permanent rule.
Strong user demand and strong technical rationale can change it.
