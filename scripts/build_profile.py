"""Build the profile README assets.

Writes light and dark SVGs for the header, project cards, toolkit and divider,
and refreshes the "Latest writing" list in README.md from Medium.
The look follows the profile portrait: a data mage theme with a midnight sky,
ice blue glow, floating runes and a rune circle around a small neural network.
The dark theme is the night sky; the light theme is parchment with ink blue.
Runes are drawn as SVG paths (no font needed), so they render everywhere.
Standard library only. Needs a GitHub token in GH_TOKEN or GITHUB_TOKEN for
the star counts and languages on the project cards (the GitHub Action passes
its own token).

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
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

USER = "BerkeArdaTurk21"
MEDIUM_FEED = "https://medium.com/feed/@berkeardaturk"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
# Artwork is embedded into the SVGs as base64, because GitHub shows README SVGs as images
# and an SVG shown as an image cannot load other files.
ART = ASSETS / "art"
PORTRAIT = "portrait.jpg"  # square portrait; crops below are in 1024 x 1024 source units
PORTRAIT_UNITS = 1024
CROP_HERO = (150, 50, 850, 940)    # hood, face, hand and rune circle
CROP_FACE = (300, 150, 450, 450)   # face for the guild card medallion
CROP_SIGIL = (560, 430, 440, 520)  # hand with the glowing rune circle
# Optional scene paintings: drop a JPEG with this name into assets/art and it replaces the portrait crop.
SCENE_PATH = "scene-path.jpg"
SCENE_RAVEN = "scene-raven.jpg"

# Dark: midnight sky with the ice blue of berkeardaturk.com. Light: parchment with ink blue.
THEMES = {
    "dark": {
        "card": "#0d1525", "inset": "#08101d", "line": "#22314a", "axis": "#3a4a66",
        "ink": "#e8f1fb", "muted": "#93a3b8", "signal": "#7dd3fc",
        "sky_center": "#173352", "sky_edge": "#0a1222", "star": "#cfe9ff", "glow": True,
    },
    "light": {
        "card": "#f8f2e4", "inset": "#fffaf0", "line": "#dccfb2", "axis": "#b9a983",
        "ink": "#2b2416", "muted": "#6b5d45", "signal": "#0b5f80",
        "sky_center": "#fdf8ec", "sky_edge": "#f0e6cf", "star": "#a8946a", "glow": False,
    },
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
SERIF = "'Palatino Linotype', 'Book Antiqua', Palatino, Georgia, 'Times New Roman', serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

# Elder Futhark runes as stroke paths in a unit box (about 0.5 wide, 1 tall).
RUNES = {
    "fehu": "M0 0V1M0 .3L.45 .05M0 .55L.45 .3",
    "uruz": "M0 1V0L.5 .3V1",
    "thurisaz": "M0 0V1M0 .25L.4 .5L0 .75",
    "ansuz": "M0 0V1M0 0L.45 .25M0 .3L.45 .55",
    "raidho": "M0 1V0L.45 .25L0 .5L.45 1",
    "kenaz": "M.45 .15L0 .5L.45 .85",
    "gebo": "M0 0L.5 1M.5 0L0 1",
    "isa": "M.25 0V1",
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
# "BERKE ARDA TURK" spelled in runes; None marks a word break.
NAME_RUNES = ["berkano", "ehwaz", "raidho", "kenaz", "ehwaz", None,
              "ansuz", "raidho", "dagaz", "ansuz", None,
              "tiwaz", "uruz", "raidho", "kenaz", None]

# Featured projects, in the same order as the pinned repos. Metrics come from each repo's README.
# Each card carries a rune that fits the project.
FEATURED = [
    {"repo": "foldsafe", "title": "foldsafe", "rune": "algiz",  # protection
     "desc": "Static analyzer and agent skill that catch data leakage in ML code before cross-validation scores mislead you.",
     "metric": "Pre-alpha · 8 rules planned", "tags": ["static analysis", "agent skill"]},
    {"repo": "kaggle-titanic", "title": "Kaggle Titanic", "rune": "laguz",  # water
     "desc": "End-to-end tabular ML: leak-free scikit-learn pipelines, nested cross-validation and a group survival feature.",
     "metric": "Kaggle 0.794 · CV 0.841", "tags": ["scikit-learn", "XGBoost"]},
    {"repo": "customer-churn-shap-dashboard", "title": "Churn SHAP Dashboard", "rune": "kenaz",  # torch, insight
     "desc": "XGBoost churn model with a SHAP explanation for every prediction, served as a Streamlit app.",
     "metric": "ROC-AUC 0.84 · recall 79%", "tags": ["XGBoost", "SHAP"]},
    {"repo": "Stock-Sentiment-Predictor", "title": "Stock Sentiment", "rune": "fehu",  # wealth
     "desc": "Three-class sentiment on 4,846 financial news headlines with TF-IDF and LinearSVC, plus a Streamlit app.",
     "metric": "74.5% accuracy · baseline 59.4%", "tags": ["NLP", "scikit-learn"]},
    {"repo": "EconoScope", "title": "EconoScope", "rune": "dagaz",  # day, the passing of time
     "desc": "Exploratory analysis of inflation in 212 countries: five measures, country comparisons and crisis periods.",
     "metric": "212 countries · 1970-2022", "tags": ["EDA", "pandas"]},
    {"repo": "Python-RoadMap", "title": "Python RoadMap", "rune": "raidho",  # journey
     "desc": "Eight weeks of daily Python lessons with quizzes and exercises, plus four standard-library projects.",
     "metric": "63 lessons · 4 projects", "tags": ["Python", "learning"]},
]

TOOLKIT = [
    ("Languages", "ansuz", ["Python", "SQL", "TypeScript", "Java"]),
    ("Machine learning", "kenaz", ["scikit-learn", "XGBoost", "SHAP", "PyTorch (learning)"]),
    ("Data & analysis", "sowilo", ["pandas", "NumPy", "Matplotlib", "Seaborn", "Jupyter"]),
    ("Big data & databases", "ingwaz", ["PySpark", "MySQL", "SQLite"]),
    ("Apps & engineering", "tiwaz", ["Streamlit", "React", "Tailwind", "Git"]),
]

PATH_ITEMS = [
    ("algiz", "Guarding models against leakage",
     "Building foldsafe, an open-source checker that flags data leakage before cross-validation scores mislead you."),
    ("kenaz", "Explaining every prediction",
     "A simple baseline first, then models whose decisions I can show with SHAP and plain words."),
    ("raidho", "Taming big data",
     "Distributed data processing with Apache Spark and PySpark in a university team project."),
]

# Static milestones, newest first. No live counters on purpose.
QUEST_LOG = [
    ("Oct 2026", "Raised my own tower: berkeardaturk.com"),
    ("Oct 2026", "Began foldsafe, a guard against data leakage"),
    ("Oct 2026", "First Kaggle quest: Titanic, score 0.794"),
    ("May 2026", "Explained churn predictions with SHAP"),
    ("May 2026", "Read 50 years of inflation in 212 countries"),
]

GUILD_FIELDS = [
    ("NAME", "Berke Arda Türk"),
    ("RANK", "Apprentice Data Mage"),
    ("GUILD", "Vizja University · Computer Science"),
    ("SCHOOL", "Artificial Intelligence & Data Science"),
    ("CURRENT QUEST", "foldsafe"),
]

STAR_PATH = ("M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97"
             ".719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194"
             "L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z")

ANIMATIONS = (
    "<style>"
    ".flow{animation:flow 1.4s linear infinite}@keyframes flow{to{stroke-dashoffset:-10}}"
    ".spin{animation:spin 120s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}"
    ".tw{animation:tw 3.2s ease-in-out infinite}@keyframes tw{50%{opacity:.15}}"
    ".drift{animation:drift 7s ease-in-out infinite}@keyframes drift{50%{transform:translateY(-6px)}}"
    "@media (prefers-reduced-motion:reduce){.flow,.spin,.tw,.drift{animation:none}}"
    "</style>"
)


# --- helpers -----------------------------------------------------------------

def svg_open(width, height, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title>')


def defs(t, extra=""):
    """Glow filter (dark theme only) plus any extra gradient definitions."""
    glow = ('<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
            '<feGaussianBlur stdDeviation="2.2" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    return f"<defs>{glow if t['glow'] else ''}{extra}</defs>"


def glow_attr(t):
    return ' filter="url(#glow)"' if t["glow"] else ""


def framed_panel(width, height, t, fill=None):
    """Card with an inner frame and small diamond ornaments in the corners."""
    parts = [f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="7" '
             f'fill="{fill or t["card"]}" stroke="{t["line"]}"/>',
             f'<rect x="6.5" y="6.5" width="{width - 13}" height="{height - 13}" rx="3" '
             f'fill="none" stroke="{t["line"]}" stroke-opacity=".7"/>']
    for x, y in ((6.5, 6.5), (width - 6.5, 6.5), (6.5, height - 6.5), (width - 6.5, height - 6.5)):
        parts.append(diamond(x, y, 3.2, t["signal"]))
    return "".join(parts)


def diamond(x, y, r, fill, opacity=1):
    return (f'<path d="M{x} {y - r}L{x + r} {y}L{x} {y + r}L{x - r} {y}Z" fill="{fill}" '
            f'fill-opacity="{opacity}"/>')


def star4(x, y, r, fill, opacity=1):
    """Four-pointed sparkle."""
    k = r * 0.28
    return (f'<path d="M{x} {y - r}Q{x + k} {y - k} {x + r} {y}Q{x + k} {y + k} {x} {y + r}'
            f'Q{x - k} {y + k} {x - r} {y}Q{x - k} {y - k} {x} {y - r}Z" fill="{fill}" fill-opacity="{opacity}"/>')


def rune(name, x, y, size, color, width=1.6, opacity=1, extra=""):
    """Draw one rune; (x, y) is its top-left corner and size its height."""
    return (f'<path d="{RUNES[name]}" transform="translate({x:.1f} {y:.1f}) scale({size})" fill="none" '
            f'stroke="{color}" stroke-width="{width}" stroke-opacity="{opacity}" stroke-linecap="round" '
            f'stroke-linejoin="round" vector-effect="non-scaling-stroke"{extra}/>')


def text(x, y, value, size, fill, family=SANS, weight=400, anchor="start", spacing=0, style=""):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
    extra += f' font-style="{style}"' if style else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{escape(str(value))}</text>')


def wrap(value, max_chars):
    lines, line = [], ""
    for word in value.split():
        if line and len(line) + 1 + len(word) > max_chars:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def chip(x, y, label, t, size=11):
    width = round(len(label) * size * 0.6 + 20)
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{size + 11}" rx="{(size + 11) / 2}" '
            f'fill="{t["inset"]}" stroke="{t["signal"]}" stroke-opacity=".35"/>'
            + text(x + width / 2, y + size + 4, label, size, t["ink"], MONO, anchor="middle")), width


def art_href(name):
    path = ART / name
    if not path.exists():
        return None
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def arch_d(x, y, w, h):
    r = w / 2
    return f"M{x} {y + h}V{y + r}A{r} {r} 0 0 1 {x + w} {y + r}V{y + h}Z"


def circle_d(cx, cy, r):
    return f"M{cx - r} {cy}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0Z"


def framed_art(clip_id, shape, box, t, scene=None, crop=CROP_HERO):
    """Artwork clipped to a shape with a glowing outline.

    Uses the scene painting when it exists (scaled to cover the box), otherwise a crop of the portrait.
    """
    x, y, w, h = box
    href = art_href(scene) if scene else None
    if href:
        image = (f'<image href="{href}" x="{x}" y="{y}" width="{w}" height="{h}" '
                 f'preserveAspectRatio="xMidYMid slice" clip-path="url(#{clip_id})"/>')
    else:
        cx0, cy0, cw, ch = crop
        s = max(w / cw, h / ch)
        ix = x - cx0 * s - (cw * s - w) / 2
        iy = y - cy0 * s - (ch * s - h) / 2
        size = PORTRAIT_UNITS * s
        image = (f'<image href="{art_href(PORTRAIT)}" x="{ix:.1f}" y="{iy:.1f}" width="{size:.1f}" '
                 f'height="{size:.1f}" preserveAspectRatio="none" clip-path="url(#{clip_id})"/>')
    return "".join([
        f'<clipPath id="{clip_id}"><path d="{shape}"/></clipPath>',
        f'<path d="{shape}" fill="{t["inset"]}"/>',
        image,
        f'<path d="{shape}" fill="none" stroke="{t["signal"]}" stroke-width="1.6"{glow_attr(t)}/>',
    ])


def sky(t, w, h, cx_ratio=.5, seed=21, text_box=None, count=70):
    """Rounded panel filled with the night sky (or parchment) gradient and a starfield."""
    gradient = (f'<radialGradient id="sky" cx="{cx_ratio:.2f}" cy=".5" r=".8">'
                f'<stop offset="0" stop-color="{t["sky_center"]}"/><stop offset="1" stop-color="{t["sky_edge"]}"/>'
                f'</radialGradient>')
    return gradient, (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="url(#sky)" '
                      f'stroke="{t["line"]}"/>' + starfield(t, w, h, count, seed, text_box))


def floating_runes(items, t, size=15):
    return "".join(f'<g class="drift" style="animation-delay:{i * .9:.1f}s">'
                   f'{rune(name, x, y, size, t["signal"], 1.3, .38)}</g>' for i, (name, x, y) in enumerate(items))


def write_pair(name, build):
    for theme, t in THEMES.items():
        (ASSETS / f"{name}-{theme}.svg").write_text(build(t), encoding="utf-8")


# --- data --------------------------------------------------------------------

def github_data():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GH_TOKEN or GITHUB_TOKEN to build the project cards.")
    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
          nodes { name stargazerCount primaryLanguage { name color } }
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
    return payload["data"]["user"]


def medium_posts(limit=3):
    """Latest Medium posts; returns None when the feed cannot be read so the README keeps its list."""
    request = urllib.request.Request(MEDIUM_FEED, headers={"User-Agent": "Mozilla/5.0 profile-readme-builder"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            root = ET.fromstring(response.read())
    except Exception as error:  # network or feed format problem: keep the existing list
        print(f"Medium feed skipped: {error}")
        return None
    posts = []
    for item in root.iter("item"):
        published = dt.datetime.strptime(item.findtext("pubDate"), "%a, %d %b %Y %H:%M:%S %Z")
        posts.append({"title": item.findtext("title").strip(),
                      "link": item.findtext("link").split("?")[0],
                      "date": published.strftime("%b %d, %Y")})
    return posts[:limit]


# --- assets ------------------------------------------------------------------

def starfield(t, w, h, count, seed, text_box=None):
    """Seeded scatter of small stars; some twinkle. Stars over the text area are dimmer."""
    rng = random.Random(seed)
    parts = []
    for i in range(count):
        x, y = rng.uniform(8, w - 8), rng.uniform(8, h - 8)
        r, opacity = rng.uniform(.5, 1.5), rng.uniform(.25, .85)
        if text_box and text_box[0] < x < text_box[2] and text_box[1] < y < text_box[3]:
            opacity *= .4
        if not t["glow"]:
            opacity *= .55
        twinkle = f' class="tw" style="animation-delay:{rng.uniform(0, 3):.1f}s"' if i % 5 == 0 else ""
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{t["star"]}" '
                     f'fill-opacity="{opacity:.2f}"{twinkle}/>')
    return "".join(parts)


def rune_circle(cx, cy, t):
    """Slowly turning ring of the name runes around a small neural network with one lit path."""
    parts = [f'<circle cx="{cx}" cy="{cy}" r="88" fill="url(#halo)"/>',
             f'<circle cx="{cx}" cy="{cy}" r="121" fill="none" stroke="{t["signal"]}" stroke-opacity=".2" '
             f'stroke-dasharray="2 6"/>',
             f'<circle cx="{cx}" cy="{cy}" r="113" fill="none" stroke="{t["signal"]}" stroke-opacity=".6" '
             f'stroke-width="1.5"{glow_attr(t)}/>',
             f'<circle cx="{cx}" cy="{cy}" r="89" fill="none" stroke="{t["signal"]}" stroke-opacity=".45"/>']

    # Ring of runes: the name twice around the circle.
    slots = NAME_RUNES * 2
    ring = []
    size, radius = 12, 101
    for i, name in enumerate(slots):
        angle = i * 360 / len(slots)
        if name is None:
            glyph = diamond(cx, cy - radius, 2.2, t["signal"], .8)
        else:
            glyph = rune(name, cx - .25 * size, cy - radius - size / 2, size, t["signal"], 1.4, .9)
        ring.append(f'<g transform="rotate({angle:.2f} {cx} {cy})">{glyph}</g>')
    parts.append(f'<g class="spin" style="transform-origin:{cx}px {cy}px"{glow_attr(t)}>{"".join(ring)}</g>')

    # Neural network inside the circle.
    layers, lit = (3, 4, 4, 3), (0, 2, 1, 1)
    xs = [cx - 60 + i * 40 for i in range(len(layers))]

    def node_y(layer, k):
        n = layers[layer]
        spread = 36 if n == 3 else 54
        return cy + spread * (k - (n - 1) / 2) / ((n - 1) / 2)

    edges, lit_edges = [], []
    for i in range(len(layers) - 1):
        for a in range(layers[i]):
            for b in range(layers[i + 1]):
                line = (xs[i], node_y(i, a), xs[i + 1], node_y(i + 1, b))
                (lit_edges if (a, b) == (lit[i], lit[i + 1]) else edges).append(line)
    parts += [f'<line x1="{x1}" y1="{y1:.1f}" x2="{x2}" y2="{y2:.1f}" stroke="{t["axis"]}" stroke-opacity=".5"/>'
              for x1, y1, x2, y2 in edges]
    lit_parts = [f'<line x1="{x1}" y1="{y1:.1f}" x2="{x2}" y2="{y2:.1f}" stroke="{t["signal"]}" '
                 f'stroke-width="2" stroke-dasharray="6 4" class="flow"/>' for x1, y1, x2, y2 in lit_edges]
    for i, n in enumerate(layers):
        for k in range(n):
            on = k == lit[i]
            node = (f'<circle cx="{xs[i]}" cy="{node_y(i, k):.1f}" r="5.5" '
                    f'fill="{t["signal"] if on else t["inset"]}" stroke="{t["signal"] if on else t["axis"]}" '
                    f'stroke-width="1.5"/>')
            (lit_parts if on else parts).append(node)
    parts.append(f'<g{glow_attr(t)}>{"".join(lit_parts)}</g>')
    return "".join(parts)


def name_in_runes(x, y, t, size=14):
    """BERKE · ARDA · TURK drawn in runes starting at (x, y)."""
    parts = []
    for name in NAME_RUNES[:-1]:
        if name is None:
            parts.append(diamond(x + 3, y + size / 2, 2, t["signal"], .7))
            x += 13
        else:
            parts.append(rune(name, x, y, size, t["signal"], 1.4, .85))
            x += size * .86
    return f'<g{glow_attr(t)}>{"".join(parts)}</g>'


def header_svg(t):
    w, h = 1000, 300
    arch = (712, 18, 250, 266)
    gradient, background = sky(t, w, h, .84, 21, text_box=(30, 30, 600, 280), count=90)
    halo = (f'<radialGradient id="halo"><stop offset="0" stop-color="{t["signal"]}" stop-opacity=".22"/>'
            f'<stop offset="1" stop-color="{t["signal"]}" stop-opacity="0"/></radialGradient>')
    ax, ay, aw, ah = arch
    return "".join([
        svg_open(w, h, "Berke Arda Türk, data mage in training: machine learning and data science. "
                       "Takes real datasets to honest answers with a baseline first and validation without leakage."),
        ANIMATIONS,
        defs(t, gradient + halo),
        background,
        floating_runes([("algiz", 640, 40), ("sowilo", 676, 128), ("othala", 630, 214), ("gebo", 680, 262)], t),
        f'<ellipse cx="{ax + aw / 2}" cy="{ay + ah / 2}" rx="{aw * .75}" ry="{ah * .62}" fill="url(#halo)"/>',
        f'<path d="{arch_d(ax - 7, ay - 7, aw + 14, ah + 14)}" fill="none" stroke="{t["signal"]}" '
        f'stroke-opacity=".35" stroke-dasharray="2 6"/>',
        framed_art("heroClip", arch_d(*arch), arch, t, crop=CROP_HERO),
        diamond(ax + aw / 2, ay - 7, 4, t["signal"]),
        star4(ax - 4, ay + 120, 6, t["signal"], .8),
        star4(ax + aw + 6, ay + 60, 5, t["signal"], .7),
        star4(46, 52, 6, t["signal"]),
        text(60, 57, "DATA MAGE · MACHINE LEARNING · VIZJA UNIVERSITY", 12, t["muted"], MONO, spacing=1.5),
        text(38, 124, "Berke Arda Türk", 54, t["ink"], SERIF, 600),
        name_in_runes(42, 142, t),
        text(40, 204, "Data mage in training. I take real datasets to honest answers:", 17, t["muted"], SERIF,
             style="italic"),
        text(40, 228, "a baseline first, no leakage in validation, and only spells that hold.", 17, t["muted"],
             SERIF, style="italic"),
        text(40, 266, "berkeardaturk.com · kaggle.com/berketurk · medium.com/@berkeardaturk", 12, t["muted"], MONO),
        "</svg>",
    ])


def path_svg(t):
    """The Mage's Path: what I work on, beside a painting (scene or the rune circle from the portrait)."""
    w, h = 1000, 350
    arch = (36, 34, 240, 282)
    gradient, background = sky(t, w, h, .15, 5, text_box=(300, 20, 980, 330), count=60)
    parts = [svg_open(w, h, "The Mage's Path: " + ". ".join(f"{a}: {b}" for _, a, b in PATH_ITEMS)),
             ANIMATIONS, defs(t, gradient), background,
             framed_art("pathClip", arch_d(*arch), arch, t, scene=SCENE_PATH, crop=CROP_SIGIL),
             diamond(arch[0] + arch[2] / 2, arch[1] - 6, 4, t["signal"]),
             star4(322, 50, 6, t["signal"]),
             text(336, 55, "THE MAGE'S PATH", 12, t["muted"], MONO, spacing=1.5),
             text(320, 96, "Find the honest answer, then ship it", 30, t["ink"], SERIF, 600)]
    for i, (sigil, title, desc) in enumerate(PATH_ITEMS):
        y = 118 + i * 72
        parts.append(f'<rect x="320.5" y="{y + .5}" width="643" height="62" rx="6" fill="{t["inset"]}" '
                     f'fill-opacity=".75" stroke="{t["line"]}"/>')
        parts.append(rune(sigil, 338, y + 14, 20, t["signal"], 1.8, extra=glow_attr(t)))
        parts.append(text(372, y + 25, title, 16, t["ink"], SERIF, 600))
        for k, line in enumerate(wrap(desc, 96)[:2]):
            parts.append(text(372, y + 43 + k * 15, line, 12.5, t["muted"]))
    parts.append("</svg>")
    return "".join(parts)


