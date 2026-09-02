import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image, UnidentifiedImageError


GGSTHudClassification = Literal["likely_gameplay_hud", "not_gameplay_hud", "unknown"]

TOP_LEFT_HUD_EDGE_THRESHOLD = 13.0
TOP_RIGHT_HUD_EDGE_THRESHOLD = 13.0
TOP_CENTER_SUPPORT_EDGE_THRESHOLD = 11.0
BOTTOM_LEFT_SUPPORT_EDGE_THRESHOLD = 12.0
BOTTOM_RIGHT_SUPPORT_EDGE_THRESHOLD = 9.0
TOP_CENTER_TRANSITION_STDDEV_THRESHOLD = 50.0
BLANK_FRAME_STDDEV_THRESHOLD = 1.0
BLANK_REGION_EDGE_THRESHOLD = 1.0
REGION_NORMALIZED_WIDTH = 160

HUD_REGIONS: dict[str, tuple[float, float, float, float]] = {
    "top_left": (0.03, 0.03, 0.43, 0.18),
    "top_center": (0.42, 0.02, 0.58, 0.18),
    "top_right": (0.57, 0.03, 0.97, 0.18),
    "bottom_left": (0.03, 0.82, 0.34, 0.97),
    "bottom_right": (0.66, 0.82, 0.97, 0.97),
}


class GGSTHudDetectionError(RuntimeError):
    def __init__(self, public_message: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message


@dataclass(frozen=True)
class GGSTHudDetectionResult:
    classification: GGSTHudClassification
    evidence: dict[str, bool]
    measurements: dict[str, float]


class GGSTHudDetectionService:
    def detect(self, image_path: str | Path) -> GGSTHudDetectionResult:
        image = load_image(image_path)
        region_measurements = {
            region_name: measure_region(crop_region(image, bounds))
            for region_name, bounds in HUD_REGIONS.items()
        }
        measurements = flatten_measurements(image, region_measurements)
        evidence = build_evidence(measurements)
        return GGSTHudDetectionResult(
            classification=classify_evidence(evidence),
            evidence=evidence,
            measurements=measurements,
        )


def load_image(image_path: str | Path) -> Image.Image:
    try:
        with Image.open(image_path) as image:
            loaded = image.convert("RGB")
            loaded.load()
            return loaded
    except (FileNotFoundError, OSError, UnidentifiedImageError) as error:
        raise GGSTHudDetectionError("HUD detection image could not be read.") from error


def crop_region(image: Image.Image, bounds: tuple[float, float, float, float]) -> Image.Image:
    width, height = image.size
    if width <= 0 or height <= 0:
        raise GGSTHudDetectionError("HUD detection image has invalid dimensions.")

    left, top, right, bottom = bounds
    crop_box = (
        round(left * width),
        round(top * height),
        round(right * width),
        round(bottom * height),
    )
    if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
        raise GGSTHudDetectionError("HUD detection image is too small to inspect.")

    return image.crop(crop_box).convert("L")


def measure_region(region: Image.Image) -> dict[str, float]:
    normalized_height = max(1, round(region.height * REGION_NORMALIZED_WIDTH / region.width))
    normalized = region.resize((REGION_NORMALIZED_WIDTH, normalized_height))
    pixels = flattened_pixels(normalized)
    mean = sum(pixels) / len(pixels)
    variance = sum((pixel - mean) ** 2 for pixel in pixels) / len(pixels)
    return {
        "horizontal_edge_score": adjacent_intensity_difference(normalized, axis="y"),
        "stddev": math.sqrt(variance),
    }


def flattened_pixels(image: Image.Image) -> list[int]:
    if hasattr(image, "get_flattened_data"):
        return list(image.get_flattened_data())
    return list(image.getdata())


def adjacent_intensity_difference(image: Image.Image, axis: Literal["x", "y"]) -> float:
    width, height = image.size
    pixels = image.load()
    total = 0
    count = 0

    if axis == "x":
        for y in range(height):
            for x in range(width - 1):
                total += abs(pixels[x + 1, y] - pixels[x, y])
                count += 1
    else:
        for y in range(height - 1):
            for x in range(width):
                total += abs(pixels[x, y + 1] - pixels[x, y])
                count += 1

    return total / count if count else 0.0


def flatten_measurements(image: Image.Image, region_measurements: dict[str, dict[str, float]]) -> dict[str, float]:
    grayscale_image = image.convert("L")
    image_pixels = flattened_pixels(grayscale_image)
    image_mean = sum(image_pixels) / len(image_pixels)
    image_variance = sum((pixel - image_mean) ** 2 for pixel in image_pixels) / len(image_pixels)
    measurements = {
        "image_width": float(image.width),
        "image_height": float(image.height),
        "image_stddev": round(math.sqrt(image_variance), 3),
    }
    for region_name, metrics in region_measurements.items():
        for metric_name, value in metrics.items():
            measurements[f"{region_name}_{metric_name}"] = round(value, 3)
    return measurements


def build_evidence(measurements: dict[str, float]) -> dict[str, bool]:
    top_left_hud = measurements["top_left_horizontal_edge_score"] >= TOP_LEFT_HUD_EDGE_THRESHOLD
    top_right_hud = measurements["top_right_horizontal_edge_score"] >= TOP_RIGHT_HUD_EDGE_THRESHOLD
    top_center_support = measurements["top_center_horizontal_edge_score"] >= TOP_CENTER_SUPPORT_EDGE_THRESHOLD
    bottom_support = (
        measurements["bottom_left_horizontal_edge_score"] >= BOTTOM_LEFT_SUPPORT_EDGE_THRESHOLD
        or measurements["bottom_right_horizontal_edge_score"] >= BOTTOM_RIGHT_SUPPORT_EDGE_THRESHOLD
    )
    transition_hint = measurements["top_center_stddev"] >= TOP_CENTER_TRANSITION_STDDEV_THRESHOLD and not (top_left_hud and top_right_hud)
    blank_frame = (
        measurements["image_stddev"] < BLANK_FRAME_STDDEV_THRESHOLD
        and measurements["top_left_horizontal_edge_score"] < BLANK_REGION_EDGE_THRESHOLD
        and measurements["top_center_horizontal_edge_score"] < BLANK_REGION_EDGE_THRESHOLD
        and measurements["top_right_horizontal_edge_score"] < BLANK_REGION_EDGE_THRESHOLD
        and measurements["bottom_left_horizontal_edge_score"] < BLANK_REGION_EDGE_THRESHOLD
        and measurements["bottom_right_horizontal_edge_score"] < BLANK_REGION_EDGE_THRESHOLD
    )

    return {
        "top_left_hud": top_left_hud,
        "top_right_hud": top_right_hud,
        "top_center_support": top_center_support,
        "bottom_support": bottom_support,
        "transition_hint": transition_hint,
        "bilateral_top_hud": top_left_hud and top_right_hud,
        "blank_frame": blank_frame,
    }


def classify_evidence(evidence: dict[str, bool]) -> GGSTHudClassification:
    if evidence["bilateral_top_hud"] and (evidence["top_center_support"] or evidence["bottom_support"]):
        return "likely_gameplay_hud"
    if evidence["blank_frame"]:
        return "unknown"
    if (
        not evidence["top_left_hud"]
        and not evidence["top_right_hud"]
        and not evidence["top_center_support"]
        and not evidence["bottom_support"]
        and not evidence["transition_hint"]
    ):
        return "not_gameplay_hud"
    return "unknown"
