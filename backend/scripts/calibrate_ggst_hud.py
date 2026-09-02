"""Local-only GGST HUD calibration utility.

This script measures ignored development fixtures under dev-fixtures/ggst-hud.
It is intentionally not production detector logic.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageStat


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = PROJECT_ROOT / "dev-fixtures" / "ggst-hud"

FIXTURES = [
    ("intro", "2s-intro.png"),
    ("duel", "9s-duel.png"),
    ("gameplay", "15s-gameplay.png"),
    ("effects", "54s-gameplay-effects.png"),
    ("slash", "61s-slash.png"),
]

REGIONS = {
    "top_left": (0.03, 0.03, 0.43, 0.18),
    "top_center": (0.42, 0.02, 0.58, 0.18),
    "top_right": (0.57, 0.03, 0.97, 0.18),
    "bottom_left": (0.03, 0.82, 0.34, 0.97),
    "bottom_right": (0.66, 0.82, 0.97, 0.97),
}


def crop_region(image: Image.Image, bounds: tuple[float, float, float, float]) -> Image.Image:
    width, height = image.size
    left, top, right, bottom = bounds
    return image.crop((
        round(left * width),
        round(top * height),
        round(right * width),
        round(bottom * height),
    )).convert("L")


def region_metrics(region: Image.Image) -> dict[str, float]:
    normalized = region.resize((160, max(1, round(region.height * 160 / region.width))))
    if hasattr(normalized, "get_flattened_data"):
        pixels = list(normalized.get_flattened_data())
    else:
        pixels = list(normalized.getdata())
    mean = sum(pixels) / len(pixels)
    variance = sum((pixel - mean) ** 2 for pixel in pixels) / len(pixels)
    bright_fraction = sum(1 for pixel in pixels if pixel >= 200) / len(pixels)
    dark_fraction = sum(1 for pixel in pixels if pixel <= 45) / len(pixels)
    horizontal_edge_score = adjacent_difference(normalized, axis="y")
    vertical_edge_score = adjacent_difference(normalized, axis="x")
    return {
        "mean": mean,
        "stddev": math.sqrt(variance),
        "bright": bright_fraction,
        "dark": dark_fraction,
        "h_edge": horizontal_edge_score,
        "v_edge": vertical_edge_score,
    }


def adjacent_difference(image: Image.Image, axis: str) -> float:
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


def top_symmetry(left: Image.Image, right: Image.Image) -> float:
    right_flipped = ImageOps.mirror(right)
    right_resized = right_flipped.resize(left.size)
    difference = ImageChops.difference(left, right_resized)
    mean_difference = ImageStat.Stat(difference).mean[0]
    return 1 - (mean_difference / 255)


def format_row(label: str, values: list[float], precision: int = 2) -> str:
    formatted = " | ".join(f"{value:.{precision}f}" for value in values)
    return f"| {label} | {formatted} |"


def main() -> None:
    loaded_images = [(label, Image.open(FIXTURE_DIR / filename).convert("RGB")) for label, filename in FIXTURES]
    print("# GGST HUD calibration measurements")
    print()
    print("Fixtures:", ", ".join(label for label, _ in loaded_images))
    print()
    print("Normalized regions:")
    for name, bounds in REGIONS.items():
        print(f"- {name}: {bounds}")
    print()
    print("## Image sizes")
    print("| fixture | width | height |")
    print("| --- | ---: | ---: |")
    for label, image in loaded_images:
        print(f"| {label} | {image.width} | {image.height} |")
    print()

    all_metrics: dict[str, dict[str, dict[str, float]]] = {}
    for label, image in loaded_images:
        all_metrics[label] = {}
        for region_name, bounds in REGIONS.items():
            all_metrics[label][region_name] = region_metrics(crop_region(image, bounds))

    fixture_labels = [label for label, _ in loaded_images]
    for metric_name, display_name, precision in [
        ("mean", "Grayscale mean", 1),
        ("stddev", "Grayscale standard deviation", 1),
        ("bright", "Bright pixel fraction", 3),
        ("dark", "Dark pixel fraction", 3),
        ("h_edge", "Horizontal edge-like score", 2),
        ("v_edge", "Vertical edge-like score", 2),
    ]:
        print(f"## {display_name}")
        print("| region | " + " | ".join(fixture_labels) + " |")
        print("| --- | " + " | ".join("---:" for _ in fixture_labels) + " |")
        for region_name in REGIONS:
            values = [all_metrics[label][region_name][metric_name] for label in fixture_labels]
            print(format_row(region_name, values, precision))
        print()

    print("## Top left/right mirrored similarity")
    print("| measurement | " + " | ".join(fixture_labels) + " |")
    print("| --- | " + " | ".join("---:" for _ in fixture_labels) + " |")
    similarities = []
    for _, image in loaded_images:
        similarities.append(top_symmetry(crop_region(image, REGIONS["top_left"]), crop_region(image, REGIONS["top_right"])))
    print(format_row("top_symmetry", similarities, 3))


if __name__ == "__main__":
    main()
