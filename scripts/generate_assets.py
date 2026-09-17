#!/usr/bin/env python3
"""Generates the animated SVGs used by the profile README.

GitHub strips JavaScript and CSS from READMEs, but animated SVG images still
play, so every "3D" effect here is projected in Python and baked into SMIL/CSS
keyframes. Stdlib only, so the scheduled GitHub Action needs no installs.

    python scripts/generate_assets.py
"""

import html
import json
import math
import os
import random
import re
import urllib.request

GITHUB_USER = "anmolgupta01"
LEETCODE_USER = "anmolgupta01"
LEETCODE_FALLBACK = {"all": 387, "medium": 209, "hard": 43}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

BG = "#07021a"
CYAN = "#00f0ff"
MAGENTA = "#ff2bd6"
VIOLET = "#8b5cf6"
YELLOW = "#f9f871"
INK = "#ece9ff"
DIM = "#8f8ab8"

DISPLAY = "'Segoe UI Black','Arial Black','Helvetica Neue',Arial,sans-serif"
SANS = "'Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','Cascadia Code',Consolas,'SF Mono',Menlo,'DejaVu Sans Mono',monospace"


# --------------------------------------------------------------------------- helpers

def n(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def esc(s):
    return html.escape(str(s), quote=True)


def mix(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def glow(fid, std):
    # userSpaceOnUse so zero-height shapes (horizontal lines) still render
    return (f'<filter id="{fid}" filterUnits="userSpaceOnUse" x="-500" y="-500" width="3000" height="3000">'
            f'<feGaussianBlur stdDeviation="{std}" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


BASE_CSS = (f"text{{font-family:{DISPLAY}}}.mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}"
            ".tw{animation:tw 3s ease-in-out infinite}"
            "@keyframes tw{0%,100%{opacity:.15}50%{opacity:.95}}"
            ".blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
            ".float{animation:float 5s ease-in-out infinite}"
            "@keyframes float{50%{transform:translateY(-9px)}}"
            ".shadow{transform-box:fill-box;transform-origin:center;animation:shadow 5s ease-in-out infinite}"
            "@keyframes shadow{50%{transform:scale(.82);opacity:.3}}")


def svg_doc(w, h, body, title, css="", defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f'<style>{BASE_CSS}{css}</style>'
            f'<defs>{glow("glow", 3)}{glow("glowL", 8)}'
            # pure blur for soft halos and shadows; glow re-draws the sharp source on top
            '<filter id="soft" filterUnits="userSpaceOnUse" x="-500" y="-500" width="3000" height="3000">'
            f'<feGaussianBlur stdDeviation="14"/></filter>{defs}</defs>{body}</svg>\n')


def write(name, content):
    path = os.path.join(ASSETS, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    print(f"  {name:<28} {len(content.encode()) / 1024:6.1f} KB")


def fetch(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0 profile-assets", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def stars(rng, w, h, count):
    out = []
    for _ in range(count):
        out.append(f'<circle class="tw" cx="{n(rng.uniform(0, w))}" cy="{n(rng.uniform(0, h))}" '
                   f'r="{rng.choice((.6, .8, 1, 1.2, 1.7))}" fill="{INK}" '
                   f'style="animation-delay:-{rng.uniform(0, 5):.2f}s;animation-duration:{rng.uniform(2.2, 5.5):.2f}s"/>')
    return "".join(out)


def floor_grid(uid, w, horizon, bottom, color, spacing=64, dur=1.3):
    """Synthwave floor: perspective-correct lines rushing toward the viewer."""
    depth = bottom - horizon
    vp = w / 2
    frames, lines, dz = 10, 20, .62
    ds = []
    for k in range(frames + 1):
        p = k / frames
        ys = (min(horizon + depth / (1 + (i - p) * dz), bottom + 30) for i in range(lines))
        ds.append("".join(f"M0 {n(y)}H{w}" for y in ys))
    reach = int(w / spacing) + 2
    verts = "".join(f"M{n(vp)} {horizon}L{n(vp + i * spacing * 2)} {bottom + depth}" for i in range(-reach, reach + 1))
    return (f'<clipPath id="{uid}c"><rect x="0" y="{horizon}" width="{w}" height="{depth}"/></clipPath>'
            f'<linearGradient id="{uid}g" x1="0" y1="{horizon}" x2="0" y2="{bottom}" gradientUnits="userSpaceOnUse">'
            '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".3" stop-color="#fff" stop-opacity=".5"/>'
            '<stop offset="1" stop-color="#fff"/></linearGradient>'
            f'<mask id="{uid}m" maskUnits="userSpaceOnUse" x="0" y="{horizon}" width="{w}" height="{depth}">'
            f'<rect x="0" y="{horizon}" width="{w}" height="{depth}" fill="url(#{uid}g)"/></mask>'
            f'<g clip-path="url(#{uid}c)" mask="url(#{uid}m)" stroke="{color}" stroke-width="1.3" fill="none">'
            f'<path d="{verts}" opacity=".75"/>'
            f'<path d="{ds[0]}"><animate attributeName="d" values="{";".join(ds)}" dur="{dur}s" repeatCount="indefinite"/></path>'
            '</g>')


def slab(x, y, w, h, depth, uid, accent, rx=16, fill_top="#1a0f45", fill_bottom="#0c0628"):
    """A rounded panel extruded down-right, with a rotating neon border."""
    layers = "".join(
        f'<rect x="{x + i}" y="{y + i}" width="{w}" height="{h}" rx="{rx}" fill="{mix("#030010", mix(accent, "#1a0b40", .8), 1 - i / depth)}"/>'
        for i in range(depth, 0, -1))
    return (f'<linearGradient id="{uid}f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{fill_top}"/>'
            f'<stop offset="1" stop-color="{fill_bottom}"/></linearGradient>'
            f'<linearGradient id="{uid}b" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{accent}"/><stop offset=".45" stop-color="{accent}" stop-opacity="0"/>'
            f'<stop offset=".7" stop-color="{MAGENTA if accent != MAGENTA else CYAN}" stop-opacity=".9"/>'
            f'<stop offset="1" stop-color="{accent}"/>'
            '<animateTransform attributeName="gradientTransform" type="rotate" values="0 .5 .5;360 .5 .5" dur="6s" repeatCount="indefinite"/>'
            '</linearGradient>'
            f'{layers}'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#{uid}f)" stroke="url(#{uid}b)" stroke-width="2.5"/>')


def text3d(x, y, s, size, depth, fill, anchor="start", spacing=2, extra=""):
    layers = "".join(
        f'<text x="{n(x + i * .9)}" y="{n(y + i * .9)}" font-size="{size}" letter-spacing="{spacing}" '
        f'text-anchor="{anchor}" fill="{mix("#12032e", "#7a1a8f", 1 - i / depth)}">{esc(s)}</text>'
        for i in range(depth, 0, -1))
    return (layers + f'<text x="{x}" y="{y}" font-size="{size}" letter-spacing="{spacing}" text-anchor="{anchor}" '
                     f'fill="{fill}" {extra}>{esc(s)}</text>')


def shimmer_gradient(gid, x1, x2):
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{n(x1)}" y1="0" x2="{n(x2)}" y2="0" spreadMethod="reflect">'
            f'<stop offset="0" stop-color="{CYAN}"/><stop offset=".45" stop-color="#ffffff"/><stop offset="1" stop-color="{MAGENTA}"/>'
            f'<animateTransform attributeName="gradientTransform" type="translate" values="0 0;{n(x2 - x1)} 0;0 0" dur="7s" repeatCount="indefinite"/>'
            '</linearGradient>')


# --------------------------------------------------------------------------- 3D pose

# Keyframe poses of a right-handed golf swing, metres. x: toward golfer's right
# (target is -x), y: up, z: toward the ball.
ADDRESS = dict(head=(0, 1.55, .3), lsh=(-.2, 1.35, .2), rsh=(.2, 1.33, .2), lel=(-.1, 1.1, .35), rel=(.1, 1.1, .33),
               lwr=(-.03, .85, .42), rwr=(.03, .86, .42), lhip=(-.15, .9, -.08), rhip=(.15, .9, -.08),
               lkn=(-.2, .45, .08), rkn=(.2, .45, .08), lank=(-.2, 0, 0), rank=(.2, 0, 0), club=(-.05, .02, .88))
TOP = dict(head=(.03, 1.55, .3), lsh=(.02, 1.36, .38), rsh=(0, 1.4, .02), lel=(.16, 1.55, .26), rel=(.28, 1.38, 0),
           lwr=(.3, 1.72, .12), rwr=(.32, 1.73, .1), lhip=(-.1, .9, .03), rhip=(.1, .9, -.19),
           lkn=(-.1, .45, .15), rkn=(.2, .46, .05), lank=(-.2, 0, 0), rank=(.2, 0, 0), club=(-.55, 1.78, -.25))
IMPACT = dict(head=(.02, 1.52, .28), lsh=(-.22, 1.34, .13), rsh=(.17, 1.3, .26), lel=(-.17, 1.08, .33), rel=(.05, 1.07, .36),
              lwr=(-.1, .86, .44), rwr=(-.06, .87, .43), lhip=(-.2, .9, -.15), rhip=(.08, .9, 0),
              lkn=(-.22, .46, .05), rkn=(.08, .43, .15), lank=(-.2, 0, 0), rank=(.18, .07, -.02), club=(-.04, .02, .88))
FINISH = dict(head=(-.2, 1.6, .02), lsh=(-.1, 1.43, -.2), rsh=(-.14, 1.42, .2), lel=(-.02, 1.5, -.38), rel=(-.3, 1.62, .12),
              lwr=(-.05, 1.78, -.12), rwr=(-.03, 1.8, -.08), lhip=(-.12, .93, -.15), rhip=(-.08, .93, .15),
              lkn=(-.2, .48, -.02), rkn=(-.1, .45, .12), lank=(-.2, 0, 0), rank=(.05, .1, .08), club=(.65, 1.3, -.35))
SWING = [(0, ADDRESS), (.1, ADDRESS), (.4, TOP), (.5, IMPACT), (.58, FINISH), (.8, FINISH), (1, ADDRESS)]

BONES = {
    CYAN: [("lsh", "lel"), ("lel", "lwr"), ("lsh", "lhip"), ("lhip", "lkn"), ("lkn", "lank")],
    YELLOW: [("rsh", "rel"), ("rel", "rwr"), ("rsh", "rhip"), ("rhip", "rkn"), ("rkn", "rank")],
    "#ffffff": [("head", "neck"), ("lsh", "rsh"), ("lhip", "rhip")],
    "#c9c6e8": [("grip", "club")],
}


def pose_at(t):
    for (t0, p0), (t1, p1) in zip(SWING, SWING[1:]):
        if t0 <= t <= t1:
            s = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            s = s * s * (3 - 2 * s)
            pose = {k: tuple(a + (b - a) * s for a, b in zip(p0[k], p1[k])) for k in p0}
            break
    mid = lambda a, b: tuple((u + v) / 2 for u, v in zip(pose[a], pose[b]))
    pose["neck"] = mid("lsh", "rsh")
    pose["grip"] = mid("lwr", "rwr")
    return pose


def make_camera(cx, cy, focal=640, dist=5.0, elevation=.2, pivot=.9):
    ce, se = math.cos(elevation), math.sin(elevation)

    def project(p, phi):
        x, y, z = p
        c, s = math.cos(phi), math.sin(phi)
        xr, zr = x * c + z * s, -x * s + z * c
        y0 = y - pivot
        yr, zz = y0 * ce - zr * se, y0 * se + zr * ce
        k = focal / (dist - zz)
        return cx + xr * k, cy - yr * k, k

    return project


def pose_figure(cx, cy):
    frames = 160
    project = make_camera(cx, cy)
    tracks = {}  # name -> list of (x, y, scale)
    bone_d = {color: [] for color in BONES}
    box_d, label_xy, ball_op, ticks_d = [], [], [], []

    for f in range(frames):
        phi = .7 + 2 * math.pi * f / frames
        t = (f % 80) / 80
        pose = pose_at(t)
        if t < .5:
            ball, op = (-.03, .02, .9), 1
        elif t < .75:
            s = (t - .5) / .25
            ball, op = (-.03 - 2.6 * s, .02 + 1.4 * math.sin(math.pi * s * .8), .9 + .4 * s), 1 - s
        else:
            ball, op = (-.03, .02, .9), max(0, (t - .92) / .08)
        pose["ball"] = ball
        ball_op.append(f"{op:.2f}")

        pts = {k: project(v, phi) for k, v in pose.items()}
        for k, v in pts.items():
            tracks.setdefault(k, []).append(v)
        for color, pairs in BONES.items():
            bone_d[color].append("".join(f"M{n(pts[a][0])} {n(pts[a][1])}L{n(pts[b][0])} {n(pts[b][1])}" for a, b in pairs))

        body = [v for k, v in pts.items() if k != "ball"]
        x0, x1 = min(p[0] for p in body) - 16, max(p[0] for p in body) + 16
        y0, y1 = min(p[1] for p in body) - 24, max(p[1] for p in body) + 10
        c = 16
        box_d.append(f"M{n(x0)} {n(y0 + c)}V{n(y0)}H{n(x0 + c)}M{n(x1 - c)} {n(y0)}H{n(x1)}V{n(y0 + c)}"
                     f"M{n(x1)} {n(y1 - c)}V{n(y1)}H{n(x1 - c)}M{n(x0 + c)} {n(y1)}H{n(x0)}V{n(y1 - c)}")
        label_xy.append((x0, y0))

        ticks = []
        for j in range(16):
            a = 2 * math.pi * j / 16
            p1 = project((1.0 * math.cos(a), 0, 1.0 * math.sin(a)), phi)
            p2 = project((1.18 * math.cos(a), 0, 1.18 * math.sin(a)), phi)
            ticks.append(f"M{n(p1[0])} {n(p1[1])}L{n(p2[0])} {n(p2[1])}")
        ticks_d.append("".join(ticks))

    dur = "16s"
    anim = lambda attr, vals: f'<animate attributeName="{attr}" values="{";".join(vals)}" dur="{dur}" repeatCount="indefinite"/>'

    ring = "".join(("M" if i == 0 else "L") + f"{n(p[0])} {n(p[1])}"
                   for i, p in enumerate(project((.95 * math.cos(a), 0, .95 * math.sin(a)), 0)
                                         for a in (2 * math.pi * i / 64 for i in range(65))))
    shadow = project((0, 0, 0), 0)
    out = [f'<ellipse cx="{n(shadow[0])}" cy="{n(shadow[1])}" rx="130" ry="26" fill="{CYAN}" opacity=".25" filter="url(#soft)"/>',
           f'<path d="{ring}Z" fill="none" stroke="{CYAN}" stroke-width="1.5" opacity=".6" filter="url(#glow)"/>',
           f'<path d="{ticks_d[0]}" stroke="{MAGENTA}" stroke-width="2" opacity=".8">{anim("d", ticks_d)}</path>',
           '<g filter="url(#glow)" stroke-linecap="round" fill="none">']
    for color, ds in bone_d.items():
        width = 2 if color == "#c9c6e8" else 4
        out.append(f'<path d="{ds[0]}" stroke="{color}" stroke-width="{width}">{anim("d", ds)}</path>')
    out.append("</g><g filter=\"url(#glow)\">")
    for k, tr in tracks.items():
        if k in ("neck", "grip"):
            continue
        color = "#ffffff" if k in ("head", "ball", "club") else CYAN if k.startswith("l") else YELLOW
        base = {"head": 11, "ball": 3.2, "club": 3}.get(k, 4.2)
        rs = [n(base * s / 128) for _, _, s in tr]
        extra = anim("opacity", ball_op) if k == "ball" else ""
        fill = "none" if k == "head" else color
        stroke = f' stroke="{color}" stroke-width="3"' if k == "head" else ""
        out.append(f'<circle cx="{n(tr[0][0])}" cy="{n(tr[0][1])}" r="{rs[0]}" fill="{fill}"{stroke}>'
                   f'{anim("cx", [n(p[0]) for p in tr])}{anim("cy", [n(p[1]) for p in tr])}{anim("r", rs)}{extra}</circle>')
    out.append("</g>")
    out.append(f'<path d="{box_d[0]}" fill="none" stroke="{MAGENTA}" stroke-width="2.5">{anim("d", box_d)}</path>')
    lx = [n(x) for x, _ in label_xy]
    ly = [n(y - 22) for _, y in label_xy]
    ty = [n(y - 8) for _, y in label_xy]
    tx = [n(x + 8) for x, _ in label_xy]
    out.append(f'<rect x="{lx[0]}" y="{ly[0]}" width="112" height="20" fill="{MAGENTA}">{anim("x", lx)}{anim("y", ly)}</rect>')
    out.append(f'<text class="mono" x="{tx[0]}" y="{ty[0]}" font-size="13" font-weight="700" fill="#12021f">'
               f'golfer 0.97{anim("x", tx)}{anim("y", ty)}</text>')
    return "".join(out)


# --------------------------------------------------------------------------- hero

def hero():
    W, H, HOR = 1200, 460, 330
    SUNX = 905
    rng = random.Random(7)
    css = (".role{opacity:0;animation:role 16s infinite}"
           "@keyframes role{0%{opacity:0;transform:translateY(10px)}3%,22%{opacity:1;transform:translateY(0)}"
           "25%,100%{opacity:0;transform:translateY(-10px)}}"
           ".scan{animation:scan 7s linear infinite}@keyframes scan{from{transform:translateY(-20px)}to{transform:translateY(480px)}}")

    stripes = "".join(f'<rect x="{SUNX - 160}" y="{n(HOR - 78 + i * 13 + i * i * .4)}" width="320" height="{n(2 + i * 1.3)}" fill="#000"/>'
                      for i in range(7))
    defs = (f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#030009"/>'
            f'<stop offset=".72" stop-color="#140639"/><stop offset="1" stop-color="#3a0c55"/></linearGradient>'
            f'<linearGradient id="ground" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22073f"/><stop offset="1" stop-color="#040010"/></linearGradient>'
            f'<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd36b"/>'
            f'<stop offset=".5" stop-color="{MAGENTA}"/><stop offset="1" stop-color="#6d28d9"/></linearGradient>'
            f'<mask id="slits"><rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>{stripes}</mask>'
            f'<clipPath id="aboveHorizon"><rect x="0" y="0" width="{W}" height="{HOR}"/></clipPath>'
            f'<radialGradient id="vignette" cx=".5" cy=".5" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity=".75"/></radialGradient>'
            f'<linearGradient id="scanG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{CYAN}" stop-opacity=".18"/></linearGradient>'
            + shimmer_gradient("nameG", 60, 640))

    # low-poly mountains, kept low behind the sun
    ridge, x, i = [(0, HOR)], 0, 0
    while x < W:
        x = min(W, x + rng.uniform(38, 80))
        near_sun = abs(x - SUNX) < 150
        peak = rng.uniform(4, 12) if near_sun else rng.uniform(22, 58) if i % 2 == 0 else rng.uniform(6, 18)
        ridge.append((x, HOR - peak))
        i += 1
    ridge.append((W, HOR))
    ridge_pts = " ".join(f"{n(a)},{n(b)}" for a, b in ridge)

    roles = ["Computer Vision Engineer @ PracticeBuzz", "Real-time pose estimation · edge AI",
             "LLMs · RAG · multimodal AI", "Kaggle Master · published researcher"]
    role_svg = "".join(
        f'<text class="mono role" x="64" y="266" font-size="22" fill="{INK}" style="animation-delay:{i * 4}s">'
        f'<tspan fill="{MAGENTA}">› </tspan>{esc(r)}</text>' for i, r in enumerate(roles))

    pills, px = [], 64
    for label, color in (("KAGGLE MASTER", CYAN), ("CRC PRESS AUTHOR", MAGENTA), ("9.71 CGPA", YELLOW)):
        w = len(label) * 8.2 + 28
        pills.append(f'<rect x="{n(px)}" y="292" width="{n(w)}" height="28" rx="14" fill="{color}" fill-opacity=".1" stroke="{color}" stroke-width="1.4"/>'
                     f'<text class="mono" x="{n(px + w / 2)}" y="311" font-size="13" font-weight="700" text-anchor="middle" fill="{color}">{label}</text>')
        px += w + 12

    brackets = "".join(
        f'<path d="M{x0} {y0 + 26 * sy}V{y0}H{x0 + 26 * sx}" fill="none" stroke="{CYAN}" stroke-width="2" opacity=".8"/>'
        for x0, y0, sx, sy in ((16, 16, 1, 1), (W - 16, 16, -1, 1), (16, H - 16, 1, -1), (W - 16, H - 16, -1, -1)))

    body = (f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
            f'{stars(rng, W, HOR - 20, 90)}'
            f'<circle cx="{SUNX}" cy="{HOR - 40}" r="175" fill="{MAGENTA}" opacity=".3" filter="url(#soft)"/>'
            f'<g clip-path="url(#aboveHorizon)"><circle cx="{SUNX}" cy="{HOR}" r="138" fill="url(#sun)" mask="url(#slits)" opacity=".62"/></g>'
            f'<polygon points="{ridge_pts}" fill="#0a0322" stroke="{CYAN}" stroke-opacity=".45" stroke-width="1.2"/>'
            f'<rect y="{HOR}" width="{W}" height="{H - HOR}" fill="url(#ground)"/>'
            + floor_grid("fl", W, HOR, H, MAGENTA)
            + f'<line x1="0" y1="{HOR}" x2="{W}" y2="{HOR}" stroke="{MAGENTA}" stroke-width="2" filter="url(#glow)"/>'
            + pose_figure(SUNX, 290)
            + f'<text class="mono" x="64" y="128" font-size="18" fill="{CYAN}" letter-spacing="3">&gt; HELLO_WORLD, I AM'
              f'<tspan class="blink">_</tspan></text>'
            + f'<text x="64" y="214" font-size="72" letter-spacing="2" fill="{MAGENTA}" opacity=".7" filter="url(#soft)">ANMOL GUPTA</text>'
            + text3d(64, 214, "ANMOL GUPTA", 72, 10, "url(#nameG)")
            + role_svg + "".join(pills)
            + f'<rect x="48" y="{H - 52}" width="640" height="30" rx="6" fill="#05010f" fill-opacity=".75" stroke="{CYAN}" stroke-opacity=".35"/>'
            + f'<circle cx="68" cy="{H - 37}" r="5" fill="#ff3b5c" class="blink"/>'
            + f'<text class="mono" x="82" y="{H - 32}" font-size="13" fill="{DIM}"><tspan fill="#ff3b5c" font-weight="700">LIVE</tspan>'
              f'  camera → pose-net → tracker → FastAPI → AWS → iOS / Android</text>'
            + f'<text class="mono" x="{W - 40}" y="48" font-size="13" text-anchor="end" fill="{DIM}" letter-spacing="1">'
              f'POSE-3D // 17 KPTS // <tspan fill="{CYAN}">60 FPS</tspan></text>'
            + f'<rect class="scan" x="0" y="0" width="{W}" height="18" fill="url(#scanG)"/>'
            + f'<rect width="{W}" height="{H}" fill="url(#vignette)" pointer-events="none"/>'
            + brackets)
    return svg_doc(W, H, body, "Anmol Gupta — Computer Vision Engineer", css, defs)


# --------------------------------------------------------------------------- section headers

def section(index, title):
    W, H = 1200, 120
    size = 46
    half = len(title) * (size * .74 + 4) / 2
    left_end, right_start = 600 - half - 40, 600 + half + 40
    flow = '<animate attributeName="stroke-dashoffset" values="0;-900" dur="3.2s" repeatCount="indefinite"/>'
    body = (f'<g filter="url(#glow)">'
            f'<line x1="60" y1="66" x2="{n(left_end)}" y2="66" stroke="{VIOLET}" stroke-opacity=".4" stroke-width="2"/>'
            f'<line x1="{n(right_start)}" y1="66" x2="1140" y2="66" stroke="{VIOLET}" stroke-opacity=".4" stroke-width="2"/>'
            f'<line x1="60" y1="66" x2="{n(left_end)}" y2="66" stroke="{CYAN}" stroke-width="3" stroke-dasharray="70 830">{flow}</line>'
            f'<line x1="1140" y1="66" x2="{n(right_start)}" y2="66" stroke="{MAGENTA}" stroke-width="3" stroke-dasharray="70 830">{flow}</line>'
            f'<rect x="{n(left_end - 5)}" y="61" width="10" height="10" transform="rotate(45 {n(left_end)} 66)" fill="{CYAN}"/>'
            f'<rect x="{n(right_start - 5)}" y="61" width="10" height="10" transform="rotate(45 {n(right_start)} 66)" fill="{MAGENTA}"/>'
            '</g>'
            f'<text class="mono" x="600" y="24" font-size="14" text-anchor="middle" fill="{DIM}" letter-spacing="6">// {index:02d}</text>'
            + text3d(600, 84, title, size, 7, "url(#secG)", anchor="middle", spacing=4))
    return svg_doc(W, H, body, title, defs=shimmer_gradient("secG", 600 - half, 600 + half))


# --------------------------------------------------------------------------- terminal + wireframe

ICOSA_V = [(-1, 1.618, 0), (1, 1.618, 0), (-1, -1.618, 0), (1, -1.618, 0), (0, -1, 1.618), (0, 1, 1.618),
           (0, -1, -1.618), (0, 1, -1.618), (1.618, 0, -1), (1.618, 0, 1), (-1.618, 0, -1), (-1.618, 0, 1)]


def icosahedron(cx, cy, radius, frames=64, dur="10s"):
    edges = [(i, j) for i in range(12) for j in range(i + 1, 12)
             if abs(math.dist(ICOSA_V[i], ICOSA_V[j]) - 2) < 1e-3]
    per_edge = {e: ([], []) for e in edges}
    verts = [([], [], []) for _ in ICOSA_V]
    for f in range(frames):
        a, b = 2 * math.pi * f / frames, 2 * math.pi * f / frames * 2
        proj = []
        for x, y, z in ICOSA_V:
            x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
            y, z = y * math.cos(b) - z * math.sin(b), y * math.sin(b) + z * math.cos(b)
            k = 5 / (7 - z)
            proj.append((cx + x * k * radius / 1.9, cy + y * k * radius / 1.9, z))
        for e in edges:
            p, q = proj[e[0]], proj[e[1]]
            per_edge[e][0].append(f"M{n(p[0])} {n(p[1])}L{n(q[0])} {n(q[1])}")
            per_edge[e][1].append(f"{.2 + .8 * ((p[2] + q[2]) / 2 + 1.9) / 3.8:.2f}")
        for vi, p in enumerate(proj):
            verts[vi][0].append(n(p[0]))
            verts[vi][1].append(n(p[1]))
            verts[vi][2].append(f"{.25 + .75 * (p[2] + 1.9) / 3.8:.2f}")
    anim = lambda attr, vals: f'<animate attributeName="{attr}" values="{";".join(vals)}" dur="{dur}" repeatCount="indefinite"/>'
    out = ['<g filter="url(#glow)" stroke-linecap="round">']
    for i, (e, (ds, ops)) in enumerate(per_edge.items()):
        color = CYAN if i % 2 == 0 else MAGENTA
        out.append(f'<path d="{ds[0]}" stroke="{color}" stroke-width="2">{anim("d", ds)}{anim("stroke-opacity", ops)}</path>')
    for xs, ys, ops in verts:
        out.append(f'<circle cx="{xs[0]}" cy="{ys[0]}" r="3.5" fill="#fff">{anim("cx", xs)}{anim("cy", ys)}{anim("opacity", ops)}</circle>')
    out.append("</g>")
    return "".join(out)


def terminal():
    lines = [
        ("cmd", "whoami"),
        ("out", "Anmol Gupta — Computer Vision Engineer @ PracticeBuzz"),
        ("cmd", "cat role.txt"),
        ("out", "Real-time CV & AI for sports + wellness products, R&D to production"),
        ("cmd", "cat pipeline.yml"),
        ("out", "pose-estimation → tracking → FastAPI → AWS → CoreML / TFLite"),
        ("cmd", "ls ~/research"),
        ("out", "hybrid-1dcnn-rnn-profession-prediction.pdf  [CRC Press · 2026]"),
        ("cmd", "cat now.txt"),
        ("out", "LLMs · RAG · multimodal AI · edge inference"),
        ("cmd", "echo $FUEL"),
        ("out", "masala chai, always"),
    ]
    W, H = 1200, 540
    x0, y0, step, cw, fs = 64, 128, 30, 9.7, 16
    prompt = "anmol@cv-lab:~$ "
    pw = len(prompt) * cw
    t = .9
    defs, rows = [], []
    for i, (kind, text) in enumerate(lines):
        y = y0 + i * step
        if kind == "cmd":
            dur = len(text) * .06
            widths = ";".join(n(k * cw) for k in range(len(text) + 1))
            cursor_x = ";".join(n(x0 + pw + k * cw) for k in range(len(text) + 1))
            defs.append(f'<clipPath id="ty{i}"><rect x="{n(x0 + pw)}" y="{y - 20}" height="28" width="0">'
                        f'<animate attributeName="width" values="{widths}" begin="{t:.2f}s" dur="{dur:.2f}s" calcMode="discrete" fill="freeze"/></rect></clipPath>')
            rows.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                        f'<text class="mono" x="{x0}" y="{y}" font-size="{fs}" fill="{CYAN}">anmol@cv-lab<tspan fill="{DIM}">:</tspan>'
                        f'<tspan fill="{MAGENTA}">~</tspan><tspan fill="{DIM}">$</tspan></text>'
                        f'<text class="mono" x="{n(x0 + pw)}" y="{y}" font-size="{fs}" fill="#ffffff" clip-path="url(#ty{i})">{esc(text)}</text></g>'
                        f'<rect x="{n(x0 + pw)}" y="{y - 15}" width="9" height="19" fill="{CYAN}" opacity="0">'
                        f'<animate attributeName="x" values="{cursor_x}" begin="{t:.2f}s" dur="{dur:.2f}s" calcMode="discrete" fill="freeze"/>'
                        f'<set attributeName="opacity" to="1" begin="{t:.2f}s"/><set attributeName="opacity" to="0" begin="{t + dur + .25:.2f}s"/></rect>')
            t += dur + .35
        else:
            rows.append(f'<text class="mono" x="{x0 + 20}" y="{y}" font-size="{fs}" fill="{INK}" fill-opacity=".85" opacity="0">'
                        f'<tspan fill="{VIOLET}">→ </tspan>{esc(text)}'
                        f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/></text>')
            t += .45
    y = y0 + len(lines) * step
    rows.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                f'<text class="mono" x="{x0}" y="{y}" font-size="{fs}" fill="{CYAN}">anmol@cv-lab<tspan fill="{DIM}">:</tspan>'
                f'<tspan fill="{MAGENTA}">~</tspan><tspan fill="{DIM}">$</tspan></text>'
                f'<rect class="blink" x="{n(x0 + pw)}" y="{y - 15}" width="9" height="19" fill="{CYAN}"/></g>')

    win_x, win_y, win_w, win_h = 24, 20, 1140, 490
    dots = "".join(f'<circle cx="{win_x + 30 + i * 22}" cy="{win_y + 24}" r="7" fill="{c}"/>'
                   for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")))
    scan = '<pattern id="lines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" fill-opacity=".025"/></pattern>'
    body = (slab(win_x, win_y, win_w, win_h, 14, "t", CYAN, rx=18, fill_top="#0e0830", fill_bottom="#070318")
            + f'<rect x="{win_x}" y="{win_y}" width="{win_w}" height="{win_h}" rx="18" fill="url(#lines)"/>'
            + f'<path d="M{win_x + 2} {win_y + 48}H{win_x + win_w - 2}" stroke="{CYAN}" stroke-opacity=".25"/>'
            + dots
            + f'<text class="mono" x="{win_x + win_w / 2}" y="{win_y + 30}" font-size="14" text-anchor="middle" fill="{DIM}">anmol@cv-lab — zsh — 120×32</text>'
            + "".join(rows)
            + icosahedron(1030, 250, 100)
            + f'<text class="mono" x="1030" y="410" font-size="13" text-anchor="middle" fill="{DIM}">latent_space.obj</text>')
    return svg_doc(W, H, body, "About Anmol — terminal", defs="".join(defs) + scan)


# --------------------------------------------------------------------------- project cards

def wrap(text, width):
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur] if cur else lines


def card(num, tag, title, desc, chips, cta, accent):
    W, H = 600, 370
    size = min(30, 470 / (len(title) * .62))
    desc_svg = "".join(f'<text class="sans" x="56" y="{168 + i * 27}" font-size="19" fill="{INK}" fill-opacity=".82">{esc(line)}</text>'
                       for i, line in enumerate(wrap(desc, 46)))
    chip_svg, cx = [], 56
    for chip in chips:
        w = len(chip) * 8.3 + 24
        chip_svg.append(f'<rect x="{n(cx)}" y="262" width="{n(w)}" height="30" rx="8" fill="{accent}" fill-opacity=".1" stroke="{accent}" stroke-opacity=".6"/>'
                        f'<text class="mono" x="{n(cx + w / 2)}" y="282" font-size="13" text-anchor="middle" fill="{accent}">{esc(chip)}</text>')
        cx += w + 10
    body = (f'<ellipse class="shadow" cx="300" cy="346" rx="230" ry="16" fill="{accent}" opacity=".35" filter="url(#soft)"/>'
            '<g class="float">'
            + slab(24, 24, 540, 290, 16, "c", accent)
            + f'<text x="536" y="130" font-size="110" text-anchor="end" fill="{accent}" fill-opacity=".07">{num:02d}</text>'
            + f'<text class="mono" x="56" y="74" font-size="14" letter-spacing="2" fill="{accent}">{esc(tag)}</text>'
            + f'<text x="56" y="120" font-size="{n(size)}" fill="#ffffff">{esc(title)}</text>'
            + desc_svg + "".join(chip_svg)
            + f'<text class="mono" x="536" y="282" font-size="14" font-weight="700" text-anchor="end" fill="{accent}">{esc(cta)}</text>'
            '</g>')
    return svg_doc(W, H, body, title)


# --------------------------------------------------------------------------- achievements

def leetcode_stats():
    query = {"query": "query($u:String!){matchedUser(username:$u){submitStats{acSubmissionNum{difficulty count}}}}",
             "variables": {"u": LEETCODE_USER}}
    try:
        data = json.loads(fetch("https://leetcode.com/graphql", json.dumps(query).encode(),
                                {"Content-Type": "application/json", "Referer": "https://leetcode.com"}))
        counts = {row["difficulty"].lower(): row["count"]
                  for row in data["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]}
        return {"all": counts["all"], "medium": counts["medium"], "hard": counts["hard"]}
    except Exception as exc:  # network hiccup or API change: keep the last known numbers
        print(f"  leetcode fetch failed ({exc}); using fallback")
        return LEETCODE_FALLBACK


def achievements(lc):
    W, H = 1200, 280
    items = [
        ("MASTER", "KAGGLE", "10+ comps · 40+ notebooks", CYAN),
        ("TOP 8%", "KAGGLE PLAYGROUND", "insurance cross-selling", MAGENTA),
        (str(lc["all"]), "LEETCODE SOLVED", f'{lc["medium"]} medium · {lc["hard"]} hard', YELLOW),
        ("9.71", "B.TECH CGPA", "CSE · AI & ML", VIOLET),
    ]
    w, h, gap = 246, 190, 30
    x0 = (W - (4 * w + 3 * gap)) / 2
    out = []
    for i, (value, label, sub, accent) in enumerate(items):
        x, y = x0 + i * (w + gap), 30
        size = min(56, 200 / (len(value) * .72))
        delay = f"animation-delay:-{i * 1.25}s"
        out.append(f'<ellipse class="shadow" style="{delay}" cx="{n(x + w / 2)}" cy="{y + h + 28}" rx="{w / 2 - 20}" ry="12" fill="{accent}" opacity=".4" filter="url(#soft)"/>'
                   f'<g class="float" style="{delay}">'
                   + slab(x, y, w, h, 18, f"a{i}", accent)
                   + f'<rect x="{n(x + 24)}" y="{y + 22}" width="44" height="4" rx="2" fill="{accent}"/>'
                   + f'<text x="{n(x + w / 2)}" y="{y + 104}" font-size="{n(size)}" text-anchor="middle" fill="url(#achG)">{esc(value)}</text>'
                   + f'<text class="mono" x="{n(x + w / 2)}" y="{y + 142}" font-size="15" font-weight="700" letter-spacing="1.5" text-anchor="middle" fill="{INK}">{esc(label)}</text>'
                   + f'<text class="mono" x="{n(x + w / 2)}" y="{y + 166}" font-size="13" text-anchor="middle" fill="{DIM}">{esc(sub)}</text>'
                   '</g>')
    return svg_doc(W, H, "".join(out), "Achievements", defs=shimmer_gradient("achG", 60, 1140))


# --------------------------------------------------------------------------- 3D contribution city

def contributions():
    page = fetch(f"https://github.com/users/{GITHUB_USER}/contributions")
    tips = {m.group(1): m.group(2) for m in re.finditer(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', page)}
    days = []
    for tag in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", page):
        date = re.search(r'data-date="([\d-]+)"', tag)
        cid = re.search(r'id="contribution-day-component-(\d+)-(\d+)"', tag)
        if not (date and cid):
            continue
        count = re.match(r"\s*(\d+) contribution", tips.get(f"contribution-day-component-{cid.group(1)}-{cid.group(2)}", ""))
        days.append({"date": date.group(1), "row": int(cid.group(1)), "col": int(cid.group(2)),
                     "count": int(count.group(1)) if count else 0})
    if len(days) < 300:
        raise RuntimeError(f"only parsed {len(days)} contribution days")
    return sorted(days, key=lambda d: d["date"])


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    current = 0
    tail = days[:-1] if days[-1]["count"] == 0 else days  # today may simply not have commits yet
    for d in reversed(tail):
        if not d["count"]:
            break
        current += 1
    return longest, current


def contrib_city(days):
    W, H = 1200, 680
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])
    longest, current = streaks(days)
    peak = max(best["count"], 1)

    ux, uy, vx, vy, k = 13.2, 5.0, -9.0, 8.0, .8
    cols = max(d["col"] for d in days) + 1
    ox, oy = (W - (cols * ux - 7 * vx)) / 2 - 7 * vx - 20, 318
    levels = [(0, "#1a1140"), (.15, "#5b21b6"), (.4, VIOLET), (.7, MAGENTA), (1.01, CYAN)]

    def color_for(ratio):
        for (r0, c0), (r1, c1) in zip(levels, levels[1:]):
            if ratio <= r1:
                return mix(c0, c1, (ratio - r0) / (r1 - r0))
        return CYAN

    pt = lambda x, y: f"{n(x)},{n(y)}"
    bars = []
    for d in sorted(days, key=lambda d: (d["col"], d["row"])):
        bx, by = ox + d["col"] * ux + d["row"] * vx, oy + d["col"] * uy + d["row"] * vy
        p0, p1 = (bx, by), (bx + ux * k, by + uy * k)
        p2, p3 = (p1[0] + vx * k, p1[1] + vy * k), (bx + vx * k, by + vy * k)
        if not d["count"]:
            bars.append(f'<polygon points="{pt(*p0)} {pt(*p1)} {pt(*p2)} {pt(*p3)}" fill="#140c34" stroke="#2a1d5c" stroke-width=".6"/>')
            continue
        ratio = math.sqrt(d["count"] / peak)
        h = 6 + 118 * ratio
        top = color_for(ratio)
        up = lambda p: (p[0], p[1] - h)
        bars.append(
            f'<g class="bar" style="animation-delay:{d["col"] * .035:.2f}s">'
            f'<polygon points="{pt(*p1)} {pt(*p2)} {pt(*up(p2))} {pt(*up(p1))}" fill="{mix(top, "#000000", .45)}"/>'
            f'<polygon points="{pt(*p3)} {pt(*p2)} {pt(*up(p2))} {pt(*up(p3))}" fill="{mix(top, "#000000", .62)}"/>'
            f'<polygon points="{pt(*up(p0))} {pt(*up(p1))} {pt(*up(p2))} {pt(*up(p3))}" fill="{top}"/>'
            '</g>')

    # glowing base plate under the grid
    pad = 10
    c0 = (ox - pad, oy - pad * .4)
    c1 = (ox + cols * ux + pad, oy + cols * uy - pad * .4)
    c2 = (c1[0] + 7 * vx - pad * .3, c1[1] + 7 * vy + pad)
    c3 = (c0[0] + 7 * vx - pad * .3, c0[1] + 7 * vy + pad)
    plate = (f'<polygon points="{pt(*c0)} {pt(*c1)} {pt(*c2)} {pt(*c3)}" fill="#0a0524" stroke="{CYAN}" stroke-width="2" '
             f'stroke-dasharray="40 16" filter="url(#glow)" transform="translate(0 8)">'
             '<animate attributeName="stroke-dashoffset" values="0;-560" dur="6s" repeatCount="indefinite"/></polygon>')

    months, last = [], None
    for d in days:
        if d["row"] == 0:
            month = d["date"][5:7]
            if month != last and d["col"] < cols - 1:
                x, y = ox + d["col"] * ux + 7.8 * vx, oy + d["col"] * uy + 7.8 * vy + 22
                name = "JanFebMarAprMayJunJulAugSepOctNovDec"[(int(month) - 1) * 3:int(month) * 3]
                months.append(f'<text class="mono" x="{n(x)}" y="{n(y)}" font-size="12" fill="{DIM}">{name}</text>')
            last = month

    bx = ox + best["col"] * ux + best["row"] * vx + (ux + vx) * k / 2
    by = oy + best["col"] * uy + best["row"] * vy + (uy + vy) * k / 2 - (6 + 118) - 18
    marker = (f'<g class="bob"><path d="M{n(bx)} {n(by)}l-8 -12h16z" fill="{YELLOW}" filter="url(#glow)"/>'
              f'<text class="mono" x="{n(bx)}" y="{n(by - 20)}" font-size="13" font-weight="700" text-anchor="middle" fill="{YELLOW}">'
              f'BEST DAY · {best["count"]}</text></g>')

    tiles, tw, th, tg = [], 214, 84, 18
    tx0 = W - 40 - 2 * tw - tg
    for i, (value, label, accent) in enumerate(((f"{total:,}", "CONTRIBUTIONS · 1Y", CYAN), (str(best["count"]), "BEST DAY · 1Y", YELLOW),
                                                 (f"{longest}d", "LONGEST STREAK · 1Y", MAGENTA), (f"{current}d", "CURRENT STREAK", VIOLET))):
        x, y = tx0 + i % 2 * (tw + tg), 40 + i // 2 * (th + tg)
        tiles.append(slab(x, y, tw, th, 10, f"s{i}", accent, rx=12)
                     + f'<text x="{x + 22}" y="{y + 48}" font-size="32" fill="{accent}">{value}</text>'
                     + f'<text class="mono" x="{x + 22}" y="{y + 70}" font-size="12" letter-spacing="1.5" fill="{DIM}">{label}</text>')

    css = (".bar{transform-box:fill-box;transform-origin:50% 100%;animation:grow 1.1s cubic-bezier(.2,.9,.25,1.15) both}"
           "@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}"
           ".bob{animation:float 2.6s ease-in-out infinite}")
    legend = "".join(f'<rect x="{84 + i * 24}" y="120" width="18" height="18" rx="3" fill="{c}"/>'
                     for i, c in enumerate(("#140c34", "#5b21b6", VIOLET, MAGENTA, CYAN)))
    body = (f'<rect width="{W}" height="{H}" rx="22" fill="{BG}"/>'
            f'{stars(random.Random(3), W, H, 60)}'
            + text3d(40, 70, "CONTRIBUTION CITY", 40, 6, "url(#cityG)", spacing=3)
            + f'<text class="mono" x="42" y="100" font-size="14" fill="{DIM}">github.com/{GITHUB_USER} · last 12 months · rebuilt daily</text>'
            + "".join(tiles) + plate + "".join(bars) + "".join(months) + marker
            + f'<text class="mono" x="42" y="134" font-size="12" fill="{DIM}">less</text>{legend}'
            + f'<text class="mono" x="216" y="134" font-size="12" fill="{DIM}">more</text>')
    return svg_doc(W, H, body, f"{total} contributions in the last year", css, shimmer_gradient("cityG", 40, 560))


# --------------------------------------------------------------------------- footer

def footer():
    W, H, HOR = 1200, 220, 110
    body = (f'<rect width="{W}" height="{H}" fill="{BG}"/>'
            f'{stars(random.Random(11), W, HOR, 40)}'
            f'<rect y="{HOR}" width="{W}" height="{H - HOR}" fill="#12032a"/>'
            + floor_grid("ft", W, HOR, H, VIOLET, spacing=58, dur=1.6)
            + f'<line x1="0" y1="{HOR}" x2="{W}" y2="{HOR}" stroke="{MAGENTA}" stroke-width="2" filter="url(#glow)"/>'
            + f'<text x="600" y="84" font-size="26" letter-spacing="3" text-anchor="middle" fill="{MAGENTA}" opacity=".7" filter="url(#soft)">'
              "LET'S BUILD SOMETHING THAT WORKS OUTSIDE THE NOTEBOOK</text>"
            + text3d(600, 84, "LET'S BUILD SOMETHING THAT WORKS OUTSIDE THE NOTEBOOK", 26, 5, "url(#ftG)", anchor="middle", spacing=3))
    return svg_doc(W, H, body, "Thanks for visiting", defs=shimmer_gradient("ftG", 140, 1060))


# --------------------------------------------------------------------------- main

def main():
    os.makedirs(ASSETS, exist_ok=True)
    print("static assets")
    write("hero.svg", hero())
    write("terminal.svg", terminal())
    for i, (slug, title) in enumerate((("about", "ABOUT ME"), ("stack", "TECH ARSENAL"), ("projects", "FEATURED BUILDS"),
                                       ("achievements", "ACHIEVEMENTS"), ("activity", "ACTIVITY")), start=1):
        write(f"section-{slug}.svg", section(i, title))
    write("card-translation.svg", card(1, "PROJECT_01 · NLP", "Neural Machine Translation",
                                       "English → Hindi translation built on an LSTM encoder-decoder with a self-attention mechanism.",
                                       ["TensorFlow", "Seq2Seq", "Attention"], "VIEW REPO →", CYAN))
    write("card-retinopathy.svg", card(2, "PROJECT_02 · MEDICAL CV", "Diabetic Retinopathy Detection",
                                       "CNN + InceptionV3 trained on retinal images to detect and grade diabetic retinopathy for early diagnosis.",
                                       ["CNN", "InceptionV3", "Medical Imaging"], "VIEW REPO →", MAGENTA))
    write("card-kaggle.svg", card(3, "KAGGLE · MASTER", "40+ Kaggle Notebooks",
                                  "ML, deep learning, CV and NLP notebooks plus 10+ competitions, including a top 8% Playground finish.",
                                  ["EDA", "Modelling", "Competitions"], "OPEN KAGGLE →", YELLOW))
    write("card-research.svg", card(4, "RESEARCH · CRC PRESS 2026", "Hybrid 1D-CNN + RNN Model",
                                    "Profession prediction using astrology, published at the International Conference on AI and Sustainable Innovation.",
                                    ["1D-CNN", "RNN", "Publication"], "PUBLISHED", VIOLET))
    write("footer.svg", footer())

    print("live data assets")
    write("achievements.svg", achievements(leetcode_stats()))
    try:
        write("contrib-city.svg", contrib_city(contributions()))
    except Exception as exc:
        if not os.path.exists(os.path.join(ASSETS, "contrib-city.svg")):
            raise
        print(f"  contribution fetch failed ({exc}); keeping previous contrib-city.svg")


if __name__ == "__main__":
    main()
