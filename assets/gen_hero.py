#!/usr/bin/env python3
"""Generate the animated README hero banner.

GitHub cannot run WebGL, so the portfolio's Three.js particle field
(src/three/Particles.tsx) is re-created as an animated SVG: the same warm
palette, the same slow flow-field drift, and the glowing pedestal disc from
AvatarHead.tsx. CSS keyframes inside an <img>-loaded SVG do animate; scripts
and external resources do not, so everything here is self-contained.
"""

import math
import random

W, H = 1200, 340

# Palette lifted from src/three/Particles.tsx, with the same weighting.
PARTICLES = [
    ("#ff7a45", 0.45),
    ("#e6403f", 0.33),
    ("#ffb070", 0.12),
    ("#ff5a3c", 0.07),
    ("#ffd9a0", 0.03),
]

THEMES = {
    "dark": dict(
        bg="#0a0b0f", bg2="#0e1016",
        title="#ffffff", subtitle="#b9bdc8", muted="#9499a6",
        accent="#ff7a45", accent2="#e6403f",
        glow=0.20, particle_scale=1.0, particle_alpha=0.85,
        rule="rgba(255,255,255,0.09)",
    ),
    "light": dict(
        bg="#f5f4f1", bg2="#ecebe6",
        title="#181a1f", subtitle="#3b3f46", muted="#595f68",
        accent="#ec5c2a", accent2="#d6322f",
        # the shader deepens the points and lifts opacity on a light bg
        glow=0.26, particle_scale=0.82, particle_alpha=1.0,
        rule="rgba(18,20,28,0.12)",
    ),
}

FONT = ("-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,'Helvetica Neue',"
        "Arial,sans-serif")


def shade(hex_color: str, factor: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, round(c * factor)) for c in (r, g, b))


def pick(rng: random.Random) -> str:
    r = rng.random()
    acc = 0.0
    for colour, weight in PARTICLES:
        acc += weight
        if r < acc:
            return colour
    return PARTICLES[0][0]


