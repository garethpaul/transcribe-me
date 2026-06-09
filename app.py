import streamlit as st
import whisper
import tempfile
import os
from pathlib import Path


ALLOWED_AUDIO_SUFFIXES = {".m4a", ".mp3", ".mpeg", ".wav"}
FALLBACK_AUDIO_SUFFIX = ".audio"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
TRANSCRIPTION_FAILURE_MESSAGE = "Transcription failed. Try a supported audio file."
UPLOAD_READ_FAILURE_MESSAGE = "Uploaded audio file could not be read."
UPLOAD_WRITE_FAILURE_MESSAGE = "Uploaded audio file could not be saved."


class UploadValidationError(ValueError):
    pass


class TranscriptionError(RuntimeError):
    pass


@st.cache_resource
def get_model():
    return whisper.load_model("base")


def uploaded_audio_suffix(uploaded_file):
    suffix = Path(str(getattr(uploaded_file, "name", "") or "")).suffix.lower()
    if suffix in ALLOWED_AUDIO_SUFFIXES:
        return suffix
    return FALLBACK_AUDIO_SUFFIX


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


def write_uploaded_file(uploaded_file):
    suffix = uploaded_audio_suffix(uploaded_file)
    data = uploaded_audio_bytes(uploaded_file)
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
    audio_path = write_uploaded_file(uploaded_file)
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
