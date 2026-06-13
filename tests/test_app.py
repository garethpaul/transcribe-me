from concurrent.futures import ThreadPoolExecutor
import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import types

import pytest


MPEG_BYTES = b"\xff\xfb\x90\x64audio"
WAV_BYTES = (
    b"RIFF"
    + (36).to_bytes(4, "little")
    + b"WAVEfmt "
    + (16).to_bytes(4, "little")
    + b"\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00"
    + b"data\x00\x00\x00\x00"
)
MP3_BYTES = b"ID3\x04\x00\x00\x00\x00\x00\x00" + MPEG_BYTES
PADDED_MP3_BYTES = b"ID3\x04\x00\x00\x00\x00\x00\x03pad" + MPEG_BYTES
FOOTER_MP3_BYTES = (
    b"ID3\x04\x00\x10\x00\x00\x00\x00" + b"3DI\x04\x00\x10\x00\x00\x00\x00" + MPEG_BYTES
)
M4A_BYTES = b"\x00\x00\x00\x18ftypM4A \x00\x00\x00\x00M4A isom"


class FakeUpload:
    def __init__(self, name="sample.wav", data=WAV_BYTES):
        self.name = name
        self.data = data

    def getvalue(self):
        return self.data


class MissingReaderUpload:
    name = "sample.wav"


class FailingReaderUpload(FakeUpload):
    def getvalue(self):
        raise RuntimeError("failed reading /tmp/private-upload.wav")


class FailingNameUpload:
    data = WAV_BYTES

    @property
    def name(self):
        raise RuntimeError("failed reading /tmp/private-name.wav")

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


def import_app(monkeypatch, stub_probe=True):
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
    app = importlib.import_module("app")
    if stub_probe:
        monkeypatch.setattr(app, "ensure_ffprobe_available", lambda: "/usr/bin/ffprobe")
        monkeypatch.setattr(app, "probe_audio_duration", lambda *args: 1.0)
    return app


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
    fake_whisper = types.SimpleNamespace(load_model=lambda name: loaded.append(name) or FakeModel())
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    app = importlib.import_module("app")

    app.main()

    assert errors == ["Uploaded audio file is empty."]
    assert loaded == []


def test_main_file_uploader_documents_upload_limit(monkeypatch):
    captured = {}
    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: captured.update(kwargs),
        write=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: FakeModel())
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    app = importlib.import_module("app")

    app.main()

    assert "25 MB" in captured["help"]


def test_main_rejects_unreadable_upload_before_loading_model(monkeypatch):
    errors = []
    loaded = []
    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: FailingReaderUpload(),
        write=lambda *args, **kwargs: None,
        error=lambda message: errors.append(message),
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: loaded.append(name) or FakeModel())
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    app = importlib.import_module("app")

    app.main()

    assert errors == ["Uploaded audio file could not be read."]
    assert loaded == []
    assert "private-upload" not in errors[0]


def test_main_rejects_unsupported_audio_before_loading_model(monkeypatch):
    errors = []
    loaded = []
    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: FakeUpload(data=b"not-audio"),
        write=lambda *args, **kwargs: None,
        error=lambda message: errors.append(message),
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: loaded.append(name) or FakeModel())
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    app = importlib.import_module("app")

    app.main()

    assert errors == ["Uploaded file content is not a supported audio format."]
    assert loaded == []


def test_main_reports_missing_ffmpeg_before_loading_model(monkeypatch):
    errors = []
    loaded = []
    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: FakeUpload(),
        write=lambda *args, **kwargs: None,
        error=lambda message: errors.append(message),
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: loaded.append(name) or FakeModel())
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    app = importlib.import_module("app")
    monkeypatch.setattr(app.shutil, "which", lambda command: None)

    app.main()

    assert errors == ["ffmpeg is required to transcribe audio."]
    assert loaded == []


