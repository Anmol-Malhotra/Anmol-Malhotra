#!/usr/bin/env python3
"""
radar.py -- draw a self-rated skill radar chart as SVG (dark + light variants).

Usage:
    python radar.py skills.json -o assets/radar

skills.json format:
    { "Python": 80, "Web Dev": 75, "C": 70, "SQL": 65, "Git": 75, "Computer Vision": 60 }

Edit the numbers (0-100) any time and re-run to update the chart.
"""
import argparse
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def draw(skills: dict, theme: str, out_path: str):
    labels = list(skills.keys())
    values = list(skills.values())
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    if theme == "dark":
        bg, fg, grid, line, fill = "none", "#c9d1d9", "#30363d", "#39D353", "#39D35355"
    else:
        bg, fg, grid, line, fill = "none", "#24292f", "#d0d7de", "#1f7a3f", "#1f7a3f33"

    fig = plt.figure(figsize=(5, 5), facecolor=bg)
    ax = plt.subplot(111, polar=True, facecolor=bg)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color=fg, size=12, fontfamily="monospace")
    ax.set_rlabel_position(0)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], color=grid, size=7)
    ax.set_ylim(0, 100)

    ax.spines["polar"].set_color(grid)
    ax.grid(color=grid, linewidth=0.7)

    ax.plot(angles, values, color=line, linewidth=2)
    ax.fill(angles, values, color=fill)

    plt.tight_layout()
    plt.savefig(out_path, format="svg", transparent=True, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skills_json")
    ap.add_argument("-o", "--out", default="radar")
    args = ap.parse_args()

    with open(args.skills_json) as f:
        skills = json.load(f)

    draw(skills, "dark", f"{args.out}-dark.svg")
    draw(skills, "light", f"{args.out}-light.svg")
    print(f"wrote {args.out}-dark.svg and {args.out}-light.svg")


if __name__ == "__main__":
    main()
