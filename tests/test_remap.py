from pathlib import Path

import numpy as np
from palette_remap import parse_palette, remap_image
from PIL import Image


def test_remap_simple(tmp_path: Path):
    # Create a tiny 2x1 image: red, green
    img = Image.new("RGBA", (2, 1))
    img.putpixel((0, 0), (255, 0, 0, 255))
    img.putpixel((1, 0), (0, 255, 0, 255))

    inp = tmp_path / "in.png"
    out = tmp_path / "out.png"
    img.save(inp)

    palette = parse_palette("#ff0000 #00ff00")
    remap_image(inp, out, palette, quiet=True)

    res = np.array(Image.open(out).convert("RGBA"))
    # Check first pixel is red, second is green
    assert tuple(res[0, 0])[:3] == (255, 0, 0)
    assert tuple(res[0, 1])[:3] == (0, 255, 0)