def test_main_reports_upload_write_failure_without_raw_exception(monkeypatch):
    errors = []
    loaded = []
    created_paths = []
    original_named_temporary_file = tempfile.NamedTemporaryFile

    class FailingTempFile:
        def __init__(self, *args, **kwargs):
            self.file = original_named_temporary_file(
                delete=False,
                suffix=kwargs.get("suffix", ""),
            )
            self.name = self.file.name
            created_paths.append(self.name)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.file.close()

        def write(self, data):
            raise OSError("disk full at /tmp/private-upload.wav")

    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: FakeUpload(),
        write=lambda *args, **kwargs: None,
        error=lambda message: errors.append(message),
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: loaded.append(name) or FakeModel())
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    app = importlib.import_module("app")
    monkeypatch.setattr(app.shutil, "which", lambda command: "/usr/bin/ffmpeg")
    monkeypatch.setattr(app.tempfile, "NamedTemporaryFile", FailingTempFile)

    app.main()

    assert errors == ["Uploaded audio file could not be saved."]
    assert loaded == []
    assert created_paths
    assert not os.path.exists(created_paths[0])
    assert "private-upload" not in errors[0]


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
    monkeypatch.setattr(app.shutil, "which", lambda command: "/usr/bin/ffmpeg")
    monkeypatch.setattr(app, "probe_audio_duration", lambda *args: 1.0)

    app.main()

    assert errors == ["Transcription failed. Try a supported audio file."]


def test_main_reports_busy_transcription_message(monkeypatch):
    errors = []
    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: FakeUpload(),
        write=lambda *args, **kwargs: None,
        error=lambda message: errors.append(message),
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: FakeModel())
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    app = importlib.import_module("app")

    def report_busy(uploaded_file, model=None):
        raise app.TranscriptionError(app.TRANSCRIPTION_BUSY_MESSAGE)

    monkeypatch.setattr(app, "transcribe_uploaded_file", report_busy)

    app.main()

    assert errors == ["Transcription service is busy. Try again shortly."]
    assert "private-file" not in errors[0]


def test_main_renders_transcript_as_plain_text(monkeypatch):
    writes = []
    texts = []
    errors = []

    class MarkdownLikeModel:
        def transcribe(self, path):
            return {"text": "  **secret** <b>raw</b>  "}

    fake_streamlit = types.SimpleNamespace(
        title=lambda *args, **kwargs: None,
        file_uploader=lambda *args, **kwargs: FakeUpload(),
        write=lambda message: writes.append(message),
        text=lambda message: texts.append(message),
        error=lambda message: errors.append(message),
        cache_resource=lambda fn: fn,
    )
    fake_whisper = types.SimpleNamespace(load_model=lambda name: MarkdownLikeModel())
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)
    sys.modules.pop("app", None)
    app = importlib.import_module("app")
    monkeypatch.setattr(app.shutil, "which", lambda command: "/usr/bin/ffmpeg")
    monkeypatch.setattr(app, "probe_audio_duration", lambda *args: 1.0)

    app.main()

    assert errors == []
    assert writes == [
        "Transcribing... This may take a while for large files.",
        "Transcription:",
    ]
    assert texts == ["**secret** <b>raw</b>"]


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


def test_transcribe_uploaded_file_sanitizes_temp_cleanup_errors(monkeypatch):
    app = import_app(monkeypatch)
    model = FakeModel()
    original_unlink = app.os.unlink

    def fail_unlink(path):
        raise OSError("permission denied for /tmp/private-upload.wav")

    monkeypatch.setattr(app.os, "unlink", fail_unlink)

    try:
        with pytest.raises(app.TranscriptionError, match="Transcription failed") as exc_info:
            app.transcribe_uploaded_file(FakeUpload(), model)

        assert isinstance(exc_info.value.__cause__, OSError)
        assert "private-upload" not in str(exc_info.value)
    finally:
        if model.seen_path and os.path.exists(model.seen_path):
            original_unlink(model.seen_path)


