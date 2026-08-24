from __future__ import annotations
import re
import time
from datetime import datetime, timedelta
from anchors import ANCHORS

try:
    import feedparser
    DEPS = True
except ImportError:
    DEPS = False

MONTHS_BACK = 12
CUTOFF = datetime.now() - timedelta(days=MONTHS_BACK * 30)
MIN_ARTICLES = 3

CONTROVERSY_KEYWORDS = {
    "Environmental": ["pollution", "spill", "oil spill", "deforestation", "toxic waste",
                      "emission violation", "environmental fine", "ecological damage"],
    "Social":        ["labour violation", "labor violation", "discrimination", "human rights",
                      "worker abuse", "forced labour", "workplace accident", "unfair dismissal"],
    "Governance":    ["fraud", "bribery", "corruption", "scandal", "investigation",
                      "money laundering", "insider trading", "misconduct", "regulatory fine",
                      "penalty", "lawsuit", "non-compliance", "breach"],
    "Greenwashing":  ["greenwashing", "misleading", "false disclosure", "esg fraud",
                      "misleading claims", "false sustainability"],
}
ALL_KW = [kw for group in CONTROVERSY_KEYWORDS.values() for kw in group]


def fetch(query: str, n: int = 10):
    if not DEPS:
        return []
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(url)
    except Exception:
        return []
    out = []
    for e in feed.entries[: n * 3]:
        text = f"{e.get('title','')}. {re.sub(r'<[^>]+>', '', e.get('summary',''))}".strip().lower()
        if not text or text == ".":
            continue
        pub = None
        if getattr(e, "published_parsed", None):
            try:
                pub = datetime(*e.published_parsed[:6])
            except Exception:
                pub = None
        if pub is None or pub < CUTOFF:
            continue
        out.append(text)
    return out[:n]


def count_flags(articles):
    if not articles:
        return 0, "Insufficient Data", 0
    flagged = 0
    for text in articles:
        if any(kw in text for kw in ALL_KW):
            flagged += 1
    risk = "Low" if flagged == 0 else "Medium" if flagged <= 2 else "High"
    conf = "Low Confidence" if len(articles) < MIN_ARTICLES else risk
    return flagged, conf, len(articles)


def main():
    print("Task 4 — Controversy detection (Google News RSS)")
    print(f"Window: last {MONTHS_BACK} months · {len(ALL_KW)} keywords / 4 families")
    print("=" * 68)
    if not DEPS:
        print("feedparser not installed — showing method only.")
    for c in ANCHORS:
        arts = fetch(c["controversy_query"])
        flags, risk, n = count_flags(arts)
        print(f"  {c['name']:<20} flags={flags}  risk={risk:<16} ({n} articles scanned)")
        time.sleep(0.5)
    print("\n(dry run — merge counts into master_data.csv in production)")


if __name__ == "__main__":
    main()