def guild_svg(t):
    """Guild member card with the portrait medallion, plus a static quest log of real milestones."""
    w, h = 1000, 340
    gradient, background = sky(t, w, h, .3, 9, count=55)
    cx_, cy_, r = 128, 178, 68
    parts = [svg_open(w, h, "Guild card. " + ". ".join(f"{k.title()}: {v}" for k, v in GUILD_FIELDS)
                      + ". Quest log: " + ". ".join(f"{d}: {e}" for d, e in QUEST_LOG)),
             ANIMATIONS, defs(t, gradient), background]
    # Card.
    cx0, cy0, cw, ch = 30, 30, 540, 280
    parts.append(f'<g transform="translate({cx0} {cy0})">{framed_panel(cw, ch, t)}</g>')
    parts.append(f'<rect x="{cx0 + 7}" y="{cy0 + 7}" width="{cw - 14}" height="34" fill="{t["signal"]}" '
                 f'fill-opacity=".1"/>')
    parts.append(rune("berkano", cx0 + 22, cy0 + 15, 18, t["signal"], 1.6, extra=glow_attr(t)))
    parts.append(text(cx0 + 44, cy0 + 29, "GUILD OF DATA MAGES · MEMBER CARD", 12, t["ink"], MONO, 600, spacing=1.5))
    parts.append(text(cx0 + cw - 22, cy0 + 29, "No. 0021", 12, t["muted"], MONO, anchor="end"))
    # Medallion.
    parts.append(f'<circle cx="{cx_}" cy="{cy_}" r="{r + 9}" fill="none" stroke="{t["signal"]}" '
                 f'stroke-opacity=".35" stroke-dasharray="2 5"/>')
    parts.append(framed_art("faceClip", circle_d(cx_, cy_, r), (cx_ - r, cy_ - r, 2 * r, 2 * r), t, crop=CROP_FACE))
    for angle in (0, 90, 180, 270):
        a = math.radians(angle)
        parts.append(diamond(round(cx_ + (r + 9) * math.cos(a), 1), round(cy_ + (r + 9) * math.sin(a), 1),
                             3.2, t["signal"]))
    # Fields.
    for i, (label, value) in enumerate(GUILD_FIELDS):
        y = cy0 + 70 + i * 40
        parts.append(text(232, y, label, 10, t["muted"], MONO, spacing=1.5))
        parts.append(text(232, y + 19, value, 15.5, t["signal"] if label == "CURRENT QUEST" else t["ink"],
                          SERIF, 600))
    parts.append(name_in_runes(cx_ - 64, cy0 + ch - 34, t, 11))
    # Quest log.
    lx = 618
    parts.append(star4(lx + 2, 52, 6, t["signal"]))
    parts.append(text(lx + 16, 57, "QUEST LOG", 12, t["muted"], MONO, spacing=1.5))
    top = 84
    parts.append(f'<line x1="{lx + 2}" y1="{top}" x2="{lx + 2}" y2="{top + (len(QUEST_LOG) - 1) * 50}" '
                 f'stroke="{t["signal"]}" stroke-opacity=".35"/>')
    for i, (date, entry) in enumerate(QUEST_LOG):
        y = top + i * 50
        parts.append(diamond(lx + 2, y, 5, t["signal"] if i == 0 else t["axis"]))
        parts.append(text(lx + 20, y + 4, date.upper(), 10.5, t["signal"], MONO, 600, spacing=1))
        parts.append(text(lx + 20, y + 23, entry, 14, t["ink"], SERIF))
    parts.append("</svg>")
    return "".join(parts)


