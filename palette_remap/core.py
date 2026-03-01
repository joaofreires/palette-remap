import sys
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image

from .models import Color


def parse_palette(value: str) -> List[Color]:
    """Parse palette from single string argument (spaces or commas)"""
    items = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        for subpart in part.split():
            subpart = subpart.strip()
            if subpart:
                items.append(subpart)

    if not items:
        raise ValueError("No colors found in palette string")

    colors: List[Color] = []
    for item in items:
        colors.append(Color.from_any(item))
    return colors


def load_palette_from_file(filepath: Path) -> List[Color]:
    """Load palette from .hex / .txt file (one or more colors per line)"""
    if not filepath.is_file():
        raise FileNotFoundError(f"Palette file not found: {filepath}")

    colors: List[Color] = []
    with filepath.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith(("#", ";", "//", "!")):
                continue

            for part in line.replace(",", " ").split():
                part = part.strip()
                if not part:
                    continue
                try:
                    colors.append(Color.from_any(part))
                except Exception as e:
                    print(
                        f"Warning: Invalid color at {filepath}:{lineno}: '{part}' ({e})",
                        file=sys.stderr,
                    )

    if not colors:
        raise ValueError(f"No valid colors found in {filepath}")

    return colors


def remap_pil_image(
    img: Image.Image,
    palette: List[Color],
    use_palette_alpha: bool = False,
    keep_transparency: bool = False,
    quiet: bool = False,
) -> Image.Image:
    """Remap a PIL Image to the nearest color in `palette`. Returns a new RGBA Image."""
    if not palette:
        raise ValueError("Palette must contain at least one color")

    if not quiet:
        print(f"Using palette with {len(palette)} colors:")
        for i, c in enumerate(palette, 1):
            print(f"  {i:2d}) {c}")

    has_alpha = img.mode in ("RGBA", "LA", "P")
    if has_alpha:
        arr = np.array(img.convert("RGBA"), dtype=np.int32)
        pixels_rgb = arr[..., :3].reshape(-1, 3)
        orig_alpha = arr[..., 3]
    else:
        arr = np.array(img.convert("RGB"), dtype=np.int32)
        pixels_rgb = arr.reshape(-1, 3)
        orig_alpha = None

    h, w = arr.shape[:2]

    if not quiet:
        print(f"Image size: {w}\u00d7{h}  ({len(pixels_rgb):,} pixels)")

    palette_rgb = np.array([c.rgb_tuple() for c in palette], dtype=np.int32)
    palette_a = np.array([c.a for c in palette], dtype=np.uint8)

    dists = np.sum((pixels_rgb[:, None] - palette_rgb[None, :]) ** 2, axis=-1)
    closest_idx = np.argmin(dists, axis=1)

    result_rgb = palette_rgb[closest_idx]

    if orig_alpha is not None:
        orig_alpha_flat = orig_alpha.ravel()
        if keep_transparency:
            result_a = np.where(
                orig_alpha_flat == 0,
                0,
                palette_a[closest_idx] if use_palette_alpha else 255,
            ).astype(np.uint8)
        else:
            result_a = (palette_a[closest_idx] if use_palette_alpha else orig_alpha_flat).astype(np.uint8)
    else:
        result_a = np.full(len(pixels_rgb), 255, dtype=np.uint8)

    result = np.column_stack([result_rgb, result_a[:, None]]).reshape(h, w, 4).astype(np.uint8)
    return Image.fromarray(result, mode="RGBA")


def remap_image(
    input_path: Path,
    output_path: Path,
    palette: List[Color],
    use_palette_alpha: bool = False,
    keep_transparency: bool = False,
    quiet: bool = False,
) -> None:
    """Remap `input_path` image to the provided `palette` and save to `output_path`."""
    if not quiet:
        print(f"Using palette with {len(palette)} colors:")
        for i, c in enumerate(palette, 1):
            print(f"  {i:2d}) {c}")

    img = Image.open(input_path)
    if not quiet:
        print(f"Image size: {img.width}\u00d7{img.height}")

    remap_pil_image(img, palette, use_palette_alpha=use_palette_alpha, keep_transparency=keep_transparency, quiet=True).save(output_path)
