import streamlit as st
import whisper
import tempfile

# Initialize Whisper model
model = whisper.load_model("base")

# Title of the application
st.title("Audio Transcription using Whisper")

# File uploader allows user to add audio file
uploaded_file = st.file_uploader(
    "Upload audio file", type=["mp3", "wav", "mpeg", "m4a"]
)

if uploaded_file is not None:
    # Display an information message
    st.write("Transcribing... This may take a while for large files.")

    # Save the file temporarily
    with tempfile.NamedTemporaryFile(
        delete=False, suffix="." + uploaded_file.name.split(".")[-1]
    ) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        audio_path = tmp_file.name

    # Process the audio file with Whisper
    result = model.transcribe(audio_path)

    # Display the transcription
    st.write("Transcription:")
    st.write(result["text"])
