#!/usr/bin/env python3
"""
cards.py -- self-hosted GitHub stats + top-languages SVG cards.

Why self-hosted: shared public instances of github-readme-stats /
streak-stats go down or get rate-limited/paused (their owner's problem,
not yours) and silently break every profile embedding them. This script
pulls your own public data straight from the GitHub API and renders
static SVGs you own, regenerated on a schedule by GitHub Actions.

Usage:
    python cards.py <username> -o assets/card-stats --theme dark
    python cards.py <username> -o assets/card-stats --theme light

Auth: pass a token via GITHUB_TOKEN env var for a much higher API rate
limit (GitHub Actions sets this automatically -- see workflow).
"""
import argparse
import os
import sys
import urllib.request
import json
from collections import defaultdict

API = "https://api.github.com"

THEMES = {
    "dark":  {"bg": "#0d1117", "border": "#30363d", "text": "#c9d1d9", "title": "#58a6ff", "accent": "#39D353"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#24292f", "title": "#0969da", "accent": "#1f7a3f"},
}

LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "C": "#555555", "C++": "#f34b7d", "HTML": "#e34c26", "CSS": "#563d7c",
    "Java": "#b07219", "Shell": "#89e051", "Jupyter Notebook": "#DA5B0B",
    "PHP": "#4F5D95", "Go": "#00ADD8", "Rust": "#dea584",
}


def api_get(path, token=None):
    req = urllib.request.Request(API + path)
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def gather(username, token):
    user = api_get(f"/users/{username}", token)
    repos = []
    page = 1
    while True:
        batch = api_get(f"/users/{username}/repos?per_page=100&page={page}", token)
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    stars = sum(r.get("stargazers_count", 0) for r in repos)
    forks = sum(r.get("forks_count", 0) for r in repos)
    lang_bytes = defaultdict(int)
    for r in repos:
        if r.get("fork"):
            continue
        try:
            langs = api_get(r["languages_url"], token)
            for lang, n in langs.items():
                lang_bytes[lang] += n
        except Exception:
            continue

    return {
        "public_repos": user.get("public_repos", len(repos)),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "stars": stars,
        "forks": forks,
        "languages": dict(sorted(lang_bytes.items(), key=lambda kv: -kv[1])[:6]),
    }


def stats_card(data, theme_name, username):
    t = THEMES[theme_name]
    w, h = 460, 190
    rows = [
        ("Public Repos", data["public_repos"]),
        ("Total Stars", data["stars"]),
        ("Total Forks", data["forks"]),
        ("Followers", data["followers"]),
    ]
    parts = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<rect x="0.5" y="0.5" rx="8" width="{w-1}" height="{h-1}" fill="{t["bg"]}" stroke="{t["border"]}"/>')
    parts.append(f'<text x="25" y="35" font-family="Segoe UI, sans-serif" font-size="18" font-weight="600" fill="{t["title"]}">{username}\'s GitHub Stats</text>')
    y = 70
    for label, value in rows:
        parts.append(f'<circle cx="30" cy="{y-5}" r="5" fill="{t["accent"]}"/>')
        parts.append(f'<text x="45" y="{y}" font-family="Segoe UI, sans-serif" font-size="14" fill="{t["text"]}">{label}:</text>')
        parts.append(f'<text x="220" y="{y}" font-family="Segoe UI, sans-serif" font-size="14" font-weight="600" fill="{t["text"]}">{value}</text>')
        y += 30
    parts.append("</svg>")
    return "\n".join(parts)


def langs_card(data, theme_name, username):
    t = THEMES[theme_name]
    w, h = 460, 200
    langs = data["languages"] or {"N/A": 1}
    total = sum(langs.values()) or 1
    parts = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<rect x="0.5" y="0.5" rx="8" width="{w-1}" height="{h-1}" fill="{t["bg"]}" stroke="{t["border"]}"/>')
    parts.append(f'<text x="25" y="35" font-family="Segoe UI, sans-serif" font-size="18" font-weight="600" fill="{t["title"]}">Most Used Languages</text>')
    bar_x, bar_w, bar_y = 25, w - 50, 55
    x = bar_x
    for lang, n in langs.items():
        seg = max(2, (n / total) * bar_w)
        color = LANG_COLORS.get(lang, "#8a8a8a")
        parts.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{seg:.1f}" height="12" rx="3" fill="{color}"/>')
        x += seg
    y = 100
    col_x = [25, 240]
    for i, (lang, n) in enumerate(langs.items()):
        pct = 100 * n / total
        cx = col_x[i % 2]
        cy = y + (i // 2) * 26
        color = LANG_COLORS.get(lang, "#8a8a8a")
        parts.append(f'<circle cx="{cx}" cy="{cy-4}" r="5" fill="{color}"/>')
        parts.append(f'<text x="{cx+14}" y="{cy}" font-family="Segoe UI, sans-serif" font-size="13" fill="{t["text"]}">{lang} {pct:.1f}%</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("username")
    ap.add_argument("-o", "--out", default="assets/card")
    args = ap.parse_args()
    token = os.environ.get("GITHUB_TOKEN")

    try:
        data = gather(args.username, token)
    except Exception as e:
        print(f"warning: could not fetch live data ({e}); writing placeholder cards", file=sys.stderr)
        data = {"public_repos": "-", "stars": "-", "forks": "-", "followers": "-", "languages": {}}

    for theme in ("dark", "light"):
        with open(f"{args.out}-stats-{theme}.svg", "w") as f:
            f.write(stats_card(data, theme, args.username))
        with open(f"{args.out}-langs-{theme}.svg", "w") as f:
            f.write(langs_card(data, theme, args.username))
    print("wrote stats + language cards for both themes")


if __name__ == "__main__":
    main()
