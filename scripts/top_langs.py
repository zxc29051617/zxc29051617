#!/usr/bin/env python3
"""Render a purple "Most Used Languages" SVG card from the owner's public repos.

Runs daily in .github/workflows/profile-assets.yml; the card is pushed to the
`output` branch together with the contribution snake.

Usage: python3 scripts/top_langs.py <output.svg>
Env:   GH_USER       GitHub login (default: zxc29051617)
       GITHUB_TOKEN  optional, raises the API rate limit
"""
import json
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

USER = os.environ.get("GH_USER", "zxc29051617")
TOKEN = os.environ.get("GITHUB_TOKEN")
TOP_N = 6

# Notebook outputs, markup, build glue and vendored course scaffolding
# (e.g. Pintos' Perl test scripts) inflate byte counts without reflecting
# the code actually written, so they are left out of the card.
EXCLUDE = {
    "Jupyter Notebook", "HTML", "CSS", "Shell", "PowerShell", "Batchfile",
    "Makefile", "CMake", "Dockerfile", "Linker Script", "Perl", "Raku", "Assembly",
}

BG, BORDER, TITLE, TEXT = "#1e1b4b", "#4c1d95", "#a78bfa", "#ddd6fe"
SWATCHES = ["#a78bfa", "#f0abfc", "#818cf8", "#c4b5fd", "#e879f9", "#ddd6fe"]
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif"


def api(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-top-langs",
    })
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def collect():
    totals = {}
    page = 1
    while True:
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        if not repos:
            break
        for repo in repos:
            if repo["fork"] or repo["name"].lower() == USER.lower():
                continue
            for lang, size in api(repo["languages_url"]).items():
                if lang not in EXCLUDE:
                    totals[lang] = totals.get(lang, 0) + size
        page += 1
    return totals


def render(totals):
    grand = sum(totals.values()) or 1
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]
    width, height = 495, 195
    bar_x, bar_y, bar_w, bar_h = 25, 62, 445, 10

    segments, x = [], float(bar_x)
    for i, (_, size) in enumerate(top):
        w = bar_w * size / grand
        segments.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{w:.2f}" height="{bar_h}" fill="{SWATCHES[i]}"/>')
        x += w

    legend = []
    for i, (lang, size) in enumerate(top):
        col, row = i % 2, i // 2
        lx, ly = 30 + col * 225, 102 + row * 28
        pct = 100 * size / grand
        legend.append(
            f'<g class="item" style="animation-delay:{150 + i * 120}ms">'
            f'<circle cx="{lx}" cy="{ly - 4}" r="5" fill="{SWATCHES[i]}"/>'
            f'<text x="{lx + 14}" y="{ly}" class="lang">{escape(lang)}</text>'
            f'<text x="{lx + 195}" y="{ly}" class="pct" text-anchor="end">{pct:.1f}%</text>'
            f'</g>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Most used languages">
  <title>Most used languages</title>
  <style>
    .title {{ font: 600 18px {FONT}; fill: {TITLE}; }}
    .lang  {{ font: 400 13px {FONT}; fill: {TEXT}; }}
    .pct   {{ font: 600 13px {FONT}; fill: {TITLE}; }}
    .item  {{ opacity: 0; animation: fade .5s ease-out forwards; }}
    .bar   {{ transform-origin: {bar_x}px 0; animation: grow .9s ease-out forwards; transform: scaleX(0); }}
    @keyframes fade {{ to {{ opacity: 1; }} }}
    @keyframes grow {{ to {{ transform: scaleX(1); }} }}
  </style>
  <defs><clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="5"/></clipPath></defs>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
  <text x="25" y="38" class="title">✦ Most Used Languages</text>
  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="5" fill="#2e1065"/>
  <g clip-path="url(#bar)"><g class="bar">{''.join(segments)}</g></g>
  {''.join(legend)}
</svg>
"""


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "top-langs.svg")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(collect()), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
