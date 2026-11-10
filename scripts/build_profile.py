"""Build the profile README and its SVG panels.

A plain, professional layout in the colours of the profile picture: dark navy
panels, an ice blue accent and a small neural network sigil in the header.
No animation, no live data, standard library only. Run it after changing the
content below, then commit README.md and assets/*.svg.

Usage: python scripts/build_profile.py
"""
import random
from html import escape
from pathlib import Path

USER = "BerkeArdaTurk21"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
# GitHub caches README images; bump this after a design change.
CACHE_VERSION = 8
W = 1000

BG_TOP, BG_BOTTOM, LINE, CHIP = "#101c30", "#0a111e", "#1f2e47", "#0c1626"
INK, MUTED, ACCENT = "#e6eef8", "#93a4ba", "#7dd3fc"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

NAME = "Berke Arda Türk"
EYEBROW = "MACHINE LEARNING · DATA SCIENCE · VIZJA UNIVERSITY"
TAGLINE = ["Computer Science student specialising in AI and Data Science.",
           "I take real datasets to honest answers: baseline first, no leakage."]

LINKS = [
    ("website", "Website", "https://berkeardaturk.com"),
    ("linkedin", "LinkedIn", "https://www.linkedin.com/in/berke-arda-turk/"),
    ("kaggle", "Kaggle", "https://www.kaggle.com/berketurk"),
    ("medium", "Medium", "https://medium.com/@berkeardaturk"),
    ("email", "Email", "mailto:turkberkearda@gmail.com"),
]

ABOUT = ("I like taking a real dataset all the way to an honest answer: a simple baseline first, validation "
         "without leakage, and a clear note on what the model cannot do. The results that hold up become "
         "apps and write-ups.")
POINTS = [
    ("Focus", "machine learning on tabular data, model explainability, and big data with PySpark"),
    ("Currently building", "foldsafe, an open-source checker for data leakage in ML code"),
    ("Open to", "machine learning and data roles, internships and collaborations"),
]

# (repo, title, description, result, stack)
PROJECTS = [
    ("foldsafe", "foldsafe", "Static analyzer and agent skill that catch data leakage in ML code.",
     "Pre-alpha · 4 rules working", ["Python", "static analysis"]),
    ("kaggle-titanic", "Kaggle Titanic",
     "End-to-end tabular ML with leak-free pipelines and nested cross-validation.",
     "Kaggle 0.794 · CV 0.841", ["scikit-learn", "XGBoost"]),
    ("customer-churn-shap-dashboard", "Churn SHAP Dashboard",
     "Churn model with a SHAP explanation for every prediction, served as an app.",
     "ROC-AUC 0.84 · recall 79%", ["XGBoost", "SHAP", "Streamlit"]),
    ("Stock-Sentiment-Predictor", "Stock Sentiment Predictor",
     "Three-class sentiment on 4,846 financial news headlines.",
     "74.5% accuracy · baseline 59.4%", ["scikit-learn", "TF-IDF"]),
    ("EconoScope", "EconoScope", "Exploratory analysis of inflation in 212 countries, 1970-2022.",
     "5 inflation measures compared", ["pandas", "Matplotlib"]),
    ("Python-RoadMap", "Python RoadMap", "Eight weeks of daily Python lessons with quizzes and exercises.",
     "63 lessons · 4 projects", ["Python"]),
]

SKILLS = [
    ("Languages", ["Python", "SQL", "TypeScript", "Java"]),
    ("Machine learning", ["scikit-learn", "XGBoost", "SHAP", "PyTorch (learning)"]),
    ("Data and analysis", ["pandas", "NumPy", "Matplotlib", "Seaborn", "Jupyter"]),
    ("Big data and databases", ["PySpark", "MySQL", "SQLite"]),
    ("Apps and engineering", ["Streamlit", "React", "Tailwind", "Git"]),
]

