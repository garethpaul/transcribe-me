import importlib
import os
import sys
import types


class FakeUpload:
    name = "sample.wav"

    def getvalue(self):
        return b"audio-bytes"


class FakeModel:
    def __init__(self):
        self.seen_path = None

    def transcribe(self, path):
        self.seen_path = path
        assert os.path.exists(path)
        return {"text": "hello world"}


def import_app(monkeypatch):
    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: None,
        write=lambda *args, **kwargs: None,
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
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: loaded.append(name))
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)

    importlib.import_module("app")

    assert loaded == []


def test_transcribe_uploaded_file_deletes_temp_file(monkeypatch):
    app = import_app(monkeypatch)
    model = FakeModel()

    transcript = app.transcribe_uploaded_file(FakeUpload(), model)

    assert transcript == "hello world"
    assert model.seen_path is not None
    assert not os.path.exists(model.seen_path)
