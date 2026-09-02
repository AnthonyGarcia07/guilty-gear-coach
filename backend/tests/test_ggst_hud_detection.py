from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from app.services.ggst_hud_detection import (
    GGSTHudDetectionError,
    GGSTHudDetectionService,
    HUD_REGIONS,
)


def save_image(image: Image.Image, path: Path) -> Path:
    image.save(path)
    return path


def blank_image(size: tuple[int, int] = (640, 360), color: int | tuple[int, ...] = 12, mode: str = "L") -> Image.Image:
    return Image.new(mode, size, color)


def draw_horizontal_structure(image: Image.Image, region_name: str, *, lines: int = 5, fill: int | tuple[int, ...] = 240) -> None:
    draw = ImageDraw.Draw(image)
    width, height = image.size
    left, top, right, bottom = HUD_REGIONS[region_name]
    x1 = round(left * width)
    y1 = round(top * height)
    x2 = round(right * width)
    y2 = round(bottom * height)
    region_height = y2 - y1
    thickness = max(2, round(height * 0.006))

    for index in range(lines):
        y = y1 + round((index + 1) * region_height / (lines + 1))
        draw.rectangle((x1, y, x2, min(y + thickness, y2)), fill=fill)


def draw_standard_hud(image: Image.Image) -> None:
    draw_horizontal_structure(image, "top_left")
    draw_horizontal_structure(image, "top_right")
    draw_horizontal_structure(image, "top_center", lines=4)
    draw_horizontal_structure(image, "bottom_left", lines=3)
    draw_horizontal_structure(image, "bottom_right", lines=3)


def detect_saved(tmp_path: Path, image: Image.Image, filename: str = "frame.png"):
    return GGSTHudDetectionService().detect(save_image(image, tmp_path / filename))


def test_strong_bilateral_top_hud_with_support_is_likely_gameplay_hud(tmp_path):
    image = blank_image()
    draw_standard_hud(image)

    result = detect_saved(tmp_path, image)

    assert result.classification == "likely_gameplay_hud"
    assert result.evidence["top_left_hud"] is True
    assert result.evidence["top_right_hud"] is True
    assert result.evidence["bilateral_top_hud"] is True
    assert result.evidence["top_center_support"] is True


def test_no_hud_structure_is_not_gameplay_hud(tmp_path):
    image = blank_image(color=30)

    result = detect_saved(tmp_path, image)

    assert result.classification == "not_gameplay_hud"
    assert result.evidence["top_left_hud"] is False
    assert result.evidence["top_right_hud"] is False
    assert result.evidence["top_center_support"] is False
    assert result.evidence["bottom_support"] is False


def test_transition_like_center_structure_without_bilateral_hud_is_unknown(tmp_path):
    image = blank_image()
    draw_horizontal_structure(image, "top_center", lines=5)

    result = detect_saved(tmp_path, image)

    assert result.classification == "unknown"
    assert result.evidence["top_center_support"] is True
    assert result.evidence["bilateral_top_hud"] is False


def test_only_one_top_hud_side_is_unknown(tmp_path):
    image = blank_image()
    draw_horizontal_structure(image, "top_left")
    draw_horizontal_structure(image, "top_center", lines=4)

    result = detect_saved(tmp_path, image)

    assert result.classification == "unknown"
    assert result.evidence["top_left_hud"] is True
    assert result.evidence["top_right_hud"] is False


def test_bottom_support_without_bilateral_top_hud_is_unknown(tmp_path):
    image = blank_image()
    draw_horizontal_structure(image, "bottom_left", lines=5)
    draw_horizontal_structure(image, "bottom_right", lines=5)

    result = detect_saved(tmp_path, image)

    assert result.classification == "unknown"
    assert result.evidence["bottom_support"] is True
    assert result.evidence["bilateral_top_hud"] is False


def test_noisy_center_with_intact_bilateral_top_hud_remains_likely_gameplay_hud(tmp_path):
    image = blank_image()
    draw = ImageDraw.Draw(image)
    for offset in range(0, 220, 11):
        draw.rectangle((140 + offset, 95, 150 + offset, 270), fill=80 + (offset % 150))
    draw_horizontal_structure(image, "top_left")
    draw_horizontal_structure(image, "top_right")
    draw_horizontal_structure(image, "bottom_right", lines=4)

    result = detect_saved(tmp_path, image)

    assert result.classification == "likely_gameplay_hud"
    assert result.evidence["top_left_hud"] is True
    assert result.evidence["top_right_hud"] is True
    assert result.evidence["bottom_support"] is True


def test_normalized_regions_scale_across_16_by_9_resolutions(tmp_path):
    small = blank_image(size=(640, 360))
    large = blank_image(size=(1280, 720))
    draw_standard_hud(small)
    draw_standard_hud(large)

    small_result = detect_saved(tmp_path, small, "small.png")
    large_result = detect_saved(tmp_path, large, "large.png")

    assert small_result.classification == "likely_gameplay_hud"
    assert large_result.classification == "likely_gameplay_hud"
    assert small_result.evidence == large_result.evidence


def test_rgba_grayscale_png_and_jpeg_inputs_are_supported(tmp_path):
    rgba = blank_image(mode="RGBA", color=(12, 12, 12, 255))
    grayscale = blank_image(mode="L", color=12)
    draw_standard_hud(rgba)
    draw_standard_hud(grayscale)

    rgba_result = GGSTHudDetectionService().detect(save_image(rgba, tmp_path / "rgba.png"))
    grayscale_result = GGSTHudDetectionService().detect(save_image(grayscale, tmp_path / "grayscale.jpg"))

    assert rgba_result.classification == "likely_gameplay_hud"
    assert grayscale_result.classification == "likely_gameplay_hud"


def test_result_includes_explicit_evidence_and_raw_measurements(tmp_path):
    image = blank_image()
    draw_standard_hud(image)

    result = detect_saved(tmp_path, image)

    assert set(result.evidence) == {
        "top_left_hud",
        "top_right_hud",
        "top_center_support",
        "bottom_support",
        "transition_hint",
        "bilateral_top_hud",
    }
    assert result.measurements["image_width"] == 640
    assert result.measurements["image_height"] == 360
    assert result.measurements["top_left_horizontal_edge_score"] > 0
    assert result.measurements["top_center_stddev"] > 0


def test_missing_or_invalid_image_raises_safe_detector_error(tmp_path):
    service = GGSTHudDetectionService()
    invalid = tmp_path / "not-an-image.txt"
    invalid.write_text("definitely not pixels")
    tiny = save_image(blank_image(size=(1, 1)), tmp_path / "tiny.png")

    with pytest.raises(GGSTHudDetectionError, match="could not be read"):
        service.detect(tmp_path / "missing.png")
    with pytest.raises(GGSTHudDetectionError, match="could not be read"):
        service.detect(invalid)
    with pytest.raises(GGSTHudDetectionError, match="too small"):
        service.detect(tiny)
