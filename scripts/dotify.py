#!/usr/bin/env python3
"""
dotify.py -- convert a photo into a dot-matrix SVG portrait.

Usage:
    python dotify.py input.png -o assets/portrait --cols 100 --equalize --detail 0.5 --color

Produces:
    assets/portrait-dark.svg   (dots colored, transparent bg -- for dark GitHub theme)
    assets/portrait-light.svg  (dots colored, transparent bg -- for light GitHub theme)
"""
import argparse
from PIL import Image, ImageOps
import numpy as np


def build_svg(img: Image.Image, cols: int, detail: float, color: bool, dot_color_override=None):
    w, h = img.size
    cell = w / cols
    rows = max(1, round(h / cell))
    small = img.resize((cols, rows), Image.LANCZOS)
    arr = np.asarray(small.convert("RGB")).astype(float)
    gray = np.asarray(small.convert("L")).astype(float) / 255.0

    # boost saturation a touch for punchier dot colors
    if color:
        mean = arr.mean(axis=2, keepdims=True)
        arr = np.clip(mean + (arr - mean) * 1.35, 0, 255)

    # gamma curve so mid/bright pixels still get a visible dot (halftone feel)
    gamma = 0.75
    weight = np.power(1 - gray, gamma)

    svg_w, svg_h = 600, 600 * rows / cols
    step_x, step_y = svg_w / cols, svg_h / rows
    min_r, max_r = step_x * 0.10, step_x * 0.58

    parts = [f'<svg viewBox="0 0 {svg_w:.1f} {svg_h:.1f}" xmlns="http://www.w3.org/2000/svg">']
    for y in range(rows):
        for x in range(cols):
            radius = min_r + weight[y, x] * (max_r - min_r) * (0.6 + detail * 0.8)
            if radius < min_r * 0.8:
                continue
            cx, cy = (x + 0.5) * step_x, (y + 0.5) * step_y
            if dot_color_override:
                fill = dot_color_override
            elif color:
                r, g, b = arr[y, x]
                fill = f"rgb({int(r)},{int(g)},{int(b)})"
            else:
                fill = "currentColor"
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.2f}" fill="{fill}"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out", default="portrait")
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--equalize", action="store_true")
    ap.add_argument("--detail", type=float, default=0.5)
    ap.add_argument("--color", action="store_true")
    args = ap.parse_args()

    img = Image.open(args.input).convert("RGB")
    if args.equalize:
        img = ImageOps.equalize(img)

    dark_svg = build_svg(img, args.cols, args.detail, args.color)
    with open(f"{args.out}-dark.svg", "w") as f:
        f.write(dark_svg)

    light_svg = build_svg(img, args.cols, args.detail, args.color)
    with open(f"{args.out}-light.svg", "w") as f:
        f.write(light_svg)

    print(f"wrote {args.out}-dark.svg and {args.out}-light.svg")


if __name__ == "__main__":
    main()
