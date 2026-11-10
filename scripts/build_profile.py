"""Build the animated profile README assets.

Layout: an animated hero with a "video" frame, a familiar, My mage way, the spell
arsenal, a mage registration card with a live GitHub dashboard, the quest table,
a 3D contribution realm (made by a separate Action step) and a connect panel.
The character is the data mage from assets/art. Everything is drawn here from
scratch; artwork and the JetBrains Mono font (SIL OFL) are embedded as base64
because GitHub shows README SVGs as images, which cannot load other files.
Tech logos come from Simple Icons (CC0), stored in assets/icons.json.

Standard library only. Needs a GitHub token in GH_TOKEN or GITHUB_TOKEN for the
live numbers (the GitHub Action passes its own token).

Usage: python scripts/build_profile.py
"""
import base64
import datetime as dt
import json
import math
import os
import random
import re
import sys
import urllib.request
from html import escape
from pathlib import Path

USER = "BerkeArdaTurk21"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ART = ASSETS / "art"
FONTS = ASSETS / "fonts"
ICONS = json.loads((ASSETS / "icons.json").read_text(encoding="utf-8"))
# GitHub caches README images; bump this (and the ?v= numbers in README.md) after a design change.
CACHE_VERSION = 7
W = 1280

# Palette: night sky with ice blue and violet light, like the portrait.
BG, PANEL, PANEL2 = "#0b0f19", "#121826", "#161e2f"
LINE, INK, MUTED, DIM = "#232c3f", "#e6edf6", "#8b97ab", "#5b667a"
ICE, ICE2, VIOLET, GOLD, GREEN = "#7dd3fc", "#38bdf8", "#a78bfa", "#fbbf24", "#34d399"

# Elder Futhark runes as stroke paths in a unit box (about 0.5 wide, 1 tall).
RUNES = {
    "fehu": "M0 0V1M0 .3L.45 .05M0 .55L.45 .3",
    "uruz": "M0 1V0L.5 .3V1",
    "ansuz": "M0 0V1M0 0L.45 .25M0 .3L.45 .55",
    "raidho": "M0 1V0L.45 .25L0 .5L.45 1",
    "kenaz": "M.45 .15L0 .5L.45 .85",
    "gebo": "M0 0L.5 1M.5 0L0 1",
    "algiz": "M.25 0V1M.25 .4L0 0M.25 .4L.5 0",
    "sowilo": "M.45 0L0 .4L.45 .6L0 1",
    "tiwaz": "M.25 0V1M0 .3L.25 0L.5 .3",
    "berkano": "M0 0V1M0 0L.4 .25L0 .5L.4 .75L0 1",
    "ehwaz": "M0 1V0L.25 .3L.5 0V1",
    "mannaz": "M0 1V0L.5 .4M.5 1V0L0 .4",
    "laguz": "M0 0V1M0 0L.4 .3",
    "ingwaz": "M.25 .2L.5 .5L.25 .8L0 .5Z",
    "dagaz": "M0 0V1L.5 0V1L0 0",
    "othala": "M.25 0L.5 .3L0 .9M.25 0L0 .3L.5 .9",
}
NAME_RUNES = ["berkano", "ehwaz", "raidho", "kenaz", "ehwaz", None, "ansuz", "raidho", "dagaz", "ansuz",
              None, "tiwaz", "uruz", "raidho", "kenaz", None]

ROLES = ["Data Science Student", "Machine Learning Apprentice", "Data Leakage Hunter"]
MOTTO = "Baseline first. Then magic."

WAY = [
    ("algiz", "Models that do not leak",
     "foldsafe flags data leakage before cross-validation scores mislead you"),
    ("kenaz", "Predictions you can explain",
     "A simple baseline first, SHAP for every prediction, honest notes on limits"),
    ("raidho", "Data at scale",
     "Apache Spark and PySpark pipelines in a university team project"),
]

# (label, icon key in icons.json or a rune name, colour)
SPELLS = [
    ("Python", "python", "#3776AB"), ("SQL", "mysql", "#4479A1"), ("TypeScript", "typescript", "#3178C6"),
    ("Java", "openjdk", "#ED8B00"), ("React", "react", "#61DAFB"),
    ("scikit-learn", "scikitlearn", "#F7931E"), ("XGBoost", "rune:ingwaz", "#3AB7BF"),
    ("SHAP", "rune:kenaz", "#FF0D57"), ("PyTorch", "pytorch", "#EE4C2C"), ("pandas", "pandas", "#E70488"),
    ("NumPy", "numpy", "#4DABCF"), ("Jupyter", "jupyter", "#F37626"), ("PySpark", "apachespark", "#E25A1C"),
    ("Streamlit", "streamlit", "#FF4B4B"), ("Git", "git", "#F05032"),
]

MANA = [
    (ICE, "TABULAR ML", "scikit-learn · XGBoost", "leak-free pipelines, CV done right"),
    (VIOLET, "EXPLAINABILITY", "SHAP · plain words", "every prediction gets a why"),
    (GOLD, "BIG DATA", "PySpark · Apache Spark", "university team project"),
]

CONTACTS = [
    ("github", "#e6edf6", "GitHub", "@BerkeArdaTurk21"),
    ("gmail", "#EA4335", "Email", "turkberkearda@gmail.com"),
    ("linkedin", "#0A66C2", "LinkedIn", "in/berke-arda-turk"),
    ("kaggle", "#20BEFF", "Kaggle", "@berketurk"),
]

