#!/usr/bin/env python3
"""CLI entrypoint for palette-remap."""

import argparse
import sys
from pathlib import Path
from typing import List

from .core import load_palette_from_file, parse_palette, remap_image


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Remap image colors to the closest colors in a palette",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input", type=Path, help="input image")
    parser.add_argument("output", type=Path, help="output image (use .png to preserve transparency)")

    parser.add_argument("--palette", type=parse_palette, help="palette colors (space or comma separated)")
    parser.add_argument("--palette-file", type=Path, metavar="FILE", help="load palette from .hex/.txt file")
    parser.add_argument("--use-palette-alpha", action="store_true", help="use alpha from the matched palette color")
    parser.add_argument("--keep-transparency", action="store_true", help="preserve original fully-transparent pixels (alpha=0 stays 0)")
    parser.add_argument("--quiet", "-q", action="store_true", help="suppress output messages")

    args = parser.parse_args(argv)

    palette = []
    if args.palette:
        palette.extend(args.palette)
    if args.palette_file:
        try:
            palette.extend(load_palette_from_file(args.palette_file))
        except Exception as e:
            print(f"Error loading palette file: {e}", file=sys.stderr)
            return 1

    if not palette:
        parser.error("You must provide at least one of --palette or --palette-file")

    try:
        remap_image(
            args.input,
            args.output,
            palette,
            use_palette_alpha=args.use_palette_alpha,
            keep_transparency=args.keep_transparency,
            quiet=args.quiet,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