# Medium posts, newest first. Updated by hand.
POSTS = [
    ("What My First Kaggle Project Taught Me About Data Leakage and Simple Models", "Oct 2026",
     "https://medium.com/@berkeardaturk/what-my-first-kaggle-project-taught-me-about-data-leakage-and-simple-models-c7c2b174e6f2"),
    ("I Tried to Predict Customer Churn With ML: Here's What Actually Worked", "May 2026",
     "https://medium.com/@berkeardaturk/i-tried-to-predict-customer-churn-with-ml-heres-what-actually-worked-50a1c38e2185"),
    ("I Analysed 50 Years of Global Inflation Data: Here's What I Found", "May 2026",
     "https://medium.com/@berkeardaturk/i-analysed-50-years-of-global-inflation-data-heres-what-i-found-7a511fd15c73"),
]

SECTIONS = {"about": "About", "projects": "Projects", "skills": "Skills", "writing": "Writing"}


# --- building blocks ---------------------------------------------------------

def svg_open(w, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title><defs>'
            f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG_TOP}"/>'
            f'<stop offset="1" stop-color="{BG_BOTTOM}"/></linearGradient>'
            '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" '
            'result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            f'<radialGradient id="halo"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".18"/>'
            f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient></defs>')


def panel(w, h, seed, dots, x=0):
    """Navy panel with a thin border and a few faint light particles, like the portrait's background."""
    rng = random.Random(seed)
    parts = [f'<rect x="{x + .5:.2f}" y=".5" width="{w - 1:.2f}" height="{h - 1}" rx="10" fill="url(#bg)" '
             f'stroke="{LINE}"/>']
    for _ in range(dots):
        parts.append(f'<circle cx="{x + rng.uniform(10, w - 10):.1f}" cy="{rng.uniform(8, h - 8):.1f}" '
                     f'r="{rng.uniform(.5, 1.3):.2f}" fill="{ACCENT}" fill-opacity="{rng.uniform(.12, .4):.2f}"/>')
    return "".join(parts)


def text(x, y, value, size, fill, family=SANS, weight=400, anchor="start", spacing=0):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
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


def chip(x, y, label, size=11):
    width = round(len(label) * size * .6 + 20)
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{size + 11}" rx="{(size + 11) / 2}" fill="{CHIP}" '
            f'stroke="{ACCENT}" stroke-opacity=".3"/>'
            + text(x + width / 2, y + size + 4, label, size, INK, MONO, anchor="middle")), width


def sigil(cx, cy):
    """Ring with tick marks around a small neural network with one lit path (the circle in the portrait)."""
    import math
    parts = [f'<circle cx="{cx}" cy="{cy}" r="120" fill="url(#halo)"/>',
             f'<circle cx="{cx}" cy="{cy}" r="88" fill="none" stroke="{ACCENT}" stroke-opacity=".75" '
             'stroke-width="1.5" filter="url(#glow)"/>',
             f'<circle cx="{cx}" cy="{cy}" r="66" fill="none" stroke="{ACCENT}" stroke-opacity=".3"/>']
    for i in range(48):
        a = i / 48 * 2 * math.pi
        r0 = 71 if i % 4 == 0 else 75
        parts.append(f'<line x1="{cx + r0 * math.cos(a):.1f}" y1="{cy + r0 * math.sin(a):.1f}" '
                     f'x2="{cx + 82 * math.cos(a):.1f}" y2="{cy + 82 * math.sin(a):.1f}" stroke="{ACCENT}" '
                     f'stroke-opacity="{.8 if i % 4 == 0 else .4}"/>')
    layers, lit = (3, 4, 4, 3), (0, 2, 1, 1)
    xs = [cx - 42 + i * 28 for i in range(4)]

    def node_y(layer, k):
        n = layers[layer]
        spread = 26 if n == 3 else 39
        return cy + spread * (k - (n - 1) / 2) / ((n - 1) / 2)

    lit_parts = []
    for i in range(3):
        for a in range(layers[i]):
            for b in range(layers[i + 1]):
                on = (a, b) == (lit[i], lit[i + 1])
                line = (f'<line x1="{xs[i]}" y1="{node_y(i, a):.1f}" x2="{xs[i + 1]}" y2="{node_y(i + 1, b):.1f}" '
                        f'stroke="{ACCENT if on else "#3a4d6b"}" stroke-width="{2 if on else 1}"/>')
                (lit_parts if on else parts).append(line)
    for i, n in enumerate(layers):
        for k in range(n):
            on = k == lit[i]
            node = (f'<circle cx="{xs[i]}" cy="{node_y(i, k):.1f}" r="4" fill="{ACCENT if on else BG_BOTTOM}" '
                    f'stroke="{ACCENT if on else "#3a4d6b"}" stroke-width="1.3"/>')
            (lit_parts if on else parts).append(node)
    parts.append(f'<g filter="url(#glow)">{"".join(lit_parts)}</g>')
    return "".join(parts)


