import streamlit as st
import whisper
import tempfile
import os
import shutil
from pathlib import Path


ALLOWED_AUDIO_SUFFIXES = {".m4a", ".mp3", ".mpeg", ".wav"}
ALLOWED_M4A_BRANDS = {b"M4A ", b"M4B ", b"M4P ", b"isom", b"mp42", b"qt  "}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_UPLOAD_MEGABYTES = MAX_UPLOAD_BYTES // (1024 * 1024)
UPLOAD_HELP_TEXT = "Upload an audio file up to %d MB." % MAX_UPLOAD_MEGABYTES
TRANSCRIPTION_FAILURE_MESSAGE = "Transcription failed. Try a supported audio file."
UPLOAD_READ_FAILURE_MESSAGE = "Uploaded audio file could not be read."
UPLOAD_WRITE_FAILURE_MESSAGE = "Uploaded audio file could not be saved."
UNSUPPORTED_AUDIO_MESSAGE = "Uploaded file content is not a supported audio format."
MISMATCHED_AUDIO_MESSAGE = "Uploaded file content does not match its filename extension."
FFMPEG_MISSING_MESSAGE = "ffmpeg is required to transcribe audio."


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


def detected_audio_suffix(data):
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return ".wav"
    if len(data) >= 12 and data[4:8] == b"ftyp" and data[8:12] in ALLOWED_M4A_BRANDS:
        return ".m4a"
    if (
        len(data) >= 10
        and data[:3] == b"ID3"
        and data[3] in {2, 3, 4}
        and all(byte < 0x80 for byte in data[6:10])
    ):
        return ".mp3"
    if len(data) >= 4:
        frame_header = int.from_bytes(data[:4], "big")
        has_sync = frame_header & 0xFFE00000 == 0xFFE00000
        version = (frame_header >> 19) & 0x3
        layer = (frame_header >> 17) & 0x3
        bitrate = (frame_header >> 12) & 0xF
        sample_rate = (frame_header >> 10) & 0x3
        if (
            has_sync
            and version != 0x1
            and layer != 0x0
            and bitrate not in {0x0, 0xF}
            and sample_rate != 0x3
        ):
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


def validated_uploaded_audio(uploaded_file):
    data = uploaded_audio_bytes(uploaded_file)
    suffix = validated_audio_suffix(uploaded_file, data)
    return data, suffix


def write_audio_bytes(data, suffix):
    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            audio_path = tmp_file.name
            tmp_file.write(data)
            return audio_path
    except Exception as error:
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)
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


def transcribe_uploaded_file(uploaded_file, model=None):
    data, suffix = validated_uploaded_audio(uploaded_file)
    if model is None:
        ensure_ffmpeg_available()
    audio_path = write_audio_bytes(data, suffix)
    try:
        try:
            if model is None:
                model = get_model()
            result = model.transcribe(audio_path)
            return normalized_transcript_text(result)
        except TranscriptionError:
            raise
        except Exception as error:
            raise TranscriptionError(TRANSCRIPTION_FAILURE_MESSAGE) from error
    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)


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
