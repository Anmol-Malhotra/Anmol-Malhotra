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


def build_svg(img: Image.Image, cols: int, detail: float, color: bool, animate: bool = False,
              darken: float = 1.0, dot_color_override=None):
    """
    img: RGBA image (alpha=0 means "no subject here" -> no dot drawn, enables
    a transparent/removed background).
    darken: <1.0 makes dot colors darker/more saturated (fixes a washed-out look).
    animate: adds a CSS reveal so dots fade/scale in top row first, matching
    a top-to-bottom sweep over the subject.
    """
    w, h = img.size
    cell = w / cols
    rows = max(1, round(h / cell))
    small = img.resize((cols, rows), Image.LANCZOS)
    rgba = np.asarray(small.convert("RGBA")).astype(float)
    arr = rgba[:, :, :3]
    alpha_mask = rgba[:, :, 3] / 255.0
    gray = np.asarray(small.convert("L")).astype(float) / 255.0

    if color:
        mean = arr.mean(axis=2, keepdims=True)
        arr = np.clip(mean + (arr - mean) * 1.5, 0, 255)
        # darken + boost contrast so it isn't washed out
        arr = np.clip(arr * darken, 0, 255)
        arr = np.clip((arr - 127.5) * 1.15 + 127.5 * darken, 0, 255)

    gamma = 0.7
    weight = np.power(1 - gray, gamma)

    svg_w, svg_h = 600, 600 * rows / cols
    step_x, step_y = svg_w / cols, svg_h / rows
    min_r, max_r = step_x * 0.10, step_x * 0.58

    style = ""
    if animate:
        style = """<style>
circle{animation:dotIn 0.5s ease-out both;}
@keyframes dotIn{
  0%{opacity:0; transform:scale(0);}
  100%{opacity:1; transform:scale(1);}
}
</style>"""

    parts = [f'<svg viewBox="0 0 {svg_w:.1f} {svg_h:.1f}" xmlns="http://www.w3.org/2000/svg">', style]
    total_delay_window = 1.6  # seconds, spread across full height
    for y in range(rows):
        for x in range(cols):
            if alpha_mask[y, x] < 0.35:
                continue  # background removed -- no dot here
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
            attrs = f'cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.2f}" fill="{fill}"'
            if animate:
                delay = (y / rows) * total_delay_window
                attrs += f' style="transform-origin:{cx:.1f}px {cy:.1f}px; animation-delay:{delay:.3f}s"'
            parts.append(f'<circle {attrs}/>')
    parts.append("</svg>")
    return "\n".join(parts)


def remove_background(img: Image.Image) -> Image.Image:
    """Cut the subject out using GrabCut so background dots aren't drawn."""
    import cv2
    arr = np.array(img.convert("RGB"))[:, :, ::-1].copy()  # RGB -> BGR for cv2
    h, w = arr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    rect = (int(w * 0.06), int(h * 0.02), int(w * 0.90), int(h * 0.97))
    cv2.grabCut(arr, mask, rect, bgd, fgd, 10, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    alpha = cv2.GaussianBlur((mask2 * 255).astype("uint8"), (5, 5), 0)
    bgra = cv2.cvtColor(arr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha
    rgba = bgra[:, :, [2, 1, 0, 3]]  # BGRA -> RGBA
    return Image.fromarray(rgba, "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out", default="portrait")
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--equalize", action="store_true")
    ap.add_argument("--detail", type=float, default=0.5)
    ap.add_argument("--color", action="store_true")
    ap.add_argument("--remove-bg", action="store_true", help="cut out the subject with GrabCut")
    ap.add_argument("--darken", type=float, default=1.0, help="<1.0 darkens dot colors")
    ap.add_argument("--animate", action="store_true", help="add a top-to-bottom reveal animation")
    args = ap.parse_args()

    img = Image.open(args.input).convert("RGB")
    if args.equalize:
        img = ImageOps.equalize(img)
    img = img.convert("RGBA")
    if args.remove_bg:
        img = remove_background(img)

    dark_svg = build_svg(img, args.cols, args.detail, args.color, args.animate, args.darken)
    with open(f"{args.out}-dark.svg", "w") as f:
        f.write(dark_svg)

    light_svg = build_svg(img, args.cols, args.detail, args.color, args.animate, args.darken)
    with open(f"{args.out}-light.svg", "w") as f:
        f.write(light_svg)

    print(f"wrote {args.out}-dark.svg and {args.out}-light.svg")


if __name__ == "__main__":
    main()