# --- panels ------------------------------------------------------------------

def header_svg():
    h = 240
    return "".join([
        svg_open(W, h, f"{NAME}. {' '.join(TAGLINE)}"),
        panel(W, h, 21, 46),
        sigil(852, 120),
        text(40, 60, EYEBROW, 12, MUTED, MONO, spacing=2),
        text(38, 124, NAME, 50, INK, SANS, 700),
        f'<rect x="40" y="142" width="64" height="3" rx="1.5" fill="{ACCENT}"/>',
        text(40, 180, TAGLINE[0], 17, MUTED),
        text(40, 204, TAGLINE[1], 17, MUTED),
        "</svg>",
    ])


def link_svg(index):
    """One of five buttons; each image is 20% of the row and the gaps sit inside the images."""
    _, label, _ = LINKS[index]
    n, gap, w, h = len(LINKS), 8, 200, 48
    pw = (W - gap * (n - 1)) / n
    x0 = index * (pw + gap) - index * w
    return "".join([
        svg_open(w, h, label), panel(pw, h, 50 + index, 5, x0),
        text(round(x0 + pw / 2, 1), 29, label, 15, INK, SANS, 600, anchor="middle"),
        text(round(x0 + pw - 18, 1), 29, "↗", 13, ACCENT, SANS, anchor="end"),
        "</svg>",
    ])


def section_svg(key):
    h = 50
    return "".join([
        svg_open(W, h, SECTIONS[key]), panel(W, h, len(key) * 5, 12),
        f'<rect x="20" y="15" width="4" height="20" rx="2" fill="{ACCENT}"/>',
        text(36, 32, SECTIONS[key], 20, INK, SANS, 600),
        "</svg>",
    ])


def about_svg():
    lines = wrap(ABOUT, 118)
    top = 42
    points_top = top + len(lines) * 25 + 18
    h = points_top + len(POINTS) * 30 + 8
    label = ABOUT + " " + " ".join(f"{a}: {b}." for a, b in POINTS)
    parts = [svg_open(W, h, label), panel(W, h, 77, 30)]
    for i, line in enumerate(lines):
        parts.append(text(36, top + i * 25, line, 15.5, INK))
    parts.append(f'<line x1="36" y1="{points_top - 16}" x2="{W - 36}" y2="{points_top - 16}" stroke="{LINE}"/>')
    for i, (name, rest) in enumerate(POINTS):
        y = points_top + 10 + i * 30
        parts.append(f'<circle cx="40" cy="{y - 5}" r="3" fill="{ACCENT}"/>')
        parts.append(f'<text x="54" y="{y}" font-family="{SANS}" font-size="15">'
                     f'<tspan fill="{ACCENT}" font-weight="600">{escape(name)}</tspan>'
                     f'<tspan fill="{MUTED}" dx="8">{escape(rest)}</tspan></text>')
    parts.append("</svg>")
    return "".join(parts)


def card_svg(project, side):
    """Project card: a 500-wide half, so two at 50% line up with the full-width panels."""
    _, title, desc, result, stack = project
    outer_w, outer_h, gutter = 500, 172, 8
    w, h = outer_w - gutter, outer_h - gutter
    dx = 0 if side == 0 else gutter
    parts = [svg_open(outer_w, outer_h, f"{title}: {desc} {result}."),
             f'<g transform="translate({dx} 0)">', panel(w, h, len(title) * 3, 10),
             f'<rect x="22" y="22" width="4" height="18" rx="2" fill="{ACCENT}"/>',
             text(36, 37, title, 17, INK, SANS, 600),
             text(w - 22, 37, "↗", 14, ACCENT, SANS, anchor="end")]
    for i, line in enumerate(wrap(desc, 72)[:2]):
        parts.append(text(22, 66 + i * 19, line, 13, MUTED))
    parts.append(text(22, 116, result, 12.5, ACCENT, MONO, 600))
    x = 22
    for tag in stack:
        svg, width = chip(x, 128, tag, 10.5)
        parts.append(svg)
        x += width + 6
    parts.append("</g></svg>")
    return "".join(parts)