def test_transcribe_uploaded_file_serializes_shared_model_calls(monkeypatch):
    app = import_app(monkeypatch)

    class ConcurrentModel:
        def __init__(self):
            self.calls = 0
            self.first_entered = threading.Event()
            self.release_first = threading.Event()
            self.second_entered = threading.Event()

        def transcribe(self, path):
            self.calls += 1
            if self.calls == 1:
                self.first_entered.set()
                assert self.release_first.wait(timeout=1)
            else:
                self.second_entered.set()
            return {"text": "hello"}

    model = ConcurrentModel()
    second_started = threading.Event()

    def transcribe_second_upload():
        second_started.set()
        return app.transcribe_uploaded_file(FakeUpload(), model)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(app.transcribe_uploaded_file, FakeUpload(), model)
        assert model.first_entered.wait(timeout=1)
        second = executor.submit(transcribe_second_upload)
        try:
            assert second_started.wait(timeout=1)
            assert not model.second_entered.wait(timeout=0.2)
        finally:
            model.release_first.set()

        assert first.result(timeout=1) == "hello"
        assert second.result(timeout=1) == "hello"
        assert model.second_entered.is_set()


def test_transcribe_uploaded_file_bounds_lock_wait_before_tempfile_creation(monkeypatch):
    app = import_app(monkeypatch)
    model = FakeModel()

    class ContendedLock:
        def __init__(self):
            self.timeout = None
            self.release_calls = 0

        def acquire(self, timeout):
            self.timeout = timeout
            return False

        def release(self):
            self.release_calls += 1

    lock = ContendedLock()

    def reject_temp_write(data, suffix):
        raise AssertionError("busy requests must not create temporary audio")

    monkeypatch.setattr(app, "TRANSCRIPTION_LOCK", lock)
    monkeypatch.setattr(app, "write_audio_bytes", reject_temp_write)

    with pytest.raises(app.TranscriptionError, match="service is busy"):
        app.transcribe_uploaded_file(FakeUpload(), model)

    assert lock.timeout == app.TRANSCRIPTION_LOCK_TIMEOUT_SECONDS
    assert lock.release_calls == 0
    assert model.seen_path is None


def test_transcribe_uploaded_file_releases_lock_after_write_failure(monkeypatch):
    app = import_app(monkeypatch)

    class AcquiredLock:
        def __init__(self):
            self.release_calls = 0

        def acquire(self, timeout):
            return True

        def release(self):
            self.release_calls += 1

    def fail_write(data, suffix):
        raise app.UploadValidationError(app.UPLOAD_WRITE_FAILURE_MESSAGE)

    lock = AcquiredLock()
    monkeypatch.setattr(app, "TRANSCRIPTION_LOCK", lock)
    monkeypatch.setattr(app, "write_audio_bytes", fail_write)

    with pytest.raises(app.UploadValidationError, match="could not be saved"):
        app.transcribe_uploaded_file(FakeUpload(), FakeModel())

    assert lock.release_calls == 1


@pytest.mark.parametrize("model", [FakeModel(), FailingModel()])
def test_transcribe_uploaded_file_releases_acquired_lock(monkeypatch, model):
    app = import_app(monkeypatch)

    class AcquiredLock:
        def __init__(self):
            self.release_calls = 0

        def acquire(self, timeout):
            return True

        def release(self):
            self.release_calls += 1

    lock = AcquiredLock()
    monkeypatch.setattr(app, "TRANSCRIPTION_LOCK", lock)

    if isinstance(model, FailingModel):
        with pytest.raises(app.TranscriptionError, match="Transcription failed"):
            app.transcribe_uploaded_file(FakeUpload(), model)
    else:
        assert app.transcribe_uploaded_file(FakeUpload(), model) == "hello world"

    assert lock.release_calls == 1


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

    path = app.write_uploaded_file(FakeUpload(name="VOICE.MP3", data=MP3_BYTES))
    try:
        assert path.endswith(".mp3")
        assert Path(path).read_bytes() == MP3_BYTES
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_write_uploaded_file_infers_suffix_for_unsupported_name(monkeypatch):
    app = import_app(monkeypatch)

    path = app.write_uploaded_file(FakeUpload(name="../../secret.exe"))
    try:
        assert path.endswith(".wav")
        assert Path(path).read_bytes() == WAV_BYTES
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_write_uploaded_file_infers_suffix_without_name(monkeypatch):
    app = import_app(monkeypatch)

    path = app.write_uploaded_file(FakeUpload(name=None))
    try:
        assert path.endswith(".wav")
        assert Path(path).read_bytes() == WAV_BYTES
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_write_uploaded_file_infers_suffix_when_name_fails(monkeypatch):
    app = import_app(monkeypatch)

    path = app.write_uploaded_file(FailingNameUpload())
    try:
        assert path.endswith(".wav")
        assert Path(path).read_bytes() == WAV_BYTES
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


