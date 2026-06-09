import importlib
import os
from pathlib import Path
import sys
import types

import pytest


class FakeUpload:
    def __init__(self, name="sample.wav", data=b"audio-bytes"):
        self.name = name
        self.data = data

    def getvalue(self):
        return self.data


class FakeModel:
    def __init__(self):
        self.seen_path = None

    def transcribe(self, path):
        self.seen_path = path
        assert os.path.exists(path)
        return {"text": "  hello world\n"}


class FailingModel:
    def __init__(self):
        self.seen_path = None

    def transcribe(self, path):
        self.seen_path = path
        assert os.path.exists(path)
        raise RuntimeError("ffmpeg failed at /tmp/private-file.wav")


def import_app(monkeypatch):
    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: None,
        write=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: FakeModel())
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    return importlib.import_module("app")


def test_import_does_not_load_model(monkeypatch):
    loaded = []
    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: None,
        write=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: loaded.append(name))
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)

    importlib.import_module("app")

    assert loaded == []


def test_main_rejects_invalid_upload_before_loading_model(monkeypatch):
    errors = []
    loaded = []
    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: FakeUpload(data=b""),
        write=lambda *args, **kwargs: None,
        error=lambda message: errors.append(message),
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(
        load_model=lambda name: loaded.append(name) or FakeModel()
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    app = importlib.import_module("app")

    app.main()

    assert errors == ["Uploaded audio file is empty."]
    assert loaded == []


def test_main_reports_transcription_failure_without_raw_exception(monkeypatch):
    errors = []
    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: FakeUpload(),
        write=lambda *args, **kwargs: None,
        error=lambda message: errors.append(message),
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: FailingModel())
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    app = importlib.import_module("app")

    app.main()

    assert errors == ["Transcription failed. Try a supported audio file."]
    assert "private-file" not in errors[0]


def test_transcribe_uploaded_file_deletes_temp_file(monkeypatch):
    app = import_app(monkeypatch)
    model = FakeModel()

    transcript = app.transcribe_uploaded_file(FakeUpload(), model)

    assert transcript == "hello world"
    assert model.seen_path is not None
    assert not os.path.exists(model.seen_path)


def test_transcribe_uploaded_file_deletes_temp_file_after_failure(monkeypatch):
    app = import_app(monkeypatch)
    model = FailingModel()

    with pytest.raises(app.TranscriptionError, match="Transcription failed"):
        app.transcribe_uploaded_file(FakeUpload(), model)

    assert model.seen_path is not None
    assert not os.path.exists(model.seen_path)


def test_transcribe_uploaded_file_rejects_missing_text_result(monkeypatch):
    app = import_app(monkeypatch)

    class MissingTextModel:
        def transcribe(self, path):
            return {}

    with pytest.raises(app.TranscriptionError, match="Transcription failed"):
        app.transcribe_uploaded_file(FakeUpload(), MissingTextModel())


def test_transcribe_uploaded_file_rejects_non_string_text(monkeypatch):
    app = import_app(monkeypatch)

    class NonStringTextModel:
        def transcribe(self, path):
            return {"text": None}

    with pytest.raises(app.TranscriptionError, match="Transcription failed"):
        app.transcribe_uploaded_file(FakeUpload(), NonStringTextModel())


def test_transcribe_uploaded_file_rejects_blank_text(monkeypatch):
    app = import_app(monkeypatch)

    class BlankTextModel:
        def transcribe(self, path):
            return {"text": "   "}

    with pytest.raises(app.TranscriptionError, match="Transcription failed"):
        app.transcribe_uploaded_file(FakeUpload(), BlankTextModel())


def test_write_uploaded_file_normalizes_supported_suffix(monkeypatch):
    app = import_app(monkeypatch)

    path = app.write_uploaded_file(FakeUpload(name="VOICE.MP3"))
    try:
        assert path.endswith(".mp3")
        assert Path(path).read_bytes() == b"audio-bytes"
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_write_uploaded_file_uses_fallback_for_unsupported_suffix(monkeypatch):
    app = import_app(monkeypatch)

    path = app.write_uploaded_file(FakeUpload(name="../../secret.exe"))
    try:
        assert path.endswith(".audio")
        assert Path(path).read_bytes() == b"audio-bytes"
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_write_uploaded_file_uses_fallback_without_name(monkeypatch):
    app = import_app(monkeypatch)

    path = app.write_uploaded_file(FakeUpload(name=None))
    try:
        assert path.endswith(".audio")
        assert Path(path).read_bytes() == b"audio-bytes"
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_write_uploaded_file_rejects_empty_upload(monkeypatch):
    app = import_app(monkeypatch)

    with pytest.raises(app.UploadValidationError, match="empty"):
        app.write_uploaded_file(FakeUpload(data=b""))


def test_write_uploaded_file_rejects_non_bytes_upload(monkeypatch):
    app = import_app(monkeypatch)

    with pytest.raises(app.UploadValidationError, match="bytes"):
        app.write_uploaded_file(FakeUpload(data="not-bytes"))


def test_write_uploaded_file_normalizes_bytearray_upload(monkeypatch):
    app = import_app(monkeypatch)

    path = app.write_uploaded_file(FakeUpload(data=bytearray(b"audio-bytes")))
    try:
        assert Path(path).read_bytes() == b"audio-bytes"
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_write_uploaded_file_rejects_oversized_upload(monkeypatch):
    app = import_app(monkeypatch)
    monkeypatch.setattr(app, "MAX_UPLOAD_BYTES", 4)

    with pytest.raises(app.UploadValidationError, match="too large"):
        app.write_uploaded_file(FakeUpload(data=b"audio"))
