import json
import math
import streamlit as st
import whisper
import tempfile
import os
import shutil
import subprocess
import threading
from pathlib import Path


ALLOWED_AUDIO_SUFFIXES = {".m4a", ".mp3", ".mpeg", ".wav"}
ALLOWED_M4A_BRANDS = {b"M4A ", b"M4B ", b"M4P ", b"isom", b"mp42", b"qt  "}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_UPLOAD_MEGABYTES = MAX_UPLOAD_BYTES // (1024 * 1024)
UPLOAD_HELP_TEXT = "Upload an audio file up to %d MB." % MAX_UPLOAD_MEGABYTES
TRANSCRIPTION_FAILURE_MESSAGE = "Transcription failed. Try a supported audio file."
TRANSCRIPTION_BUSY_MESSAGE = "Transcription service is busy. Try again shortly."
TRANSCRIPTION_LOCK_TIMEOUT_SECONDS = 30
FFPROBE_TIMEOUT_SECONDS = 10
MAX_AUDIO_DURATION_SECONDS = 15 * 60
UPLOAD_READ_FAILURE_MESSAGE = "Uploaded audio file could not be read."
UPLOAD_WRITE_FAILURE_MESSAGE = "Uploaded audio file could not be saved."
UNSUPPORTED_AUDIO_MESSAGE = "Uploaded file content is not a supported audio format."
MISMATCHED_AUDIO_MESSAGE = "Uploaded file content does not match its filename extension."
FFMPEG_MISSING_MESSAGE = "ffmpeg is required to transcribe audio."
FFPROBE_MISSING_MESSAGE = "ffprobe is required to validate audio."
AUDIO_TOO_LONG_MESSAGE = "Uploaded audio is longer than 15 minutes."
TRANSCRIPTION_LOCK = threading.Lock()


class UploadValidationError(ValueError):
    pass


class TranscriptionError(RuntimeError):
    pass


@st.cache_resource
def get_model():
    return whisper.load_model("base")


def uploaded_audio_suffix(uploaded_file):
    try:
        suffix = Path(str(getattr(uploaded_file, "name", "") or "")).suffix.lower()
    except Exception:
        return None
    if suffix in ALLOWED_AUDIO_SUFFIXES:
        return suffix
    return None


def uploaded_audio_bytes(uploaded_file):
    getvalue = getattr(uploaded_file, "getvalue", None)
    if not callable(getvalue):
        raise UploadValidationError(UPLOAD_READ_FAILURE_MESSAGE)
    try:
        data = getvalue()
    except Exception as error:
        raise UploadValidationError(UPLOAD_READ_FAILURE_MESSAGE) from error
    if not isinstance(data, (bytes, bytearray)):
        raise UploadValidationError("Uploaded audio file must be bytes.")
    data = bytes(data)
    if not data:
        raise UploadValidationError("Uploaded audio file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadValidationError("Uploaded audio file is too large.")
    return data


def has_complete_riff_header(data):
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return False
    riff_size = int.from_bytes(data[4:8], "little")
    return riff_size >= 4 and riff_size + 8 <= len(data)


def has_complete_ftyp_box(data):
    if len(data) < 16 or data[4:8] != b"ftyp" or data[8:12] not in ALLOWED_M4A_BRANDS:
        return False
    box_size = int.from_bytes(data[:4], "big")
    return box_size == 0 or 16 <= box_size <= len(data)


def has_mp3_frame_header(data, offset=0):
    if len(data) < offset + 4:
        return False
    frame_header = int.from_bytes(data[offset : offset + 4], "big")
    has_sync = frame_header & 0xFFE00000 == 0xFFE00000
    version = (frame_header >> 19) & 0x3
    layer = (frame_header >> 17) & 0x3
    bitrate = (frame_header >> 12) & 0xF
    sample_rate = (frame_header >> 10) & 0x3
    return (
        has_sync
        and version != 0x1
        and layer != 0x0
        and bitrate not in {0x0, 0xF}
        and sample_rate != 0x3
    )


def id3_audio_offset(data):
    if (
        len(data) < 10
        or data[:3] != b"ID3"
        or data[3] not in {2, 3, 4}
        or any(byte >= 0x80 for byte in data[6:10])
    ):
        return None
    tag_size = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
    footer_size = 10 if data[3] == 4 and data[5] & 0x10 else 0
    audio_offset = 10 + tag_size + footer_size
    if audio_offset > len(data):
        return None
    return audio_offset


def detected_audio_suffix(data):
    if has_complete_riff_header(data):
        return ".wav"
    if has_complete_ftyp_box(data):
        return ".m4a"
    audio_offset = id3_audio_offset(data)
    if audio_offset is not None and has_mp3_frame_header(data, audio_offset):
        return ".mp3"
    if has_mp3_frame_header(data):
        return ".mp3"
    raise UploadValidationError(UNSUPPORTED_AUDIO_MESSAGE)


def validated_audio_suffix(uploaded_file, data):
    declared_suffix = uploaded_audio_suffix(uploaded_file)
    detected_suffix = detected_audio_suffix(data)
    if declared_suffix in {".mp3", ".mpeg"} and detected_suffix == ".mp3":
        return declared_suffix
    if declared_suffix is not None and declared_suffix != detected_suffix:
        raise UploadValidationError(MISMATCHED_AUDIO_MESSAGE)
    return detected_suffix


def ensure_ffmpeg_available():
    if shutil.which("ffmpeg") is None:
        raise TranscriptionError(FFMPEG_MISSING_MESSAGE)


def ensure_ffprobe_available():
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path is None:
        raise TranscriptionError(FFPROBE_MISSING_MESSAGE)
    return ffprobe_path


def probe_audio_duration(audio_path, ffprobe_path):
    try:
        completed = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                audio_path,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=FFPROBE_TIMEOUT_SECONDS,
        )
        duration = float(json.loads(completed.stdout)["format"]["duration"])
    except (
        json.JSONDecodeError,
        KeyError,
        OSError,
        subprocess.SubprocessError,
        TypeError,
        ValueError,
    ) as error:
        raise TranscriptionError(TRANSCRIPTION_FAILURE_MESSAGE) from error

    if not math.isfinite(duration) or duration <= 0:
        raise TranscriptionError(TRANSCRIPTION_FAILURE_MESSAGE)
    if duration > MAX_AUDIO_DURATION_SECONDS:
        raise TranscriptionError(AUDIO_TOO_LONG_MESSAGE)
    return duration