def raven_svg(t):
    """Send a raven: closing call to action with a painting (scene or the rune circle)."""
    w, h = 1000, 280
    gradient, background = sky(t, w, h, .83, 33, text_box=(30, 30, 640, 250), count=70)
    halo = (f'<radialGradient id="halo"><stop offset="0" stop-color="{t["signal"]}" stop-opacity=".16"/>'
            f'<stop offset="1" stop-color="{t["signal"]}" stop-opacity="0"/></radialGradient>')
    scene = art_href(SCENE_RAVEN) is not None
    box = (712, 18, 250, 244)
    art = (f'<ellipse cx="837" cy="140" rx="190" ry="150" fill="url(#halo)"/>'
           f'<path d="{arch_d(box[0] - 7, box[1] - 7, box[2] + 14, box[3] + 14)}" fill="none" '
           f'stroke="{t["signal"]}" stroke-opacity=".35" stroke-dasharray="2 6"/>'
           + framed_art("ravenClip", arch_d(*box), box, t, scene=SCENE_RAVEN)
           + diamond(box[0] + box[2] / 2, box[1] - 7, 4, t["signal"])
           if scene else rune_circle(830, 140, t))
    return "".join([
        svg_open(w, h, "Send a raven: open to machine learning and data roles, and to collaboration "
                       "on data science projects."),
        ANIMATIONS, defs(t, gradient + halo), background,
        floating_runes([("ansuz", 650, 40), ("gebo", 672, 210)], t),
        art,
        star4(46, 62, 6, t["signal"]),
        text(60, 67, "SEND A RAVEN", 12, t["muted"], MONO, spacing=1.5),
        text(40, 124, "Let's build something honest", 38, t["ink"], SERIF, 600),
        text(40, 166, "Open to machine learning and data roles, and to collaboration", 17, t["muted"], SERIF,
             style="italic"),
        text(40, 190, "on data science projects. The links below reach me fastest.", 17, t["muted"], SERIF,
             style="italic"),
        name_in_runes(42, 226, t, 12),
        "</svg>",
    ])


