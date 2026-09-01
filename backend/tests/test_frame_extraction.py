import math
import subprocess

import pytest

from app.services.frame_extraction import (
    FRAME_EXTRACTION_TIMEOUT_SECONDS,
    FRAME_EXTRACTION_WIDTH,
    FFmpegFrameExtractionService,
    FrameExtractionError,
    format_timestamp,
    validate_timestamp,
)


def test_extract_jpeg_frame_runs_ffmpeg_with_safe_arguments(monkeypatch, tmp_path):
    video_path = tmp_path / "replay.mp4"
    output_path = tmp_path / "frame.jpg"
    calls = []

    def fake_run(command, **kwargs):
        calls.append({"command": command, "kwargs": kwargs})
        output_path.write_bytes(b"\xff\xd8fake-jpeg\xff\xd9")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    FFmpegFrameExtractionService().extract_jpeg_frame(video_path, 10.25, output_path)

    command = calls[0]["command"]
    assert command[:2] == ["ffmpeg", "-v"]
    assert "-ss" in command
    assert command[command.index("-ss") + 1] == "10.25"
    assert str(video_path) in command
    assert command[command.index("-frames:v") + 1] == "1"
    assert command[command.index("-vf") + 1] == f"scale='min({FRAME_EXTRACTION_WIDTH},iw)':-2"
    assert command[command.index("-q:v") + 1] == "3"
    assert command[-1] == str(output_path)
    assert calls[0]["kwargs"]["check"] is True
    assert calls[0]["kwargs"]["capture_output"] is True
    assert calls[0]["kwargs"]["text"] is True
    assert calls[0]["kwargs"]["timeout"] == FRAME_EXTRACTION_TIMEOUT_SECONDS
    assert "shell" not in calls[0]["kwargs"]


def test_extract_jpeg_frame_uses_safe_timestamp_formatting(monkeypatch, tmp_path):
    video_path = tmp_path / "replay.mp4"
    output_path = tmp_path / "frame.jpg"
    seen_command = []

    def fake_run(command, **kwargs):
        seen_command.extend(command)
        output_path.write_bytes(b"\xff\xd8fake-jpeg\xff\xd9")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    FFmpegFrameExtractionService().extract_jpeg_frame(video_path, 1.23456, output_path)

    assert seen_command[seen_command.index("-ss") + 1] == "1.235"


def test_extract_jpeg_frame_converts_nonzero_ffmpeg_failure_to_safe_error(monkeypatch, tmp_path):
    def fake_run(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, stderr="internal ffmpeg details")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(FrameExtractionError, match="Frame extraction failed."):
        FFmpegFrameExtractionService().extract_jpeg_frame(tmp_path / "replay.mp4", 10, tmp_path / "frame.jpg")


def test_extract_jpeg_frame_converts_timeout_to_safe_error(monkeypatch, tmp_path):
    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, timeout=FRAME_EXTRACTION_TIMEOUT_SECONDS)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(FrameExtractionError, match="Frame extraction timed out."):
        FFmpegFrameExtractionService().extract_jpeg_frame(tmp_path / "replay.mp4", 10, tmp_path / "frame.jpg")


def test_extract_jpeg_frame_converts_missing_ffmpeg_to_safe_error(monkeypatch, tmp_path):
    def fake_run(command, **kwargs):
        raise FileNotFoundError("ffmpeg")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(FrameExtractionError, match="Frame extraction tool is not available."):
        FFmpegFrameExtractionService().extract_jpeg_frame(tmp_path / "replay.mp4", 10, tmp_path / "frame.jpg")


def test_extract_jpeg_frame_requires_non_empty_output(monkeypatch, tmp_path):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(FrameExtractionError, match="Frame extraction did not produce an image."):
        FFmpegFrameExtractionService().extract_jpeg_frame(tmp_path / "replay.mp4", 10, tmp_path / "frame.jpg")


def test_timestamp_validation_rejects_non_finite_and_negative_values():
    assert validate_timestamp(0) == 0
    assert validate_timestamp("10.5") == 10.5
    assert format_timestamp(10.0) == "10"
    assert format_timestamp(10.25) == "10.25"

    with pytest.raises(FrameExtractionError):
        validate_timestamp(-0.1)
    with pytest.raises(FrameExtractionError):
        validate_timestamp(math.inf)
    with pytest.raises(FrameExtractionError):
        validate_timestamp("not-a-number")