def validated_uploaded_audio(uploaded_file):
    data = uploaded_audio_bytes(uploaded_file)
    suffix = validated_audio_suffix(uploaded_file, data)
    return data, suffix


def remove_audio_file(audio_path, cleanup_error):
    try:
        os.unlink(audio_path)
    except FileNotFoundError:
        return
    except OSError as error:
        raise cleanup_error from error


def write_audio_bytes(data, suffix):
    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            audio_path = tmp_file.name
            tmp_file.write(data)
            return audio_path
    except Exception as error:
        if audio_path:
            remove_audio_file(
                audio_path,
                UploadValidationError(UPLOAD_WRITE_FAILURE_MESSAGE),
            )
        raise UploadValidationError(UPLOAD_WRITE_FAILURE_MESSAGE) from error


def write_uploaded_file(uploaded_file):
    data, suffix = validated_uploaded_audio(uploaded_file)
    return write_audio_bytes(data, suffix)


def normalized_transcript_text(result):
    if not isinstance(result, dict):
        raise TranscriptionError(TRANSCRIPTION_FAILURE_MESSAGE)

    text = result.get("text")
    if not isinstance(text, str):
        raise TranscriptionError(TRANSCRIPTION_FAILURE_MESSAGE)

    text = text.strip()
    if not text:
        raise TranscriptionError(TRANSCRIPTION_FAILURE_MESSAGE)
    return text


def transcribe_with_lock(model, data, suffix, ffprobe_path):
    acquired = TRANSCRIPTION_LOCK.acquire(timeout=TRANSCRIPTION_LOCK_TIMEOUT_SECONDS)
    if not acquired:
        raise TranscriptionError(TRANSCRIPTION_BUSY_MESSAGE)
    audio_path = None
    try:
        audio_path = write_audio_bytes(data, suffix)
        probe_audio_duration(audio_path, ffprobe_path)
        if model is None:
            model = get_model()
        return model.transcribe(audio_path)
    finally:
        try:
            if audio_path is not None:
                remove_audio_file(
                    audio_path,
                    TranscriptionError(TRANSCRIPTION_FAILURE_MESSAGE),
                )
        finally:
            TRANSCRIPTION_LOCK.release()


def transcribe_uploaded_file(uploaded_file, model=None):
    data, suffix = validated_uploaded_audio(uploaded_file)
    if model is None:
        ensure_ffmpeg_available()
    ffprobe_path = ensure_ffprobe_available()
    try:
        result = transcribe_with_lock(model, data, suffix, ffprobe_path)
        return normalized_transcript_text(result)
    except (UploadValidationError, TranscriptionError):
        raise
    except Exception as error:
        raise TranscriptionError(TRANSCRIPTION_FAILURE_MESSAGE) from error


def main():
    st.title("Audio Transcription using Whisper")
    uploaded_file = st.file_uploader(
        "Upload audio file",
        type=sorted(suffix[1:] for suffix in ALLOWED_AUDIO_SUFFIXES),
        help=UPLOAD_HELP_TEXT,
    )

    if uploaded_file is not None:
        st.write("Transcribing... This may take a while for large files.")
        try:
            transcript = transcribe_uploaded_file(uploaded_file)
        except UploadValidationError as error:
            st.error(str(error))
            return
        except TranscriptionError as error:
            st.error(str(error))
            return
        st.write("Transcription:")
        st.text(transcript)


if __name__ == "__main__":
    main()
