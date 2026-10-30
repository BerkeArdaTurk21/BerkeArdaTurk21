"""Build the profile README assets.

Writes light and dark SVGs for the header, project cards and toolkit, and
refreshes the "Latest writing" list in README.md from Medium.
Neutral colors follow GitHub's own UI so the cards sit naturally on the page;
the accent is the ice blue from berkeardaturk.com.
Standard library only. Needs a GitHub token in GH_TOKEN or GITHUB_TOKEN for
the star counts and languages on the project cards (the GitHub Action passes
its own token).

Usage: python scripts/build_profile.py
"""
import datetime as dt
import json
import os
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

# GitHub UI neutrals with the berkeardaturk.com accent (src/index.css: --signal).
THEMES = {
    "dark": {
        "card": "#151b23", "inset": "#0d1117", "line": "#2b323b", "axis": "#3d444d",
        "ink": "#e6edf3", "muted": "#9198a1", "signal": "#7fe0ff", "empty": "#1e252e",
    },
    "light": {
        "card": "#f6f8fa", "inset": "#ffffff", "line": "#d1d9e0", "axis": "#b7c0ca",
        "ink": "#1f2328", "muted": "#59636e", "signal": "#085d77", "empty": "#e6eaef",
    },
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

# Featured projects, in the same order as the pinned repos. Metrics come from each repo's README.
FEATURED = [
    {"repo": "foldsafe", "title": "foldsafe",
     "desc": "Static analyzer and agent skill that catch data leakage in ML code before cross-validation scores mislead you.",
     "metric": "Pre-alpha · 8 rules planned", "tags": ["static analysis", "agent skill"]},
    {"repo": "kaggle-titanic", "title": "Kaggle Titanic",
     "desc": "End-to-end tabular ML: leak-free scikit-learn pipelines, nested cross-validation and a group survival feature.",
     "metric": "Kaggle 0.794 · CV 0.841", "tags": ["scikit-learn", "XGBoost"]},
    {"repo": "customer-churn-shap-dashboard", "title": "Churn SHAP Dashboard",
     "desc": "XGBoost churn model with a SHAP explanation for every prediction, served as a Streamlit app.",
     "metric": "ROC-AUC 0.84 · recall 79%", "tags": ["XGBoost", "SHAP"]},
    {"repo": "Stock-Sentiment-Predictor", "title": "Stock Sentiment",
     "desc": "Three-class sentiment on 4,846 financial news headlines with TF-IDF and LinearSVC, plus a Streamlit app.",
     "metric": "74.5% accuracy · baseline 59.4%", "tags": ["NLP", "scikit-learn"]},
    {"repo": "EconoScope", "title": "EconoScope",
     "desc": "Exploratory analysis of inflation in 212 countries: five measures, country comparisons and crisis periods.",
     "metric": "212 countries · 1970-2022", "tags": ["EDA", "pandas"]},
    {"repo": "Python-RoadMap", "title": "Python RoadMap",
     "desc": "Eight weeks of daily Python lessons with quizzes and exercises, plus four standard-library projects.",
     "metric": "63 lessons · 4 projects", "tags": ["Python", "learning"]},
]

TOOLKIT = [
    ("Languages", ["Python", "SQL", "TypeScript", "Java"]),
    ("Machine learning", ["scikit-learn", "XGBoost", "SHAP", "PyTorch (learning)"]),
    ("Data & analysis", ["pandas", "NumPy", "Matplotlib", "Seaborn", "Jupyter"]),
    ("Big data & databases", ["PySpark", "MySQL", "SQLite"]),
    ("Apps & engineering", ["Streamlit", "React", "Tailwind", "Git"]),
]

STAR_PATH = ("M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97"
             ".719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194"
             "L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z")
REPO_PATH = ("M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5"
             "h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708"
             "A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087"
             "a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z")


# --- helpers -----------------------------------------------------------------

def svg_open(width, height, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title>')


def panel(width, height, t):
    return (f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="8" '
            f'fill="{t["card"]}" stroke="{t["line"]}"/>')


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


def chip(x, y, label, t, size=11):
    width = round(len(label) * size * 0.6 + 20)
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{size + 11}" rx="{(size + 11) / 2}" '
            f'fill="{t["inset"]}" stroke="{t["line"]}"/>'
            + text(x + width / 2, y + size + 4, label, size, t["ink"], MONO, anchor="middle")), width


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

def header_svg(t):
    w, h = 1000, 260
    # A small feed-forward network; one path through it is lit in the accent color.
    layers, lit = (4, 6, 6, 2), (1, 3, 2, 0)
    xs = [660 + i * 92 for i in range(len(layers))]
    top, bottom = 44, 204

    def node_y(layer, k):
        n = layers[layer]
        return top + (bottom - top) * (k + 0.5) / n

    edges, lit_edges = [], []
    for i in range(len(layers) - 1):
        for a in range(layers[i]):
            for b in range(layers[i + 1]):
                line = (xs[i], node_y(i, a), xs[i + 1], node_y(i + 1, b))
                (lit_edges if (a, b) == (lit[i], lit[i + 1]) else edges).append(line)
    net = [f'<line x1="{x1}" y1="{y1:.1f}" x2="{x2}" y2="{y2:.1f}" stroke="{t["axis"]}" stroke-opacity=".55"/>'
           for x1, y1, x2, y2 in edges]
    net += [f'<line x1="{x1}" y1="{y1:.1f}" x2="{x2}" y2="{y2:.1f}" stroke="{t["signal"]}" stroke-width="2" '
            f'stroke-dasharray="6 4" class="flow"/>' for x1, y1, x2, y2 in lit_edges]
    for i, n in enumerate(layers):
        for k in range(n):
            on = k == lit[i]
            net.append(f'<circle cx="{xs[i]}" cy="{node_y(i, k):.1f}" r="7" fill="{t["signal"] if on else t["inset"]}" '
                       f'stroke="{t["signal"] if on else t["axis"]}" stroke-width="1.5"/>')
    for label, x in (("input", xs[0]), ("hidden", (xs[1] + xs[2]) / 2), ("output", xs[-1])):
        net.append(text(x, 232, label, 11, t["muted"], MONO, anchor="middle"))
    return "".join([
        svg_open(w, h, "Berke Arda Türk: machine learning and data science. Builds models on real datasets, "
                       "tests them against a baseline first and turns the useful ones into apps."),
        "<style>.flow{animation:flow 1.4s linear infinite}@keyframes flow{to{stroke-dashoffset:-10}}"
        "@media (prefers-reduced-motion:reduce){.flow{animation:none}}</style>",
        panel(w, h, t),
        text(40, 62, "MACHINE LEARNING · DATA SCIENCE · VIZJA UNIVERSITY", 12, t["muted"], MONO, spacing=1.5),
        text(38, 128, "Berke Arda Türk", 54, t["ink"], SANS, 700),
        text(40, 168, "Computer Science student who builds machine learning models on real", 17, t["muted"]),
        text(40, 191, "data, tests them against a baseline first and ships the useful ones.", 17, t["muted"]),
        text(40, 230, "berkeardaturk.com · kaggle.com/berketurk · medium.com/@berkeardaturk", 12, t["muted"], MONO),
        *net,
        "</svg>",
    ])


def card_svg(project, repo, t):
    w, h = 420, 178
    parts = [svg_open(w, h, f'{project["title"]}: {project["metric"]}. {project["desc"]}'),
             panel(w, h, t),
             f'<path d="{REPO_PATH}" transform="translate(20 20)" fill="{t["muted"]}"/>',
             text(44, 33, project["title"], 15.5, t["ink"], SANS, 600)]
    stars = repo.get("stargazerCount", 0)
    star_x = w - 20 - len(str(stars)) * 7.5 - 19
    parts.append(f'<path d="{STAR_PATH}" transform="translate({star_x:.1f} 21) scale(.9)" fill="{t["muted"]}"/>')
    parts.append(text(w - 20, 33, stars, 12.5, t["muted"], MONO, anchor="end"))
    for i, line in enumerate(wrap(project["desc"], 56)[:3]):
        parts.append(text(20, 62 + i * 19, line, 12.5, t["muted"]))
    parts.append(text(20, 134, project["metric"], 12.5, t["signal"], MONO, 600))
    language = repo.get("primaryLanguage") or {"name": "Python", "color": "#3572A5"}
    parts.append(f'<circle cx="26" cy="157" r="5" fill="{language["color"]}"/>')
    parts.append(text(37, 161, language["name"], 11.5, t["muted"]))
    x = 37 + len(language["name"]) * 6.4 + 14
    for tag in project["tags"]:
        svg, width = chip(x, 146, tag, t, 10)
        parts.append(svg)
        x += width + 6
    parts.append("</svg>")
    return "".join(parts)


def toolkit_svg(t):
    w, row_h = 1000, 46
    h = 40 + len(TOOLKIT) * row_h
    parts = [svg_open(w, h, "Toolkit: " + ". ".join(f"{k}: {', '.join(v)}" for k, v in TOOLKIT)), panel(w, h, t)]
    for r, (label, items) in enumerate(TOOLKIT):
        y = 30 + r * row_h
        parts.append(text(32, y + 19, label.upper(), 11, t["muted"], MONO, spacing=1.5))
        x = 250
        for item in items:
            svg, width = chip(x, y, item, t, 12.5)
            parts.append(svg)
            x += width + 9
    parts.append("</svg>")
    return "".join(parts)


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
    for project in FEATURED:
        write_pair(f'card-{project["repo"].lower()}', lambda t, p=project: card_svg(p, repos.get(p["repo"], {}), t))
    write_pair("toolkit", toolkit_svg)
    posts = medium_posts()
    if posts:
        update_writing(posts)
    print("profile assets written")


if __name__ == "__main__":
    main()
