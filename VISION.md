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
- Reject unreadable, empty, oversized, and non-byte uploads before writing
  temporary files
- Clean up temporary files when upload writes fail
- Report transcription failures without leaking local exception details
- Validate and trim model transcript text before display
- Display transcripts as plain text
- Keep completed maintenance plans under `docs/plans`
- Maintain minimal dependencies

Next priorities:

- Add README setup notes for Python, ffmpeg, and model download behavior
- Add duration guidance for supported audio files
- Add manual verification notes for common audio formats

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
- Hidden telemetry

This list is a roadmap guardrail, not a permanent rule.
Strong user demand and strong technical rationale can change it.
