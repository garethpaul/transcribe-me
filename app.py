import streamlit as st
import whisper
import tempfile
import os
from pathlib import Path


ALLOWED_AUDIO_SUFFIXES = {".m4a", ".mp3", ".mpeg", ".wav"}
FALLBACK_AUDIO_SUFFIX = ".audio"


@st.cache_resource
def get_model():
    return whisper.load_model("base")


def uploaded_audio_suffix(uploaded_file):
    suffix = Path(str(getattr(uploaded_file, "name", "") or "")).suffix.lower()
    if suffix in ALLOWED_AUDIO_SUFFIXES:
        return suffix
    return FALLBACK_AUDIO_SUFFIX


def write_uploaded_file(uploaded_file):
    suffix = uploaded_audio_suffix(uploaded_file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name


def transcribe_uploaded_file(uploaded_file, model):
    audio_path = write_uploaded_file(uploaded_file)
    try:
        result = model.transcribe(audio_path)
        return result["text"]
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
        transcript = transcribe_uploaded_file(uploaded_file, get_model())
        st.write("Transcription:")
        st.write(transcript)


if __name__ == "__main__":
    main()