def card_svg(project, repo, t):
    w, h = 420, 180
    parts = [svg_open(w, h, f'{project["title"]}: {project["metric"]}. {project["desc"]}'),
             defs(t),
             framed_panel(w, h, t),
             rune(project["rune"], 22, 19, 18, t["signal"], 1.8, extra=glow_attr(t)),
             text(44, 35, project["title"], 17, t["ink"], SERIF, 600)]
    stars = repo.get("stargazerCount", 0)
    star_x = w - 22 - len(str(stars)) * 7.5 - 19
    parts.append(f'<path d="{STAR_PATH}" transform="translate({star_x:.1f} 23) scale(.9)" fill="{t["muted"]}"/>')
    parts.append(text(w - 22, 35, stars, 12.5, t["muted"], MONO, anchor="end"))
    for i, line in enumerate(wrap(project["desc"], 56)[:3]):
        parts.append(text(22, 64 + i * 19, line, 12.5, t["muted"]))
    parts.append(star4(27, 132, 5, t["signal"]))
    parts.append(text(38, 136, project["metric"], 12.5, t["signal"], MONO, 600))
    language = repo.get("primaryLanguage") or {"name": "Python", "color": "#3572A5"}
    parts.append(f'<circle cx="28" cy="158" r="5" fill="{language["color"]}"/>')
    parts.append(text(39, 162, language["name"], 11.5, t["muted"]))
    x = 39 + len(language["name"]) * 6.4 + 14
    for tag in project["tags"]:
        svg, width = chip(x, 147, tag, t, 10)
        parts.append(svg)
        x += width + 6
    parts.append("</svg>")
    return "".join(parts)