def build(theme_name: str) -> str:
    t = THEMES[theme_name]
    # Fixed seed: both themes get the identical field, so toggling GitHub's
    # theme swaps colours without the stars jumping around.
    rng = random.Random(20101999)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="Zakaria Makhkhas — Software Engineer and AI Trainer">',
        "<style>",
        # Eight drift classes stand in for the shader's layered sin/cos flow.
        # Per-particle animation-delay (inline) desynchronises them.
        ]

    for i in range(8):
        ang = i / 8 * math.tau
        dx = round(math.cos(ang) * 16, 1)
        dy = round(math.sin(ang) * 11, 1)
        dur = 7 + i * 1.7
        out.append(
            f"@keyframes f{i}{{from{{transform:translate(0,0)}}"
            f"to{{transform:translate({dx}px,{dy}px)}}}}"
        )
        out.append(
            f".p{i}{{animation:f{i} {dur}s ease-in-out infinite alternate,"
            f"tw {dur / 2:.1f}s ease-in-out infinite alternate}}"
        )

    out += [
        "@keyframes tw{from{opacity:.25}to{opacity:1}}",
        # the pedestal disc's travelling rim ring. SVG defaults transform-box to
        # view-box, which would resolve `center` to the whole canvas — pin it to
        # each element's own box instead.
        "@keyframes ring{0%{transform:scale(.5);opacity:.5}"
        "100%{transform:scale(1.3);opacity:0}}",
        ".ring{animation:ring 4.4s ease-out infinite;"
        "transform-box:fill-box;transform-origin:center}",
        "@keyframes breathe{from{opacity:.5;transform:scale(.94)}"
        "to{opacity:1;transform:scale(1)}}",
        ".core{animation:breathe 3.6s ease-in-out infinite alternate;"
        "transform-box:fill-box;transform-origin:center}",
        "@keyframes rise{from{opacity:0;transform:translateY(10px)}"
        "to{opacity:1;transform:translateY(0)}}",
        ".in1{animation:rise .9s cubic-bezier(.22,1,.36,1) both}",
        ".in2{animation:rise .9s cubic-bezier(.22,1,.36,1) .18s both}",
        ".in3{animation:rise .9s cubic-bezier(.22,1,.36,1) .34s both}",
        "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}",
        ".rule{animation:grow 1.1s cubic-bezier(.22,1,.36,1) .5s both;"
        "transform-origin:left center}",
        # Respect the reader's motion preference, as the site does.
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}",
        "</style>",
        "<defs>",
        f'<radialGradient id="bg" cx="50%" cy="42%" r="78%">'
        f'<stop offset="0" stop-color="{t["bg2"]}"/>'
        f'<stop offset="1" stop-color="{t["bg"]}"/></radialGradient>',
        f'<radialGradient id="glow" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{t["accent"]}" stop-opacity="{t["glow"]}"/>'
        f'<stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/>'
        f"</radialGradient>",
        f'<radialGradient id="disc" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="#ffd9a0" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="{t["accent2"]}" stop-opacity="0"/>'
        f"</radialGradient>",
        f'<linearGradient id="ink" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["accent"]}"/>'
        f'<stop offset="1" stop-color="{t["accent2"]}"/></linearGradient>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>',
        # one warm bloom, roughly where the avatar stands on the real site
        f'<ellipse cx="915" cy="170" rx="340" ry="235" fill="url(#glow)"/>',
    ]

    # ---- the particle field -------------------------------------------------
    # The copy occupies the left third, so weight density to the right and keep
    # whatever lands behind the text faint — the field should frame the name,
    # not compete with it.
    TEXT_BOX = (40, 660, 80, 300)
    out.append('<g fill="none">')
    for _ in range(170):
        x = round(W * rng.random() ** 0.55, 1)
        y = round(rng.random() * H, 1)
        r = round(0.8 + rng.random() ** 2.4 * 2.8, 2)
        colour = pick(rng)
        if t["particle_scale"] != 1.0:
            colour = shade(colour, t["particle_scale"])
        cls = rng.randrange(8)
        delay = round(-rng.random() * 14, 2)
        x0, x1, y0, y1 = TEXT_BOX
        behind_text = x0 < x < x1 and y0 < y < y1
        alpha = t["particle_alpha"] * (0.22 if behind_text else 0.9)
        out.append(
            f'<circle class="p{cls}" cx="{x}" cy="{y}" r="{r}" fill="{colour}" '
            f'opacity="{alpha:.2f}" style="animation-delay:{delay}s"/>'
        )
    out.append("</g>")

    # ---- the flowing pedestal disc -----------------------------------------
    out.append('<g transform="translate(915 170)">')
    out.append('<circle class="core" cx="0" cy="0" r="58" fill="url(#disc)"/>')
    for delay in (0, 1.1, 2.2, 3.3):
        out.append(
            f'<circle class="ring" cx="0" cy="0" r="74" fill="none" '
            f'stroke="url(#ink)" stroke-width="1.4" stroke-opacity=".8" '
            f'style="animation-delay:{delay}s"/>'
        )
    out.append("</g>")

    # ---- the copy -----------------------------------------------------------
    out += [
        f'<g font-family="{FONT}">',
        f'<text class="in1" x="64" y="126" fill="{t["muted"]}" font-size="19" '
        f'font-weight="600" letter-spacing="3.4">HI, I\'M</text>',
        f'<text class="in2" x="62" y="192" fill="{t["title"]}" font-size="56" '
        f'font-weight="800" letter-spacing="-1.6">Zakaria Makhkhas</text>',
        f'<rect class="rule" x="64" y="215" width="132" height="3" rx="1.5" '
        f'fill="url(#ink)"/>',
        f'<text class="in3" x="64" y="256" fill="{t["subtitle"]}" font-size="23" '
        f'font-weight="600">Software Engineer &amp; AI Trainer</text>',
        f'<text class="in3" x="64" y="288" fill="{t["muted"]}" font-size="16">'
        f'React · TypeScript · Python · Machine Learning — Casablanca, Morocco</text>',
        "</g>",
        "</svg>",
    ]
    return "".join(out)


if __name__ == "__main__":
    import pathlib
    import sys

    dest = pathlib.Path(sys.argv[1])
    dest.mkdir(parents=True, exist_ok=True)
    for name in THEMES:
        path = dest / f"hero-{name}.svg"
        path.write_text(build(name), encoding="utf-8")
        print(f"{path}  {path.stat().st_size / 1024:.1f} KB")