def skills_svg():
    row_h = 44
    h = 22 + len(SKILLS) * row_h + 6
    parts = [svg_open(W, h, ". ".join(f"{k}: {', '.join(v)}" for k, v in SKILLS)), panel(W, h, 3, 30)]
    for r, (name, items) in enumerate(SKILLS):
        y = 24 + r * row_h
        parts.append(text(36, y + 17, name.upper(), 11.5, MUTED, MONO, spacing=1.5))
        x = 270
        for item in items:
            svg, width = chip(x, y, item, 12.5)
            parts.append(svg)
            x += width + 9
    parts.append("</svg>")
    return "".join(parts)


def post_svg(index):
    title, date, _ = POSTS[index]
    h, outer_h = 66, 74
    shown = title if len(title) <= 96 else title[:93].rstrip() + "..."
    return "".join([
        svg_open(W, outer_h, f"{title}, {date}"), panel(W, h, 40 + index, 12),
        text(30, 40, f"{index + 1:02d}", 15, ACCENT, MONO, 600),
        text(72, 30, shown, 16, INK, SANS, 600),
        text(72, 50, f"{date} · Medium", 11.5, MUTED, MONO),
        text(W - 28, 39, "↗", 15, ACCENT, SANS, anchor="end"),
        "</svg>",
    ])


# --- README ------------------------------------------------------------------

def img(name, alt, width="100%"):
    return f'<img src="./assets/{name}.svg?v={CACHE_VERSION}" alt="{escape(alt)}" width="{width}">'


def readme():
    links = "".join(f'<a href="{href}">{img(f"link-{key}", label, "20%")}</a>' for key, label, href in LINKS)
    cards = "".join(f'<a href="https://github.com/{USER}/{p[0]}">'
                    f'{img(f"card-{p[0].lower()}", f"{p[1]}: {p[2]} {p[3]}.", "50%")}</a>' for p in PROJECTS)
    posts = "".join(f'<a href="{href}">{img(f"post-{i + 1}", f"{title}, {date}")}</a>'
                    for i, (title, date, href) in enumerate(POSTS))
    about_alt = ABOUT + " " + " ".join(f"{a}: {b}." for a, b in POINTS)
    skills_alt = ". ".join(f"{k}: {', '.join(v)}" for k, v in SKILLS)
    blocks = [
        f'<a href="https://berkeardaturk.com">{img("header", f"{NAME}. {chr(32).join(TAGLINE)}")}</a>',
        f"<p>{links}</p>",
        img("section-about", "About"), img("about", about_alt),
        img("section-projects", "Projects"), f"<p>{cards}</p>",
        img("section-skills", "Skills"), img("skills", skills_alt),
        img("section-writing", "Writing"), f"<p>{posts}</p>",
    ]
    return "\n\n".join(blocks) + "\n"


def main():
    ASSETS.mkdir(exist_ok=True)
    files = {"header": header_svg(), "about": about_svg(), "skills": skills_svg()}
    files.update({f"link-{LINKS[i][0]}": link_svg(i) for i in range(len(LINKS))})
    files.update({f"section-{key}": section_svg(key) for key in SECTIONS})
    files.update({f"card-{p[0].lower()}": card_svg(p, i % 2) for i, p in enumerate(PROJECTS)})
    files.update({f"post-{i + 1}": post_svg(i) for i in range(len(POSTS))})
    for name, svg in files.items():
        (ASSETS / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    (ROOT / "README.md").write_text(readme(), encoding="utf-8", newline="\n")
    print(f"wrote {len(files)} panels and README.md")


if __name__ == "__main__":
    main()