# Quest table, in the same order as the pinned repos.
FEATURED = [
    ("foldsafe", "foldsafe", "Static analyzer and agent skill that catch data leakage in ML code",
     ["Python", "static analysis"]),
    ("kaggle-titanic", "Kaggle Titanic", "Leak-free pipelines and nested CV · Kaggle 0.794",
     ["scikit-learn", "XGBoost"]),
    ("customer-churn-shap-dashboard", "Churn SHAP Dashboard", "XGBoost churn model with a SHAP why for every prediction",
     ["XGBoost", "SHAP", "Streamlit"]),
    ("Stock-Sentiment-Predictor", "Stock Sentiment", "Three-class sentiment on 4,846 financial headlines",
     ["NLP", "scikit-learn"]),
    ("EconoScope", "EconoScope", "Inflation in 212 countries, 1970-2022",
     ["pandas", "EDA"]),
    ("Python-RoadMap", "Python RoadMap", "Eight weeks of daily lessons, quizzes and four projects",
     ["Python"]),
]

# Octicons (MIT) for the dashboard tiles, 16 x 16.
OCT = {
    "repo": ("M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5"
             "h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708"
             "A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087"
             "a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"),
    "star": ("M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192"
             "a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1"
             " .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"),
    "fork": ("M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25"
             " 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1"
             " 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75"
             "a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"),
    "person": ("M10.561 8.073a6.005 6.005 0 0 1 3.432 5.142.75.75 0 1 1-1.498.07 4.5 4.5 0 0 0-8.99 0 .75.75 0 0 1"
               "-1.498-.07 6.004 6.004 0 0 1 3.431-5.142 3.999 3.999 0 1 1 5.123 0ZM10.5 5a2.5 2.5 0 1 0-5 0 2.5 2.5"
               " 0 0 0 5 0Z"),
}


# --- building blocks ---------------------------------------------------------

def b64(path):
    return base64.b64encode(path.read_bytes()).decode("ascii")


FONT_CSS = "".join(
    f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{b64(FONTS / file)}) format('woff2')}}"
    for family, file in (("JBM", "JetBrainsMono-Regular.woff2"), ("JBMB", "JetBrainsMono-Bold.woff2"),
                         ("JBMX", "JetBrainsMono-ExtraBold.woff2")))
FALLBACK = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

CSS = (
    "text{font-family:'JBM'," + FALLBACK + ";font-variant-ligatures:none;font-feature-settings:'liga' 0,'calt' 0}"
    ".b{font-family:'JBMB'," + FALLBACK + ";font-weight:700}"
    ".x{font-family:'JBMX'," + FALLBACK + ";font-weight:800}"
    ".fu{opacity:0;animation:fu .9s ease forwards}"
    "@keyframes fu{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}"
    ".fl{opacity:0;animation:fl 1s ease forwards}"
    "@keyframes fl{from{opacity:0;transform:translateX(-24px)}to{opacity:1;transform:none}}"
    ".fi{opacity:0;animation:fi 1.2s ease forwards}@keyframes fi{to{opacity:1}}"
    ".blink{animation:bl 1s steps(1) infinite}@keyframes bl{50%{opacity:0}}"
    ".tw{animation:tw 3.4s ease-in-out infinite}@keyframes tw{50%{opacity:.15}}"
    ".pulse{animation:pu 3.2s ease-in-out infinite}@keyframes pu{50%{opacity:.4}}"
    ".spin{animation:sp 60s linear infinite;transform-box:fill-box;transform-origin:center}"
    ".spin2{animation:sp 12s linear infinite;transform-box:fill-box;transform-origin:center}"
    "@keyframes sp{to{transform:rotate(360deg)}}"
    ".kb{animation:kb 16s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}"
    "@keyframes kb{from{transform:scale(1)}to{transform:scale(1.09) translate(-8px,-6px)}}"
    ".bob{animation:bob 3.2s ease-in-out infinite}@keyframes bob{50%{transform:translateY(-8px)}}"
    ".grow{transform:scaleX(0);transform-box:fill-box;transform-origin:left;"
    "animation:gr 1.8s cubic-bezier(.2,.8,.2,1) forwards}@keyframes gr{to{transform:scaleX(1)}}"
    ".role{opacity:0;animation:ro 9s ease infinite}"
    "@keyframes ro{0%{opacity:0;transform:translateY(8px)}5%,30%{opacity:1;transform:none}36%,100%{opacity:0}}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}.fu,.fl,.fi{opacity:1}"
    ".grow{transform:none}.role{opacity:0}.role0{opacity:1}}"
)


def svg_open(w, h, label, extra_defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f"<style>{FONT_CSS}{CSS}</style>"
            "<defs>"
            '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" '
            'result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            '<filter id="glow2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8" '
            'result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{ICE}" '
            f'stop-opacity=".7"/><stop offset=".45" stop-color="{LINE}"/><stop offset="1" stop-color="{VIOLET}" '
            'stop-opacity=".6"/></linearGradient>'
            f'<linearGradient id="iv" x1="0" x2="1"><stop offset="0" stop-color="{ICE}"/>'
            f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient>'
            '<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
            '<circle cx="1" cy="1" r="1" fill="#ffffff" fill-opacity=".05"/></pattern>'
            f"{extra_defs}</defs>")


def T(x, y, value, size, fill, cls="", anchor="start", ls=0, delay=None, opacity=None, extra=""):
    attrs = f' class="{cls}"' if cls else ""
    if ls:
        attrs += f' letter-spacing="{ls}"'
    if delay is not None:
        attrs += f' style="animation-delay:{delay}s"'
    if opacity is not None:
        attrs += f' fill-opacity="{opacity}"'
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{attrs}{extra}>'
            f"{escape(str(value))}</text>")


