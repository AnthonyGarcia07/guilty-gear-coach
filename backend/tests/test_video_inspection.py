import json
import subprocess

import pytest

from app.services.video_inspection import FFPROBE_TIMEOUT_SECONDS, FFprobeVideoInspectionService, VideoInspectionError, parse_ffprobe_json


def ffprobe_payload(**stream_overrides: object) -> str:
    stream = {
        "codec_type": "video",
        "codec_name": "h264",
        "width": 1920,
        "height": 1080,
        "avg_frame_rate": "60/1",
        "duration": "95.5",
    }
    stream.update(stream_overrides)
    return json.dumps({"streams": [stream], "format": {"duration": "100.0"}})


def test_valid_ffprobe_json_is_normalized():
    metadata = parse_ffprobe_json(ffprobe_payload())

    assert metadata.duration_seconds == 95.5
    assert metadata.width == 1920
    assert metadata.height == 1080
    assert metadata.fps == 60.0
    assert metadata.codec == "h264"


def test_fractional_frame_rate_is_normalized():
    metadata = parse_ffprobe_json(ffprobe_payload(avg_frame_rate="60000/1001"))

    assert metadata.fps == 59.94


def test_format_duration_is_used_when_stream_duration_is_missing():
    metadata = parse_ffprobe_json(ffprobe_payload(duration=None))

    assert metadata.duration_seconds == 100.0


def test_no_video_stream_is_rejected():
    with pytest.raises(VideoInspectionError, match="No usable video stream"):
        parse_ffprobe_json(json.dumps({"streams": [{"codec_type": "audio"}], "format": {"duration": "1.0"}}))


def test_missing_resolution_is_rejected():
    with pytest.raises(VideoInspectionError, match="resolution"):
        parse_ffprobe_json(ffprobe_payload(width=None))


def test_malformed_ffprobe_output_is_rejected():
    with pytest.raises(VideoInspectionError, match="not readable"):
        parse_ffprobe_json("{not-json")


def test_subprocess_failure_is_safe(monkeypatch: pytest.MonkeyPatch):
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(1, ["ffprobe"], stderr="raw internal error")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(VideoInspectionError, match="metadata inspection failed"):
        FFprobeVideoInspectionService().inspect("bad.mp4")


def test_ffprobe_timeout_is_safe(monkeypatch: pytest.MonkeyPatch):
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(["ffprobe"], timeout=FFPROBE_TIMEOUT_SECONDS)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(VideoInspectionError, match="metadata inspection timed out"):
        FFprobeVideoInspectionService().inspect("slow.mp4")


def test_missing_ffprobe_executable_is_safe(monkeypatch: pytest.MonkeyPatch):
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("ffprobe")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(VideoInspectionError, match="inspection tool is not available"):
        FFprobeVideoInspectionService().inspect("set.mp4")


def test_inspector_requests_machine_readable_ffprobe_json(monkeypatch: pytest.MonkeyPatch):
    calls: list[dict] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(command, 0, stdout=ffprobe_payload(), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    metadata = FFprobeVideoInspectionService().inspect("set.mp4")

    assert metadata.width == 1920
    assert "-print_format" in calls[0]["command"]
    assert "json" in calls[0]["command"]
    assert "-show_format" in calls[0]["command"]
    assert "-show_streams" in calls[0]["command"]
    assert calls[0]["check"] is True
    assert calls[0]["capture_output"] is True
    assert calls[0]["text"] is True
    assert calls[0]["timeout"] == FFPROBE_TIMEOUT_SECONDS
