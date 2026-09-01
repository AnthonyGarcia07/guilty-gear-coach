import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

FFPROBE_TIMEOUT_SECONDS = 15


class VideoInspectionError(RuntimeError):
    def __init__(self, public_message: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message


@dataclass(frozen=True)
class VideoMetadata:
    duration_seconds: float | None
    width: int
    height: int
    fps: float | None
    codec: str | None


class FFprobeVideoInspectionService:
    def __init__(self, ffprobe_path: str = "ffprobe") -> None:
        self.ffprobe_path = ffprobe_path

    def inspect(self, video_path: str | Path) -> VideoMetadata:
        try:
            completed = subprocess.run(
                [
                    self.ffprobe_path,
                    "-v",
                    "error",
                    "-print_format",
                    "json",
                    "-show_format",
                    "-show_streams",
                    str(video_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=FFPROBE_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as error:
            raise VideoInspectionError("Video inspection tool is not available.") from error
        except subprocess.TimeoutExpired as error:
            raise VideoInspectionError("Video metadata inspection timed out.") from error
        except subprocess.CalledProcessError as error:
            raise VideoInspectionError("Video metadata inspection failed.") from error

        return parse_ffprobe_json(completed.stdout)


def parse_ffprobe_json(output: str) -> VideoMetadata:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as error:
        raise VideoInspectionError("Video metadata output was not readable.") from error

    if not isinstance(payload, dict):
        raise VideoInspectionError("Video metadata output was not readable.")

    streams = payload.get("streams")
    if not isinstance(streams, list):
        raise VideoInspectionError("Video metadata output did not include streams.")

    video_stream = next((stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "video"), None)
    if video_stream is None:
        raise VideoInspectionError("No usable video stream was found.")

    width = positive_int(video_stream.get("width"))
    height = positive_int(video_stream.get("height"))
    if width is None or height is None:
        raise VideoInspectionError("Video stream is missing resolution metadata.")

    duration = first_positive_float(video_stream.get("duration"), nested_get(payload, "format", "duration"))
    fps = parse_frame_rate(video_stream.get("avg_frame_rate")) or parse_frame_rate(video_stream.get("r_frame_rate"))
    codec = cleaned_string(video_stream.get("codec_name"))

    return VideoMetadata(
        duration_seconds=round(duration, 3) if duration is not None else None,
        width=width,
        height=height,
        fps=round(fps, 3) if fps is not None else None,
        codec=codec,
    )


def nested_get(payload: dict[str, Any], key: str, nested_key: str) -> Any:
    value = payload.get(key)
    return value.get(nested_key) if isinstance(value, dict) else None


def positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def first_positive_float(*values: Any) -> float | None:
    for value in values:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if parsed >= 0:
            return parsed
    return None


def parse_frame_rate(value: Any) -> float | None:
    if not isinstance(value, str) or value in {"", "0/0"}:
        return None
    try:
        parsed = float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None
    return parsed if parsed > 0 else None


def cleaned_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None
