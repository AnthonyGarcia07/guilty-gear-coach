import math
import subprocess
from pathlib import Path

FRAME_EXTRACTION_TIMEOUT_SECONDS = 20
FRAME_EXTRACTION_WIDTH = 640


class FrameExtractionError(RuntimeError):
    def __init__(self, public_message: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message


class FFmpegFrameExtractionService:
    def __init__(self, ffmpeg_path: str = "ffmpeg") -> None:
        self.ffmpeg_path = ffmpeg_path

    def extract_jpeg_frame(self, video_path: str | Path, timestamp_seconds: float, output_path: str | Path) -> None:
        timestamp = validate_timestamp(timestamp_seconds)
        try:
            subprocess.run(
                [
                    self.ffmpeg_path,
                    "-v",
                    "error",
                    "-ss",
                    format_timestamp(timestamp),
                    "-i",
                    str(video_path),
                    "-frames:v",
                    "1",
                    "-vf",
                    f"scale='min({FRAME_EXTRACTION_WIDTH},iw)':-2",
                    "-q:v",
                    "3",
                    "-y",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=FRAME_EXTRACTION_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as error:
            raise FrameExtractionError("Frame extraction tool is not available.") from error
        except subprocess.TimeoutExpired as error:
            raise FrameExtractionError("Frame extraction timed out.") from error
        except subprocess.CalledProcessError as error:
            raise FrameExtractionError("Frame extraction failed.") from error

        output = Path(output_path)
        if not output.exists() or output.stat().st_size <= 0:
            raise FrameExtractionError("Frame extraction did not produce an image.")


def validate_timestamp(timestamp_seconds: float) -> float:
    try:
        timestamp = float(timestamp_seconds)
    except (TypeError, ValueError) as error:
        raise FrameExtractionError("Timestamp must be a valid number.") from error
    if not math.isfinite(timestamp) or timestamp < 0:
        raise FrameExtractionError("Timestamp must be a finite number greater than or equal to 0.")
    return timestamp


def format_timestamp(timestamp_seconds: float) -> str:
    return f"{timestamp_seconds:.3f}".rstrip("0").rstrip(".")
