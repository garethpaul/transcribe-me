# Audio Ingestion Deep Review Design

Status: Completed. Verified with `make check`.

## Goal

Consolidate PRs #2-#7 while ensuring an uploaded file cannot reach Whisper until its bytes, container, first audio stream, duration, channel count, and sample rate have passed bounded offline validation.

## Considered Approaches

1. Keep duration-only probing and add post-capture length checks. This is small, but it still accepts video-only or extreme audio and does not make the parser contract explicit.
2. Probe every stream and aggregate resource estimates. This is comprehensive, but the output and policy surface grow with attacker-controlled stream counts.
3. Probe only the first audio stream plus container metadata, cap the fixed-shape JSON response, and enforce conservative limits before model loading. This is the selected approach because it bounds output independently of stream count and validates the actual decoding boundary with minimal compatibility risk.

## Architecture

The existing byte/signature gate remains the first boundary. After the process-wide admission gate and secure temporary write, one ffprobe invocation selects `a:0` and returns only format name, duration, codec name/type, channels, and sample rate. The parser rejects oversized output, missing or malformed fields, container mismatches, unsupported codecs, non-finite duration, excessive duration, excessive channels, and excessive sample rate before loading Whisper.

Admission uses a bounded semaphore for at most one active request and one queued request. The existing transcription lock still serializes the cached model and bounds the single queued wait. All releases and temporary-file cleanup remain nested so failures cannot leak capacity or files.

## Error Handling

User-facing errors remain sanitized constants. ffprobe stdin stays disconnected, stderr stays discarded, and stdout is checked against a small fixed limit before JSON decoding. No subprocess command, local path, environment value, model exception, or provider diagnostic is rendered to Streamlit.

## Testing

Tests use synthetic bytes and mocked probe results only. Hostile cases cover no-audio containers, container/codec mismatch, excessive channels/sample rate, malformed and oversized probe output, symlink/type rejection at the probe boundary, private temp permissions, bounded request admission, cleanup/release ordering, and unchanged no-model-before-validation behavior. Local ffmpeg fixtures verify WAV, MP3, and M4A metadata when the tools are available; no model is downloaded or called.

## Residual Risk

Whisper inference remains in-process and cannot be safely killed on a hard deadline without moving model ownership to a worker process. Codec decoders and model behavior still require live runtime testing, and the direct-runtime audit does not resolve Whisper's full heavyweight ML dependency graph.