def frame(w, h, glow_x, glow_y, glow_color=ICE, glow_r=380):
    """Rounded dark panel with a coloured glow, dot grid and gradient edge."""
    return (f'<radialGradient id="glowbg" cx="{glow_x / w:.3f}" cy="{glow_y / h:.3f}" r="{glow_r / w:.3f}" '
            f'gradientTransform="translate({glow_x / w:.3f} {glow_y / h:.3f}) scale(1 {w / h:.3f}) '
            f'translate({-glow_x / w:.3f} {-glow_y / h:.3f})">'
            f'<stop offset="0" stop-color="{glow_color}" stop-opacity=".16"/>'
            f'<stop offset="1" stop-color="{glow_color}" stop-opacity="0"/></radialGradient>'
            f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="{BG}"/>'
            f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="url(#glowbg)"/>'
            f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="url(#dots)"/>'
            f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="none" stroke="url(#edge)" '
            'stroke-width="1.5"/>')


def rune(name, x, y, size, color, width=1.8, opacity=1, extra=""):
    return (f'<path d="{RUNES[name]}" transform="translate({x:.1f} {y:.1f}) scale({size})" fill="none" '
            f'stroke="{color}" stroke-width="{width}" stroke-opacity="{opacity}" stroke-linecap="round" '
            f'stroke-linejoin="round" vector-effect="non-scaling-stroke"{extra}/>')


def star4(x, y, r, fill, opacity=1, cls="", delay=0):
    k = r * .28
    c = f' class="{cls}" style="animation-delay:{delay}s"' if cls else ""
    return (f'<path d="M{x} {y - r}Q{x + k} {y - k} {x + r} {y}Q{x + k} {y + k} {x} {y + r}Q{x - k} {y + k} '
            f'{x - r} {y}Q{x - k} {y - k} {x} {y - r}Z" fill="{fill}" fill-opacity="{opacity}"{c}/>')


def sparkles(seed, count, box, colors=(ICE, VIOLET, "#ffffff")):
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    out = []
    for i in range(count):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        color = rng.choice(colors)
        if i % 4 == 0:
            out.append(star4(round(x, 1), round(y, 1), rng.uniform(4, 7), color, .7, "tw", round(rng.uniform(0, 3), 1)))
        else:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rng.uniform(.8, 1.8):.1f}" fill="{color}" '
                       f'fill-opacity="{rng.uniform(.25, .7):.2f}" class="tw" '
                       f'style="animation-delay:{rng.uniform(0, 3):.1f}s"/>')
    return "".join(out)


def image(name, box, view, cls="", radius=12, clip_id=None, mask=None):
    """Artwork in a box, cropped by a viewBox in source pixels (slice keeps the box covered)."""
    path = ART / name
    x, y, w, h = box
    mime = "image/jpeg"
    href = f"data:{mime};base64,{b64(path)}"
    vx, vy, vw, vh = view
    cid = clip_id or f"clip{abs(hash((name, box))) % 99999}"
    img_cls = f' class="{cls}"' if cls else ""
    m = f' mask="url(#{mask})"' if mask else ""
    sw, sh = {"portrait.jpg": (768, 768)}.get(name, (1024, 765))
    scale = 768 / 1024 if name == "portrait.jpg" else 1
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}"/></clipPath>'
            f'<g clip-path="url(#{cid})"{m}><svg x="{x}" y="{y}" width="{w}" height="{h}" '
            f'viewBox="{vx * scale:.1f} {vy * scale:.1f} {vw * scale:.1f} {vh * scale:.1f}" '
            f'preserveAspectRatio="xMidYMid slice"><image href="{href}" width="{sw}" height="{sh}"{img_cls}/></svg></g>')


# Video for the hero frame: JPEG frames cut from the character clip, already sized to the frame box.
# The clip does not loop on its own, so it plays forward and then backward (ping-pong).
FRAMES = sorted((ART / "frames").glob("frame-*.jpg"))
FRAME_SECONDS = 1 / 6


def video_cycle():
    return max(2 * len(FRAMES) - 2, 1) * FRAME_SECONDS if FRAMES else 16


def video_frames(box):
    x, y, w, h = box
    n = len(FRAMES)
    slots = max(2 * n - 2, 1)
    key_times = ";".join(f"{k / slots:.4f}" for k in range(slots))
    parts = [f'<clipPath id="vid"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/></clipPath>'
             '<g clip-path="url(#vid)">']
    for i, path in enumerate(FRAMES):
        shown = {i, slots - i}
        values = ";".join("1" if k in shown else "0" for k in range(slots))
        parts.append(f'<image href="data:image/jpeg;base64,{b64(path)}" x="{x}" y="{y}" width="{w}" height="{h}" '
                     f'preserveAspectRatio="xMidYMid slice" opacity="{1 if i == 0 else 0}">'
                     f'<animate attributeName="opacity" values="{values}" keyTimes="{key_times}" calcMode="discrete" '
                     f'dur="{video_cycle():.2f}s" repeatCount="indefinite"/></image>')
    parts.append("</g>")
    return "".join(parts)


def icon(key, x, y, size, color):
    """Simple Icons logo (24 x 24) or a rune when the key starts with 'rune:'."""
    if key.startswith("rune:"):
        return rune(key[5:], x + size * .25, y, size, color, 2)
    return f'<path d="{ICONS[key]}" transform="translate({x} {y}) scale({size / 24:.4f})" fill="{color}"/>'


def eyebrow(x, y, label, color=ICE):
    return T(x, y, f"// {label}", 12, color, "b fu", ls=2.5, delay=.2)


# --- data --------------------------------------------------------------------