def test_write_uploaded_file_rejects_upload_without_getvalue(monkeypatch):
    app = import_app(monkeypatch)

    with pytest.raises(app.UploadValidationError, match="could not be read"):
        app.write_uploaded_file(MissingReaderUpload())


def test_write_uploaded_file_rejects_upload_read_errors(monkeypatch):
    app = import_app(monkeypatch)

    with pytest.raises(app.UploadValidationError, match="could not be read"):
        app.write_uploaded_file(FailingReaderUpload())


def test_write_uploaded_file_cleans_up_after_write_error(monkeypatch):
    app = import_app(monkeypatch)
    created_paths = []
    original_named_temporary_file = app.tempfile.NamedTemporaryFile

    class FailingTempFile:
        def __init__(self, *args, **kwargs):
            self.file = original_named_temporary_file(
                delete=False,
                suffix=kwargs.get("suffix", ""),
            )
            self.name = self.file.name
            created_paths.append(self.name)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.file.close()

        def write(self, data):
            raise OSError("disk full at /tmp/private-upload.wav")

    monkeypatch.setattr(app.tempfile, "NamedTemporaryFile", FailingTempFile)

    with pytest.raises(app.UploadValidationError, match="could not be saved"):
        app.write_uploaded_file(FakeUpload())

    assert created_paths
    assert not os.path.exists(created_paths[0])


def test_write_uploaded_file_sanitizes_cleanup_errors_after_write_failure(monkeypatch):
    app = import_app(monkeypatch)
    created_paths = []
    original_named_temporary_file = app.tempfile.NamedTemporaryFile
    original_unlink = app.os.unlink

    class FailingTempFile:
        def __init__(self, *args, **kwargs):
            self.file = original_named_temporary_file(
                delete=False,
                suffix=kwargs.get("suffix", ""),
            )
            self.name = self.file.name
            created_paths.append(self.name)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.file.close()

        def write(self, data):
            raise OSError("disk full at /tmp/private-upload.wav")

    def fail_unlink(path):
        raise OSError("permission denied for /tmp/private-upload.wav")

    monkeypatch.setattr(app.tempfile, "NamedTemporaryFile", FailingTempFile)
    monkeypatch.setattr(app.os, "unlink", fail_unlink)

    try:
        with pytest.raises(app.UploadValidationError, match="could not be saved") as exc_info:
            app.write_uploaded_file(FakeUpload())

        assert isinstance(exc_info.value.__cause__, OSError)
        assert "private-upload" not in str(exc_info.value)
        assert created_paths
    finally:
        for path in created_paths:
            if os.path.exists(path):
                original_unlink(path)


def test_write_uploaded_file_normalizes_bytearray_upload(monkeypatch):
    app = import_app(monkeypatch)

    path = app.write_uploaded_file(FakeUpload(data=bytearray(WAV_BYTES)))
    try:
        assert Path(path).read_bytes() == WAV_BYTES
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_write_uploaded_file_rejects_oversized_upload(monkeypatch):
    app = import_app(monkeypatch)
    monkeypatch.setattr(app, "MAX_UPLOAD_BYTES", 4)

    with pytest.raises(app.UploadValidationError, match="too large"):
        app.write_uploaded_file(FakeUpload(data=b"audio"))


