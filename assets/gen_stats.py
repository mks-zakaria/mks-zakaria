#!/usr/bin/env python3
"""Generate the README's GitHub stats panel.

The usual third-party stat cards (github-readme-stats and friends) render as
broken images whenever their public instance is rate-limited, and they only
approximate the portfolio palette. This draws the same information as a
self-hosted SVG in the site's exact colours.

Refresh the numbers with:

    gh api graphql -f query='{ user(login:"mks-zakaria") { ... } }' > gh.json
    python3 assets/gen_stats.py assets gh.json "August 2026"

Usage without gh.json falls back to the committed FIGURES below.
"""

import json
import pathlib
import sys

W, H = 1200, 232

FIGURES = {
    "repos": 99,
    "prs": 1448,
    "followers": 26,
    "contributions": 5211,  # public + private, trailing 12 months
    "as_of": "August 2026",
}

# name, share of bytes, GitHub's own language colour
LANGUAGES = [
    ("Python", 18.8, "#3572A5"),
    ("Jupyter Notebook", 18.6, "#DA5B0B"),
    ("TypeScript", 15.3, "#3178c6"),
    ("HTML", 12.7, "#e34c26"),
    ("TeX", 10.9, "#3D6117"),
    ("JavaScript", 5.0, "#f1e05a"),
    ("MDX", 4.4, "#fcb32c"),
    ("Swift", 3.6, "#F05138"),
    ("C", 2.5, "#8f8f8f"),
]

THEMES = {
    "dark": dict(
        bg="#0a0b0f", card="#12141b", border="rgba(255,255,255,0.09)",
        title="#ffffff", muted="#9499a6", accent="#ff7a45", track="#1c1f28",
    ),
    "light": dict(
        bg="#f5f4f1", card="#ffffff", border="rgba(18,20,28,0.12)",
        title="#181a1f", muted="#595f68", accent="#ec5c2a", track="#e4e2dc",
    ),
}

FONT = ("-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,'Helvetica Neue',"
        "Arial,sans-serif")


def build(theme_name: str, fig: dict, langs: list) -> str:
    t = THEMES[theme_name]
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="GitHub activity">',
        "<style>",
        "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}",
        ".bar{animation:grow 1.2s cubic-bezier(.22,1,.36,1) both;"
        "transform-box:fill-box;transform-origin:left center}",
        "@keyframes rise{from{opacity:0;transform:translateY(8px)}"
        "to{opacity:1;transform:translateY(0)}}",
        ".fade{animation:rise .7s cubic-bezier(.22,1,.36,1) both}",
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}",
        "</style>",
        f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
        f'<g font-family="{FONT}">',
    ]

    # ---- left card: the headline numbers ------------------------------------
    o.append(f'<rect x="0" y="0" width="470" height="{H}" rx="16" '
             f'fill="{t["card"]}" stroke="{t["border"]}"/>')
    o.append(f'<text x="34" y="46" fill="{t["muted"]}" font-size="13" '
             f'font-weight="700" letter-spacing="2.2">AT A GLANCE</text>')

    cells = [
        (fig["contributions"], "contributions, last 12 months"),
        (fig["prs"], "pull requests opened"),
        (fig["repos"], "repositories"),
        (fig["followers"], "followers"),
    ]
    for i, (value, label) in enumerate(cells):
        x = 34 + (i % 2) * 218
        y = 108 + (i // 2) * 74
        o.append(f'<g class="fade" style="animation-delay:{0.1 + i * 0.09:.2f}s">')
        o.append(f'<text x="{x}" y="{y}" fill="{t["accent"]}" font-size="34" '
                 f'font-weight="800" letter-spacing="-1">{value:,}</text>')
        o.append(f'<text x="{x}" y="{y + 22}" fill="{t["muted"]}" '
                 f'font-size="12.5">{label}</text>')
        o.append("</g>")

    # ---- right card: the language mix ---------------------------------------
    o.append(f'<rect x="490" y="0" width="710" height="{H}" rx="16" '
             f'fill="{t["card"]}" stroke="{t["border"]}"/>')
    o.append(f'<text x="524" y="46" fill="{t["muted"]}" font-size="13" '
             f'font-weight="700" letter-spacing="2.2">'
             f'MOST USED LANGUAGES</text>')

    total = sum(share for _, share, _ in langs)
    bar_x, bar_w = 524, 642
    o.append(f'<rect x="{bar_x}" y="70" width="{bar_w}" height="11" rx="5.5" '
             f'fill="{t["track"]}"/>')
    # One clip keeps the stacked segments inside the rounded track.
    o.append(f'<clipPath id="clip"><rect x="{bar_x}" y="70" width="{bar_w}" '
             f'height="11" rx="5.5"/></clipPath>')
    o.append('<g clip-path="url(#clip)">')
    cursor = float(bar_x)
    for i, (_, share, colour) in enumerate(langs):
        seg = bar_w * share / total
        o.append(f'<rect class="bar" x="{cursor:.1f}" y="70" '
                 f'width="{seg:.1f}" height="11" fill="{colour}" '
                 f'style="animation-delay:{0.15 + i * 0.06:.2f}s"/>')
        cursor += seg
    o.append("</g>")

    # legend — three columns of three
    for i, (name, share, colour) in enumerate(langs):
        col, row = i // 3, i % 3
        x = 524 + col * 218
        y = 122 + row * 34
        o.append(f'<g class="fade" style="animation-delay:{0.2 + i * 0.05:.2f}s">')
        o.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{colour}"/>')
        o.append(f'<text x="{x + 18}" y="{y}" fill="{t["title"]}" '
                 f'font-size="13.5" font-weight="600">{name}</text>')
        o.append(f'<text x="{x + 186}" y="{y}" fill="{t["muted"]}" '
                 f'font-size="13" text-anchor="end">{share:.1f}%</text>')
        o.append("</g>")

    o.append(f'<text x="1166" y="{H - 14}" fill="{t["muted"]}" font-size="11" '
             f'text-anchor="end" opacity=".8">as of {fig["as_of"]}</text>')
    o += ["</g>", "</svg>"]
    return "".join(o)


def from_api(path: pathlib.Path, as_of: str):
    """Recompute FIGURES/LANGUAGES from a saved `gh api graphql` response."""
    import collections

    user = json.loads(path.read_text())["data"]["user"]
    repos = user["repositories"]
    sizes, colours = collections.Counter(), {}
    for node in repos["nodes"]:
        for edge in node["languages"]["edges"]:
            sizes[edge["node"]["name"]] += edge["size"]
            colours[edge["node"]["name"]] = edge["node"]["color"]
    total = sum(sizes.values())
    contrib = user["contributionsCollection"]
    fig = {
        "repos": repos["totalCount"],
        "prs": user["pullRequests"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "contributions": (contrib["totalCommitContributions"]
                          + contrib["restrictedContributionsCount"]),
        "as_of": as_of,
    }
    langs = [(name, size / total * 100, colours[name] or "#8f8f8f")
             for name, size in sizes.most_common(9)]
    return fig, langs


if __name__ == "__main__":
    dest = pathlib.Path(sys.argv[1])
    dest.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 2:
        fig, langs = from_api(pathlib.Path(sys.argv[2]),
                              sys.argv[3] if len(sys.argv) > 3
                              else FIGURES["as_of"])
    else:
        fig, langs = FIGURES, LANGUAGES
    for name in THEMES:
        path = dest / f"stats-{name}.svg"
        path.write_text(build(name, fig, langs), encoding="utf-8")
        print(f"{path}  {path.stat().st_size / 1024:.1f} KB")