def github_data():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GH_TOKEN or GITHUB_TOKEN to build the live numbers.")
    query = """
    query($login: String!) {
      user(login: $login) {
        createdAt
        followers { totalCount }
        repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
          totalCount
          nodes {
            name stargazerCount forkCount
            defaultBranchRef { target { ... on Commit { history { totalCount } } } }
          }
        }
      }
    }"""
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if "errors" in payload:
        sys.exit(f"GitHub API error: {payload['errors']}")
    user = payload["data"]["user"]
    nodes = user["repositories"]["nodes"]

    def commits(node):
        ref = node.get("defaultBranchRef") or {}
        return ((ref.get("target") or {}).get("history") or {}).get("totalCount", 0)

    return {
        "repos": user["repositories"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in nodes),
        "forks": sum(n["forkCount"] for n in nodes),
        "followers": user["followers"]["totalCount"],
        "since": user["createdAt"][:4],
        "by_repo": {n["name"]: {"stars": n["stargazerCount"], "commits": commits(n)} for n in nodes},
        "month": dt.datetime.now(dt.timezone.utc).strftime("%b %Y").upper(),
    }


# --- sections ----------------------------------------------------------------

def hero_svg(d):
    w, h = W, 560
    defs = (f'<linearGradient id="vfade" x1="0" x2="0" y1="0" y2="1"><stop offset=".6" stop-color="{BG}" '
            f'stop-opacity="0"/><stop offset="1" stop-color="{BG}" stop-opacity=".9"/></linearGradient>'
            '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" '
            'fill="#000" fill-opacity=".18"/></pattern>')
    p = [svg_open(w, h, f"Hi, I'm Berke Arda Türk. {ROLES[0]}. {MOTTO}", defs), frame(w, h, 240, 140)]
    # Rune circle watermark.
    p.append(f'<g class="spin" opacity=".07"><circle cx="330" cy="330" r="190" fill="none" stroke="{ICE}" '
             f'stroke-width="2"/><circle cx="330" cy="330" r="150" fill="none" stroke="{ICE}" stroke-dasharray="4 10"/>'
             + "".join(rune(n, 330 + 168 * math.cos(i / 12 * 6.283) - 6,
                            330 + 168 * math.sin(i / 12 * 6.283) - 12, 24, ICE, 2)
                       for i, n in enumerate(["algiz", "berkano", "ansuz", "kenaz", "raidho", "sowilo",
                                              "tiwaz", "ehwaz", "mannaz", "laguz", "dagaz", "othala"]))
             + "</g>")
    p.append(sparkles(3, 26, (30, 30, 690, 530)))
    # Terminal line that types itself.
    prompt = "mage@vizja:~$ summon --profile"
    p.append(f'<clipPath id="type"><rect x="52" y="48" width="0" height="26"><animate attributeName="width" '
             f'from="0" to="{len(prompt) * 8.4 + 4}" begin=".2s" dur="1.6s" fill="freeze"/></rect></clipPath>')
    p.append(f'<g clip-path="url(#type)"><text x="52" y="66" font-size="14">'
             f'<tspan fill="{GREEN}" class="b">mage@vizja</tspan><tspan fill="{MUTED}">:~$ </tspan>'
             f'<tspan fill="{INK}">summon </tspan><tspan fill="{VIOLET}">--profile</tspan></text></g>')
    p.append(f'<rect x="{52 + len(prompt) * 8.4 + 8}" y="52" width="9" height="18" fill="{GREEN}" class="blink"/>')
    # Greeting, name and roles.
    p.append(T(52, 150, "Hi, I'm", 28, INK, "b fu", delay=.9))
    p.append(f'<g filter="url(#glow)">{T(50, 232, "Berke Arda Türk", 64, "url(#iv)", "x fu", delay=1.2)}</g>')
    p.append(f'<rect x="52" y="252" width="150" height="4" rx="2" fill="url(#iv)" class="grow" '
             'style="animation-delay:1.6s"/>')
    p.append(f'<g class="fu" style="animation-delay:1.9s"><circle cx="62" cy="298" r="9" fill="none" stroke="{ICE}" '
             f'stroke-width="2"/>{rune("berkano", 58, 291, 14, ICE, 1.6)}</g>')
    for i, role in enumerate(ROLES):
        p.append(T(82, 305, role, 20, INK, f"b role role{i}", extra=f' style="animation-delay:{2 + i * 3}s"'))
    p.append(T(52, 348, "Turning messy real-world data into honest answers,", 16, MUTED, "fu", delay=2.2))
    p.append(T(52, 372, "one leak-free model at a time.", 16, MUTED, "fu", delay=2.3))
    # Stat boxes.
    boxes = [(d["repos"], "REPOS"), (d["stars"], "STARS"), (d["followers"], "FOLLOWERS")]
    x = 52
    for i, (value, label) in enumerate(boxes):
        p.append(f'<g class="fu" style="animation-delay:{2.5 + i * .15}s"><rect x="{x}" y="398" width="112" '
                 f'height="64" rx="10" fill="{PANEL}" stroke="{LINE}"/>'
                 + T(x + 14, 430, value, 24, ICE, "x") + T(x + 14, 450, label, 9.5, DIM, "b", ls=1.5) + "</g>")
        x += 124
    p.append(f'<g class="fu" style="animation-delay:3s"><rect x="{x}" y="398" width="150" height="64" rx="10" '
             f'fill="{GREEN}" fill-opacity=".08" stroke="{GREEN}" stroke-opacity=".55"/>'
             f'<circle cx="{x + 20}" cy="422" r="4.5" fill="{GREEN}" class="pulse"/>'
             + T(x + 32, 426, "OPEN TO", 11, GREEN, "b", ls=1.5) + T(x + 32, 444, "WORK", 11, GREEN, "b", ls=1.5)
             + "</g>")
    p.append(T(52, 506, "MOTTO ·", 11.5, DIM, "b fu", ls=1.5, delay=3.2))
    p.append(T(130, 506, MOTTO, 11.5, VIOLET, "fu", delay=3.3))
    # Video frame with the portrait.
    fx, fy, fw, fh = 704, 40, 524, 480
    p.append(f'<g class="fi" style="animation-delay:.4s">'
             + (video_frames((fx, fy, fw, fh)) if FRAMES else
                image("portrait.jpg", (fx, fy, fw, fh), (90, 40, 880, 806), cls="kb", radius=10, clip_id="vid"))
             + f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="10" fill="url(#vfade)"/>'
             + f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="10" fill="url(#scan)"/></g>')
    for cx, cy, sx, sy in ((fx - 10, fy - 10, 1, 1), (fx + fw + 10, fy - 10, -1, 1),
                           (fx - 10, fy + fh + 10, 1, -1), (fx + fw + 10, fy + fh + 10, -1, -1)):
        p.append(f'<path d="M{cx} {cy + 26 * sy}V{cy}H{cx + 26 * sx}" fill="none" stroke="{ICE}" stroke-width="2.5"/>')
    p.append(star4(fx + fw - 34, fy + 40, 11, ICE, .9, "spin2"))
    p.append(T(fx + 26, fy + fh - 30, "MAGE.MP4", 11, INK, "b", ls=2.5))
    cycle = video_cycle()
    p.append(T(fx + fw - 26, fy + fh - 30, f"VIZJA · 00:{round(cycle):02d}", 11, MUTED, "b", anchor="end", ls=1.5))
    p.append(f'<rect x="{fx + 26}" y="{fy + fh - 18}" width="{fw - 52}" height="3" rx="1.5" fill="#ffffff" '
             f'fill-opacity=".15"/><rect x="{fx + 26}" y="{fy + fh - 18}" width="0" height="3" rx="1.5" '
             f'fill="url(#iv)"><animate attributeName="width" from="0" to="{fw - 52}" dur="{cycle:.2f}s" '
             'repeatCount="indefinite"/></rect>')
    p.append("</svg>")
    return "".join(p)


def familiar_svg():
    """Small animated companion under the hero: the face medallion with orbiting runes."""
    w, h = 260, 150
    p = [svg_open(w, h, "My familiar: a floating rune medallion")]
    p.append(f'<ellipse cx="130" cy="138" rx="46" ry="6" fill="{ICE}" fill-opacity=".18" class="pulse"/>')
    p.append('<g class="bob">')
    p.append(f'<circle cx="130" cy="66" r="56" fill="none" stroke="{ICE}" stroke-opacity=".35" stroke-dasharray="3 7" '
             'class="spin2"/>')
    p.append(image("portrait.jpg", (86, 22, 88, 88), (300, 150, 450, 450), radius=44, clip_id="fam"))
    p.append(f'<circle cx="130" cy="66" r="44" fill="none" stroke="{ICE}" stroke-width="2" filter="url(#glow)"/>')
    p.append("</g>")
    for i, (name, x, y, delay) in enumerate((("algiz", 28, 50, 0), ("kenaz", 216, 36, .8), ("raidho", 222, 96, 1.6),
                                             ("ansuz", 22, 104, 2.4))):
        p.append(f'<g class="bob" style="animation-delay:{delay}s" filter="url(#glow)">'
                 f'{rune(name, x, y, 18, ICE if i % 2 == 0 else VIOLET, 2)}</g>')
    p.append(sparkles(8, 10, (10, 10, 250, 140)))
    p.append("</svg>")
    return "".join(p)


def way_svg(d):
    w, h = W, 520
    p = [svg_open(w, h, "My mage way: " + ". ".join(f"{a}: {b}" for _, a, b in WAY)), frame(w, h, 260, 260)]
    p.append(f'<g class="fl">{image("scene-path.jpg", (40, 40, 440, 440), (140, 0, 765, 765), radius=14, clip_id="wayimg")}'
             f'<rect x="40" y="40" width="440" height="440" rx="14" fill="none" stroke="{ICE}" stroke-opacity=".35"/></g>')
    x = 530
    p.append(eyebrow(x, 96, "MY MAGE WAY"))
    p.append(T(x, 140, "Find the answer, then ship it", 32, INK, "x fu", delay=.35))
    p.append(T(x, 172, "CS student at Vizja by day, data mage by night.", 14.5, MUTED, "fu", delay=.5))
    for i, (sigil, title, desc) in enumerate(WAY):
        y = 204 + i * 68
        p.append(f'<g class="fu" style="animation-delay:{.7 + i * .2}s">'
                 f'<rect x="{x}" y="{y}" width="44" height="44" rx="10" fill="{ICE}" fill-opacity=".08" stroke="{ICE}" '
                 f'stroke-opacity=".35"/>{rune(sigil, x + 15.5, y + 11, 22, ICE, 2)}'
                 + T(x + 62, y + 19, title, 16, INK, "b") + T(x + 62, y + 39, desc, 12, MUTED) + "</g>")
    p.append(f'<g class="fu" style="animation-delay:1.4s"><rect x="{x}" y="414" width="{w - 40 - x}" height="66" rx="10" '
             f'fill="{PANEL2}" stroke="{LINE}"/><rect x="{x}" y="414" width="4" height="66" rx="2" fill="url(#iv)"/>'
             + T(x + 24, 442, f"“{MOTTO}”", 16, INK, "b")
             + T(x + 24, 464, f"MOTTO · {d['repos']} REPOS · {d['stars']} STARS · {d['followers']} FOLLOWERS",
                 10.5, DIM, "b", ls=1.5)
             + star4(w - 70, 446, 9, VIOLET, .9, "tw") + "</g>")
    p.append(sparkles(11, 14, (500, 30, 1250, 500)))
    p.append("</svg>")
    return "".join(p)


def spells_svg():
    w, h = W, 500
    defs = (f'<radialGradient id="pfade" cx=".5" cy=".42" r=".62"><stop offset=".55" stop-color="#fff"/>'
            '<stop offset="1" stop-color="#000"/></radialGradient>'
            '<mask id="pmask"><rect x="20" y="30" width="360" height="450" fill="url(#pfade)"/></mask>'
            f'<linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="{ICE}" stop-opacity=".55"/>'
            f'<stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>')
    p = [svg_open(w, h, "Spell arsenal, tools I cast with: " + ", ".join(s[0] for s in SPELLS), defs),
         frame(w, h, 260, 280)]
    # The portrait's rune circle sits at about (785, 610) in source pixels; the crop maps it to (270, 283).
    p.append(f'<polygon points="270,283 1250,120 1250,470" fill="url(#beam)" class="pulse"/>')
    p.append(f'<g class="fl">{image("portrait.jpg", (20, 30, 360, 450), (200, 40, 820, 1025), radius=0, clip_id="spimg", mask="pmask")}</g>')
    p.append(f'<circle cx="270" cy="283" r="16" fill="{ICE}" fill-opacity=".5" filter="url(#glow2)" class="pulse"/>')
    p.append(eyebrow(400, 74, "SPELL ARSENAL"))
    p.append(T(400, 116, "Tools I cast with", 32, INK, "x fu", delay=.35))
    p.append(T(w - 40, 74, f"{len(SPELLS)} SPELLS LEARNED", 11, DIM, "b fu", anchor="end", ls=2, delay=.4))
    tw, th, gap = 158, 52, 10
    for i, (label, key, color) in enumerate(SPELLS):
        r, c = divmod(i, 5)
        x, y = 400 + c * (tw + gap), 160 + r * 92
        p.append(f'<g class="fu" style="animation-delay:{.6 + i * .06:.2f}s">'
                 f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="10" fill="{color}" fill-opacity=".10" '
                 f'stroke="{color}" stroke-opacity=".5"/>{icon(key, x + 16, y + 15, 22, color)}'
                 + T(x + 48, y + 31, label, 13, INK, "b") + "</g>")
    p.append(sparkles(21, 16, (390, 130, 1250, 480)))
    p.append("</svg>")
    return "".join(p)


def id_svg(d):
    w, h = W, 620
    defs = (f'<linearGradient id="card" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1b2540"/>'
            f'<stop offset="1" stop-color="#0e1422"/></linearGradient>'
            f'<linearGradient id="strap" x1="0" x2="1"><stop offset="0" stop-color="{ICE2}"/>'
            f'<stop offset="1" stop-color="#1d4ed8"/></linearGradient>')
    p = [svg_open(w, h, f"Mage registration card for Berke Arda Türk and a live dashboard: {d['repos']} public repos, "
                        f"{d['stars']} stars, {d['forks']} forks, {d['followers']} followers", defs),
         frame(w, h, 200, 320)]
    # Lanyard and card, swinging gently from the top.
    p.append('<g style="animation:sw 6s ease-in-out infinite;transform-origin:200px 0px">'
             "<style>@keyframes sw{0%,100%{transform:rotate(-1.4deg)}50%{transform:rotate(1.4deg)}}</style>")
    p.append(f'<rect x="186" y="0" width="28" height="112" fill="url(#strap)"/>')
    p.append(T(205, 10, "VIZJA · DATA MAGE · VIZJA", 9, "#ffffff", "b", ls=2, opacity=.8,
               extra=' transform="rotate(90 205 10)"'))
    p.append(f'<rect x="178" y="104" width="44" height="24" rx="6" fill="#9aa4b2"/><rect x="192" y="122" width="16" '
             f'height="16" rx="3" fill="none" stroke="#9aa4b2" stroke-width="3"/>')
    cx0, cy0, cw, ch = 40, 136, 320, 456
    p.append(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="18" fill="url(#card)" stroke="{ICE}" '
             f'stroke-opacity=".4" stroke-width="1.5"/>')
    p.append(f'<rect x="185" y="{cy0 + 10}" width="30" height="6" rx="3" fill="{BG}"/>')
    p.append(T(cx0 + 20, cy0 + 40, "◆ MAGE REGISTRATION", 10.5, ICE, "b", ls=1.5))
    p.append(T(cx0 + cw - 20, cy0 + 40, "No. 0021", 10.5, DIM, "b", anchor="end"))
    p.append(image("portrait.jpg", (110, cy0 + 58, 180, 180), (300, 150, 450, 450), radius=16, clip_id="idface"))
    p.append(f'<rect x="110" y="{cy0 + 58}" width="180" height="180" rx="16" fill="none" stroke="{ICE}" stroke-width="2"/>')
    p.append(f'<g transform="rotate(-14 300 {cy0 + 84})"><circle cx="300" cy="{cy0 + 84}" r="30" fill="{BG}" '
             f'fill-opacity=".6" stroke="{VIOLET}" stroke-width="2" stroke-dasharray="3 3"/>'
             + T(300, cy0 + 80, "LVL", 9, VIOLET, "b", anchor="middle", ls=1.5)
             + T(300, cy0 + 98, "6", 18, VIOLET, "x", anchor="middle") + "</g>")
    p.append(T(200, cy0 + 270, "Berke Arda Türk", 21, INK, "x", anchor="middle"))
    p.append(T(200, cy0 + 290, "DATA MAGE · APPRENTICE", 10, ICE, "b", anchor="middle", ls=2))
    fields = [("TOWER", "Vizja Univ."), ("SCHOOL", "AI & Data Sci."), ("SINCE", d["since"]), ("SEMESTER", "6th")]
    for i, (label, value) in enumerate(fields):
        fx = cx0 + 24 + (i % 2) * 150
        fy = cy0 + 322 + (i // 2) * 40
        p.append(T(fx, fy, label, 8.5, DIM, "b", ls=1.5) + T(fx, fy + 17, value, 12, INK, "b"))
    rng = random.Random(21)
    x = cx0 + 24
    bars = []
    while x < cx0 + 196:
        bw = rng.choice((1, 1, 2, 3))
        bars.append(f'<rect x="{x}" y="{cy0 + 396}" width="{bw}" height="24" fill="{INK}" fill-opacity=".75"/>')
        x += bw + rng.choice((1, 2, 2, 3))
    p.append("".join(bars))
    p.append(f'<circle cx="{cx0 + 28}" cy="{cy0 + 438}" r="4" fill="{GREEN}" class="pulse"/>')
    p.append(T(cx0 + 38, cy0 + 442, "ACTIVE QUEST", 9.5, GREEN, "b", ls=1.5))
    p.append(T(cx0 + cw - 20, cy0 + 442, f"@{USER}", 9.5, DIM, "b", anchor="end"))
    p.append("</g>")
    # Dashboard.
    x = 420
    p.append(eyebrow(x, 84, "QUEST DASHBOARD"))
    p.append(T(x, 126, "Stats from the tower", 32, INK, "x fu", delay=.35))
    p.append(f'<g class="fu" style="animation-delay:.5s"><rect x="{w - 40 - 168}" y="66" width="168" height="28" rx="14" '
             f'fill="{GREEN}" fill-opacity=".1" stroke="{GREEN}" stroke-opacity=".6"/>'
             f'<circle cx="{w - 40 - 150}" cy="80" r="4" fill="{GREEN}" class="pulse"/>'
             + T(w - 40 - 138, 84, f"LIVE · {d['month']}", 10.5, GREEN, "b", ls=1.5) + "</g>")
    tiles = [(d["repos"], "PUBLIC REPOS", ICE, "repo"), (d["stars"], "STARS EARNED", GOLD, "star"),
             (d["forks"], "FORKS", VIOLET, "fork"), (d["followers"], "FOLLOWERS", GREEN, "person")]
    tw = (w - 40 - x - 3 * 16) / 4
    for i, (value, label, color, ic) in enumerate(tiles):
        tx = x + i * (tw + 16)
        p.append(f'<g class="fu" style="animation-delay:{.6 + i * .12:.2f}s">'
                 f'<rect x="{tx:.1f}" y="152" width="{tw:.1f}" height="96" rx="12" fill="{PANEL}" stroke="{LINE}"/>'
                 f'<rect x="{tx + 18:.1f}" y="168" width="24" height="3" rx="1.5" fill="{color}"/>'
                 f'<path d="{OCT[ic]}" transform="translate({tx + tw - 38:.1f} 166) scale(1.15)" fill="{color}"/>'
                 + T(round(tx + 18, 1), 216, value, 32, INK, "x") + T(round(tx + 18, 1), 236, label, 9.5, DIM, "b", ls=1.5)
                 + "</g>")
    # Commits per featured repo.
    px, py, pw, ph = x, 268, 500, 312
    p.append(f'<g class="fu" style="animation-delay:1.1s"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="12" '
             f'fill="{PANEL}" stroke="{LINE}"/>' + T(px + 22, py + 32, "TOP QUESTS · COMMITS", 10.5, DIM, "b", ls=1.5))
    rows = [(title, d["by_repo"].get(repo, {}).get("commits", 0)) for repo, title, _, _ in FEATURED]
    top = max([c for _, c in rows] + [1])
    for i, (title, commits) in enumerate(rows):
        y = py + 66 + i * 38
        bw = 220 * commits / top
        p.append(T(px + 22, y + 4, title[:20], 11.5, MUTED, "b"))
        p.append(f'<rect x="{px + 196}" y="{y - 5}" width="220" height="9" rx="4.5" fill="#ffffff" fill-opacity=".06"/>')
        if bw:
            p.append(f'<rect x="{px + 196}" y="{y - 5}" width="{bw:.1f}" height="9" rx="4.5" fill="url(#iv)" class="grow" '
                     f'style="animation-delay:{1.3 + i * .1:.1f}s"/>')
        p.append(T(px + 430, y + 4, commits, 11.5, INK, "b"))
    p.append(T(px + 22, py + ph - 20, "live from the GitHub API · rebuilt every day", 9.5, DIM, extra=' font-style="italic"'))
    p.append("</g>")
    # Mana nature.
    mx, mw = px + pw + 16, w - 40 - (px + pw + 16)
    p.append(f'<g class="fu" style="animation-delay:1.3s"><rect x="{mx}" y="{py}" width="{mw}" height="{ph}" rx="12" '
             f'fill="{PANEL}" stroke="{LINE}"/>' + T(mx + 22, py + 32, "MANA NATURE", 10.5, DIM, "b", ls=1.5))
    for i, (color, label, value, sub) in enumerate(MANA):
        y = py + 72 + i * 80
        p.append(f'<circle cx="{mx + 26}" cy="{y - 4}" r="4" fill="{color}"/>'
                 + T(mx + 38, y, label, 10.5, color, "b", ls=1.5)
                 + T(mx + 22, y + 24, value, 14, INK, "b") + T(mx + 22, y + 44, sub, 10.5, MUTED))
    p.append("</g>")
    p.append(sparkles(31, 12, (400, 40, 1250, 600)))
    p.append("</svg>")
    return "".join(p)


def connect_svg():
    w, h = W, 440
    p = [svg_open(w, h, "Let's connect: " + ", ".join(f"{label} {handle}" for _, _, label, handle in CONTACTS)),
         frame(w, h, 300, 220, VIOLET)]
    p.append(f'<g class="fl">{image("scene-raven.jpg", (40, 40, 520, 360), (40, 0, 1024, 680), radius=14, clip_id="rav")}'
             f'<rect x="40" y="40" width="520" height="360" rx="14" fill="none" stroke="{VIOLET}" stroke-opacity=".4"/></g>')
    x = 604
    p.append(eyebrow(x, 96, "JOIN THE GUILD", VIOLET))
    p.append(T(x, 138, "Let's build something honest", 30, INK, "x fu", delay=.35))
    tw, th = (w - 40 - x - 16) / 2, 74
    for i, (key, color, label, handle) in enumerate(CONTACTS):
        tx, ty = x + (i % 2) * (tw + 16), 168 + (i // 2) * (th + 14)
        p.append(f'<g class="fu" style="animation-delay:{.6 + i * .15:.2f}s">'
                 f'<rect x="{tx:.1f}" y="{ty}" width="{tw:.1f}" height="{th}" rx="12" fill="{PANEL}" stroke="{LINE}"/>'
                 f'<rect x="{tx + 16:.1f}" y="{ty + 15}" width="44" height="44" rx="10" fill="{color}" '
                 f'fill-opacity=".14"/>{icon(key, round(tx + 27, 1), ty + 26, 22, color)}'
                 + T(round(tx + 76, 1), ty + 33, label, 14, INK, "b") + T(round(tx + 76, 1), ty + 53, handle, 11, MUTED)
                 + "</g>")
    p.append(f'<circle cx="{x + 5}" cy="370" r="4" fill="{GREEN}" class="pulse"/>')
    p.append(T(x + 18, 374, "Open to internships, collaborations and data roles", 11.5, MUTED, "fu", delay=1.4))
    p.append(sparkles(41, 14, (580, 30, 1250, 410), (VIOLET, ICE, "#ffffff")))
    p.append("</svg>")
    return "".join(p)


def orb_svg():
    """Small spinning rune orb between the quest table and the contribution realm."""
    w = h = 150
    p = [svg_open(w, h, "A spinning rune orb")]
    p.append(f'<circle cx="75" cy="75" r="30" fill="{ICE}" fill-opacity=".35" filter="url(#glow2)" class="pulse"/>')
    p.append(f'<circle cx="75" cy="75" r="16" fill="#ffffff" fill-opacity=".85" filter="url(#glow)"/>')
    ring = "".join(rune(n, 75 + 52 * math.cos(i / 8 * 6.283) - 4,
                        75 + 52 * math.sin(i / 8 * 6.283) - 8, 16, ICE, 1.8)
                   for i, n in enumerate(["berkano", "algiz", "kenaz", "ansuz", "raidho", "sowilo", "tiwaz", "dagaz"]))
    p.append(f'<g class="spin2" filter="url(#glow)"><circle cx="75" cy="75" r="62" fill="none" stroke="{ICE}" '
             f'stroke-opacity=".55" stroke-width="1.5"/><circle cx="75" cy="75" r="42" fill="none" stroke="{VIOLET}" '
             f'stroke-opacity=".5" stroke-dasharray="3 6"/>{ring}</g>')
    p.append(sparkles(51, 8, (5, 5, 145, 145)))
    p.append("</svg>")
    return "".join(p)


def sigil_svg():
    """Tiny pulsing seal at the very end, with the B rune."""
    w = h = 90
    p = [svg_open(w, h, "A glowing B rune seal")]
    p.append(f'<g class="bob"><circle cx="45" cy="42" r="26" fill="{PANEL}" stroke="{ICE}" stroke-width="2" '
             f'filter="url(#glow)"/>{rune("berkano", 37, 26, 32, ICE, 2.4)}</g>')
    p.append(f'<ellipse cx="45" cy="82" rx="20" ry="4" fill="{ICE}" fill-opacity=".2" class="pulse"/>')
    p.append("</svg>")
    return "".join(p)


def quests_block(d):
    rows = []
    for repo, title, what, tags in FEATURED:
        stars = d["by_repo"].get(repo, {}).get("stars", 0)
        code = " ".join(f"<code>{escape(t)}</code>" for t in tags)
        rows.append(f'<tr><td><a href="https://github.com/{USER}/{repo}"><b>{escape(title)}</b></a></td>'
                    f"<td>{escape(what)}</td><td>{code}</td><td align=\"center\"><b>{stars}</b></td></tr>")
    return ("<table>\n<tr><th>Quest</th><th>What it is</th><th>Spells used</th><th align=\"center\">⭐</th></tr>\n"
            + "\n".join(rows) + "\n</table>\n\n<div align=\"center\">\n\n"
            f'<a href="https://github.com/{USER}?tab=repositories"><b>→ See all {d["repos"]} repositories</b></a>')


def update_readme(d):
    readme = ROOT / "README.md"
    content = readme.read_text(encoding="utf-8")
    block = f"<!-- QUESTS:START -->\n{quests_block(d)}\n<!-- QUESTS:END -->"
    content = re.sub(r"<!-- QUESTS:START -->.*?<!-- QUESTS:END -->", lambda _: block, content, flags=re.S)
    readme.write_text(content, encoding="utf-8", newline="\n")


def main():
    d = github_data()
    outputs = {
        "hero": hero_svg(d), "familiar": familiar_svg(), "mage-way": way_svg(d), "spell-stack": spells_svg(),
        "mage-id": id_svg(d), "connect": connect_svg(), "orb": orb_svg(), "sigil": sigil_svg(),
    }
    for name, svg in outputs.items():
        (ASSETS / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    update_readme(d)
    print("profile assets written:", ", ".join(outputs))


if __name__ == "__main__":
    main()
