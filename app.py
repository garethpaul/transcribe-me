import streamlit as st
import whisper
import tempfile
import os


@st.cache_resource
def get_model():
    return whisper.load_model("base")


def write_uploaded_file(uploaded_file):
    suffix = "." + uploaded_file.name.split(".")[-1]
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
        "Upload audio file", type=["mp3", "wav", "mpeg", "m4a"]
    )

    if uploaded_file is not None:
        st.write("Transcribing... This may take a while for large files.")
        transcript = transcribe_uploaded_file(uploaded_file, get_model())
        st.write("Transcription:")
        st.write(transcript)


if __name__ == "__main__":
    main()