@pytest.mark.parametrize(
    ("name", "data", "expected_suffix"),
    [
        ("sample.wav", WAV_BYTES, ".wav"),
        ("sample.mp3", MP3_BYTES, ".mp3"),
        ("padded.mp3", PADDED_MP3_BYTES, ".mp3"),
        ("footer.mp3", FOOTER_MP3_BYTES, ".mp3"),
        ("sample.mpeg", MPEG_BYTES, ".mpeg"),
        ("sample.m4a", M4A_BYTES, ".m4a"),
    ],
)
def test_write_uploaded_file_accepts_supported_audio_signatures(
    monkeypatch, name, data, expected_suffix
):
    app = import_app(monkeypatch)

    path = app.write_uploaded_file(FakeUpload(name=name, data=data))
    try:
        assert path.endswith(expected_suffix)
        assert Path(path).read_bytes() == data
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_write_uploaded_file_rejects_unsupported_content_before_tempfile(monkeypatch):
    app = import_app(monkeypatch)

    with pytest.raises(app.UploadValidationError, match="not a supported audio format"):
        app.write_uploaded_file(FakeUpload(name="payload.wav", data=b"not-audio"))


@pytest.mark.parametrize(
    "data",
    [
        b"\\x00\\x00\\x00\\x18ftypBAD!payload",
        b"ID3\\x01\\x00\\x00\\x00\\x00\\x00\\x00payload",
        b"\\xff\\xe0\\x00\\x00payload",
    ],
)
def test_write_uploaded_file_rejects_lookalike_audio_headers(monkeypatch, data):
    app = import_app(monkeypatch)

    with pytest.raises(app.UploadValidationError, match="not a supported audio format"):
        app.write_uploaded_file(FakeUpload(name=None, data=data))


@pytest.mark.parametrize(
    "data",
    [
        WAV_BYTES[:-1],
        (12).to_bytes(4, "big") + M4A_BYTES[4:],
        (len(M4A_BYTES) + 1).to_bytes(4, "big") + M4A_BYTES[4:],
        b"ID3\x04\x00\x00\x00\x00\x00\x7f" + MPEG_BYTES,
        b"ID3\x04\x00\x00\x00\x00\x00\x00audio",
    ],
)
def test_write_uploaded_file_rejects_truncated_audio_declarations_before_tempfile(
    monkeypatch, data
):
    app = import_app(monkeypatch)
    writes = []
    monkeypatch.setattr(
        app,
        "write_audio_bytes",
        lambda *args: writes.append(args),
    )

    with pytest.raises(app.UploadValidationError, match="not a supported audio format"):
        app.write_uploaded_file(FakeUpload(name=None, data=data))

    assert writes == []


def test_write_uploaded_file_rejects_extension_mismatch(monkeypatch):
    app = import_app(monkeypatch)

    with pytest.raises(app.UploadValidationError, match="does not match"):
        app.write_uploaded_file(FakeUpload(name="payload.mp3", data=WAV_BYTES))


def test_transcribe_uploaded_file_checks_ffmpeg_before_loading_model(monkeypatch):
    app = import_app(monkeypatch)
    loaded = []
    tempfiles = []
    monkeypatch.setattr(app.shutil, "which", lambda command: None)
    monkeypatch.setattr(app, "get_model", lambda: loaded.append("model"))
    monkeypatch.setattr(
        app.tempfile,
        "NamedTemporaryFile",
        lambda *args, **kwargs: tempfiles.append(kwargs) or None,
    )

    with pytest.raises(app.TranscriptionError, match="ffmpeg is required"):
        app.transcribe_uploaded_file(FakeUpload())

    assert loaded == []
    assert tempfiles == []


def test_transcribe_uploaded_file_checks_ffprobe_before_tempfile(monkeypatch):
    app = import_app(monkeypatch, stub_probe=False)
    tempfiles = []
    monkeypatch.setattr(app.shutil, "which", lambda command: None)
    monkeypatch.setattr(
        app.tempfile,
        "NamedTemporaryFile",
        lambda *args, **kwargs: tempfiles.append(kwargs) or None,
    )

    with pytest.raises(app.TranscriptionError, match="ffprobe is required"):
        app.transcribe_uploaded_file(FakeUpload(), FakeModel())

    assert tempfiles == []