def toolkit_svg(t):
    w, row_h = 1000, 46
    h = 44 + len(TOOLKIT) * row_h
    label = "Toolkit: " + ". ".join(f"{k}: {', '.join(v)}" for k, _, v in TOOLKIT)
    parts = [svg_open(w, h, label), defs(t), framed_panel(w, h, t)]
    for r, (name, sigil, items) in enumerate(TOOLKIT):
        y = 32 + r * row_h
        parts.append(rune(sigil, 34, y + 3, 17, t["signal"], 1.6, extra=glow_attr(t)))
        parts.append(text(58, y + 17, name.upper(), 12.5, t["ink"], SERIF, 600, spacing=1.5))
        x = 270
        for item in items:
            svg, width = chip(x, y, item, t, 12.5)
            parts.append(svg)
            x += width + 9
    parts.append("</svg>")
    return "".join(parts)


def divider_svg(t):
    """Ornamental rule with a small rune seal in the middle."""
    w, h, cx, cy = 1000, 44, 500, 22
    fade = (f'<linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="{t["signal"]}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{t["signal"]}" stop-opacity=".6"/></linearGradient>'
            f'<linearGradient id="fadeR" x1="1" x2="0"><stop offset="0" stop-color="{t["signal"]}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{t["signal"]}" stop-opacity=".6"/></linearGradient>')
    return "".join([
        svg_open(w, h, "Divider"),
        defs(t, fade),
        f'<rect x="60" y="{cy - .5}" width="{cx - 60 - 34}" height="1" fill="url(#fadeL)"/>',
        f'<rect x="{cx + 34}" y="{cy - .5}" width="{w - 60 - cx - 34}" height="1" fill="url(#fadeR)"/>',
        diamond(cx - 26, cy, 3, t["signal"], .8),
        diamond(cx + 26, cy, 3, t["signal"], .8),
        f'<g{glow_attr(t)}><circle cx="{cx}" cy="{cy}" r="15" fill="none" stroke="{t["signal"]}" stroke-opacity=".7"/>',
        rune("berkano", cx - 4, cy - 8, 16, t["signal"], 1.6),
        "</g></svg>",
    ])


def update_writing(posts):
    readme = ROOT / "README.md"
    content = readme.read_text(encoding="utf-8")
    lines = "\n".join(f'- [{escape(p["title"], quote=False)}]({p["link"]}) <sub>· {p["date"]}</sub>' for p in posts)
    block = f"<!-- WRITING:START -->\n{lines}\n<!-- WRITING:END -->"
    content = re.sub(r"<!-- WRITING:START -->.*?<!-- WRITING:END -->", lambda _: block, content, flags=re.S)
    readme.write_text(content, encoding="utf-8")


def main():
    user = github_data()
    repos = {r["name"]: r for r in user["repositories"]["nodes"]}
    write_pair("header", header_svg)
    write_pair("path", path_svg)
    write_pair("guild", guild_svg)
    write_pair("raven", raven_svg)
    for project in FEATURED:
        write_pair(f'card-{project["repo"].lower()}', lambda t, p=project: card_svg(p, repos.get(p["repo"], {}), t))
    write_pair("toolkit", toolkit_svg)
    write_pair("divider", divider_svg)
    posts = medium_posts()
    if posts:
        update_writing(posts)
    print("profile assets written")


if __name__ == "__main__":
    main()
