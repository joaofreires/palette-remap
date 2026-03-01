"""MCP server exposing palette-remap tools to LLMs."""

from pathlib import Path
from typing import Any, Dict

import numpy as np
from mcp.server.fastmcp import FastMCP
from PIL import Image

from .core import load_palette_from_file, parse_palette, remap_pil_image

mcp = FastMCP(
    "palette-remap",
    instructions=(
        "Tools to remap pixel-art or sprite images to a constrained color palette. "
        "All tools work with file paths on the server filesystem. "
        "Pair this server with mcp/filesystem so you can read directory listings and "
        "pass the correct absolute paths to image_path / output_path. "
        "Use `remap_image_tool` to convert an image, `preview_palette` to inspect palette "
        "colors, and `list_image_colors` to discover the colors present in an image."
    ),
)


def _open_image(image_path: str) -> Image.Image:
    """Open an image from a filesystem path."""
    return Image.open(Path(image_path))


@mcp.tool()
def remap_image_tool(
    image_path: str,
    output_path: str,
    palette_colors: str = "",
    palette_file: str = "",
    use_palette_alpha: bool = False,
    keep_transparency: bool = True,
) -> Dict[str, Any]:
    """Remap every pixel of an image to the closest color from a palette.

    Args:
        image_path: Path to the source image file (readable by the server).
        output_path: Path where the remapped image will be saved.
        palette_colors: Space/comma-separated hex colors, e.g. "#d1b187 #c77b58".
        palette_file: Optional path to a .hex/.txt palette file.
        use_palette_alpha: If True, use the alpha channel from the matched palette color.
        keep_transparency: If True, fully transparent pixels (alpha=0) remain transparent.

    Returns a dict with keys: output_path, palette_size, width, height.
    """
    palette = []
    if palette_colors:
        palette.extend(parse_palette(palette_colors))
    if palette_file:
        palette.extend(load_palette_from_file(Path(palette_file)))
    if not palette:
        return {"error": "Provide at least one of palette_colors or palette_file."}

    try:
        img = _open_image(image_path)
    except Exception as e:
        return {"error": f"Could not load image: {e}"}

    result = remap_pil_image(img, palette, use_palette_alpha=use_palette_alpha, keep_transparency=keep_transparency)
    result.save(output_path)
    return {
        "output_path": output_path,
        "palette_size": len(palette),
        "width": result.width,
        "height": result.height,
    }


@mcp.tool()
def preview_palette(
    palette_colors: str = "",
    palette_file: str = "",
) -> str:
    """Parse and list palette colors from a string and/or a file.

    Useful for confirming what colors will be used before remapping.

    Args:
        palette_colors: Space/comma-separated hex colors, e.g. "#000 #fff #f00".
        palette_file: Path to a .hex/.txt file.
    """
    palette = []
    if palette_colors:
        palette.extend(parse_palette(palette_colors))
    if palette_file:
        palette.extend(load_palette_from_file(Path(palette_file)))
    if not palette:
        return "Error: provide at least one of palette_colors or palette_file."

    lines = [f"  {i + 1:2d}) {c}" for i, c in enumerate(palette)]
    return f"Palette ({len(palette)} colors):\n" + "\n".join(lines)


@mcp.tool()
def list_image_colors(
    image_path: str,
    max_colors: int = 32,
    min_pixel_percent: float = 0.0,
) -> str:
    """List the most frequent distinct colors in an image.

    Args:
        image_path: Path to the image file (readable by the server).
        max_colors: Maximum number of colors to return (sorted by frequency, default 32).
        min_pixel_percent: Skip colors that make up less than this % of total pixels (0\u2013100).
    """
    try:
        img = _open_image(image_path).convert("RGBA")
    except Exception as e:
        return f"Error: Could not load image: {e}"
    arr = np.array(img).reshape(-1, 4)
    total = len(arr)

    # Structured view for fast unique counting
    view = arr.view(np.dtype((np.void, arr.dtype.itemsize * arr.shape[1])))
    unique_raw, counts = np.unique(view, return_counts=True)
    order = np.argsort(-counts)
    unique_raw = unique_raw[order]
    counts = counts[order]

    rows = []
    shown = 0
    for raw, count in zip(unique_raw, counts):
        pct = 100.0 * count / total
        if pct < min_pixel_percent:
            continue
        r, g, b, a = np.frombuffer(bytes(raw), dtype=np.uint8)
        alpha_note = f" (alpha={a})" if a != 255 else ""
        rows.append(f"  #{r:02x}{g:02x}{b:02x}{alpha_note} — {count:,} px ({pct:.2f}%)")
        shown += 1
        if shown >= max_colors:
            break

    truncation = f"\n  … showing top {max_colors} of {len(counts)} unique colors" if len(counts) > max_colors else ""
    return f"Image: {img.width}×{img.height}, {total:,} pixels\n" + "\n".join(rows) + truncation


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