def test_probe_audio_duration_uses_bounded_json_probe(monkeypatch):
    app = import_app(monkeypatch, stub_probe=False)
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, '{"format":{"duration":"12.5"}}', "")

    monkeypatch.setattr(app.subprocess, "run", run)

    assert app.probe_audio_duration("/tmp/audio.wav", "/tools/ffprobe") == 12.5
    assert calls == [
        (
            [
                "/tools/ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                "/tmp/audio.wav",
            ],
            {
                "check": True,
                "capture_output": True,
                "stdin": subprocess.DEVNULL,
                "text": True,
                "timeout": 10,
            },
        )
    ]
    assert app.FFPROBE_TIMEOUT_SECONDS == 10


@pytest.mark.parametrize(
    "stdout",
    [
        "not-json",
        "{}",
        '{"format":{}}',
        '{"format":{"duration":"nan"}}',
        '{"format":{"duration":"inf"}}',
        '{"format":{"duration":"0"}}',
        '{"format":{"duration":"-1"}}',
    ],
)
def test_probe_audio_duration_rejects_invalid_results(monkeypatch, stdout):
    app = import_app(monkeypatch, stub_probe=False)
    monkeypatch.setattr(
        app.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout, ""),
    )

    with pytest.raises(app.TranscriptionError, match="Transcription failed"):
        app.probe_audio_duration("/tmp/private.wav", "/tools/ffprobe")


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, ["ffprobe"], stderr="private path"),
        subprocess.TimeoutExpired(["ffprobe"], 10),
        OSError("private path"),
    ],
)
def test_probe_audio_duration_sanitizes_probe_failures(monkeypatch, error):
    app = import_app(monkeypatch, stub_probe=False)

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(app.subprocess, "run", fail)

    with pytest.raises(app.TranscriptionError, match="^Transcription failed") as raised:
        app.probe_audio_duration("/tmp/private.wav", "/tools/ffprobe")

    assert "private" not in str(raised.value)


def test_probe_audio_duration_rejects_excessive_duration(monkeypatch):
    app = import_app(monkeypatch, stub_probe=False)
    assert app.MAX_AUDIO_DURATION_SECONDS == 15 * 60
    duration = app.MAX_AUDIO_DURATION_SECONDS + 0.001
    monkeypatch.setattr(
        app.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0],
            0,
            '{"format":{"duration":"%s"}}' % duration,
            "",
        ),
    )

    with pytest.raises(app.TranscriptionError, match="longer than 15 minutes"):
        app.probe_audio_duration("/tmp/private.wav", "/tools/ffprobe")


def test_transcribe_uploaded_file_rejects_long_audio_before_model_load(monkeypatch):
    app = import_app(monkeypatch)
    loaded = []
    removed = []
    monkeypatch.setattr(
        app,
        "probe_audio_duration",
        lambda *args: (_ for _ in ()).throw(app.TranscriptionError(app.AUDIO_TOO_LONG_MESSAGE)),
    )
    monkeypatch.setattr(app, "ensure_ffmpeg_available", lambda: None)
    monkeypatch.setattr(app, "get_model", lambda: loaded.append("model"))
    original_remove = app.remove_audio_file

    def record_remove(path, error):
        removed.append(path)
        original_remove(path, error)

    monkeypatch.setattr(app, "remove_audio_file", record_remove)

    with pytest.raises(app.TranscriptionError, match="longer than 15 minutes"):
        app.transcribe_uploaded_file(FakeUpload())

    assert loaded == []
    assert len(removed) == 1
    assert not os.path.exists(removed[0])


def test_transcribe_uploaded_file_rejects_content_before_loading_model(monkeypatch):
    app = import_app(monkeypatch)
    loaded = []
    monkeypatch.setattr(app, "get_model", lambda: loaded.append("model"))

    with pytest.raises(app.UploadValidationError, match="not a supported audio"):
        app.transcribe_uploaded_file(FakeUpload(data=b"not-audio"))

    assert loaded == []
