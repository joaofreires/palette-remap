"""Tests for the MCP server tools."""

from pathlib import Path

import numpy as np
import pytest
from palette_remap.mcp_server import list_image_colors, preview_palette, remap_image_tool
from PIL import Image

# ─── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def red_green_image(tmp_path: Path) -> Path:
    img = Image.new("RGBA", (2, 1))
    img.putpixel((0, 0), (255, 0, 0, 255))
    img.putpixel((1, 0), (0, 255, 0, 255))
    p = tmp_path / "rg.png"
    img.save(p)
    return p


# ─── remap_image_tool ─────────────────────────────────────────────────────────


def test_remap_image_tool(red_green_image: Path, tmp_path: Path):
    out = tmp_path / "out.png"
    result = remap_image_tool(str(red_green_image), str(out), palette_colors="#ff0000 #00ff00", keep_transparency=True)
    assert "error" not in result
    assert result["output_path"] == str(out)
    assert result["palette_size"] == 2
    assert result["width"] == 2
    assert result["height"] == 1
    assert out.exists()

    arr = np.array(Image.open(out).convert("RGBA"))
    assert tuple(arr[0, 0])[:3] == (255, 0, 0)
    assert tuple(arr[0, 1])[:3] == (0, 255, 0)


def test_remap_image_tool_no_palette(red_green_image: Path, tmp_path: Path):
    result = remap_image_tool(str(red_green_image), str(tmp_path / "out.png"))
    assert "error" in result


def test_remap_image_tool_bad_path(tmp_path: Path):
    result = remap_image_tool("/nonexistent/image.png", str(tmp_path / "out.png"), palette_colors="#ff0000")
    assert "error" in result


# ─── preview_palette ──────────────────────────────────────────────────────────


def test_preview_palette_string():
    result = preview_palette(palette_colors="#ff0000 #00ff00 #0000ff")
    assert "3 colors" in result
    assert "#ff0000" in result


def test_preview_palette_file(tmp_path: Path):
    hexfile = tmp_path / "pal.hex"
    hexfile.write_text("ff0000\n00ff00\n0000ff\n")
    result = preview_palette(palette_file=str(hexfile))
    assert "3 colors" in result


def test_preview_palette_no_input():
    result = preview_palette()
    assert "Error" in result


# ─── list_image_colors ────────────────────────────────────────────────────────


def test_list_image_colors(red_green_image: Path):
    result = list_image_colors(str(red_green_image))
    assert "#ff0000" in result
    assert "#00ff00" in result
    assert "2×1" in result


def test_list_image_colors_max_colors(tmp_path: Path):
    img = Image.new("RGBA", (4, 1))
    for i, c in enumerate([(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]):
        img.putpixel((i, 0), c)
    p = tmp_path / "four.png"
    img.save(p)
    result = list_image_colors(str(p), max_colors=2)
    assert "showing top 2 of 4" in result


def test_list_image_colors_bad_path():
    result = list_image_colors("/nonexistent/image.png")
    assert "Error" in result
