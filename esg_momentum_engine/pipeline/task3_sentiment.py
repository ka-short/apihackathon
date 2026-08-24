from __future__ import annotations
import re
import time
from datetime import datetime, timedelta
from anchors import ANCHORS

try:
    import feedparser
    from textblob import TextBlob
    DEPS = True
except ImportError:
    DEPS = False

MONTHS_BACK = 12
CUTOFF = datetime.now() - timedelta(days=MONTHS_BACK * 30)
MIN_ARTICLES = 3

ESG_POSITIVE = ["sustainable", "sustainability", "green", "renewable", "esg",
                "net zero", "carbon neutral", "clean energy", "governance",
                "diversity", "inclusion", "climate", "ethical", "responsible",
                "transparent", "community", "impact", "ai", "digital"]
ESG_NEGATIVE = ["violation", "scandal", "fine", "penalty", "lawsuit", "corruption",
                "fraud", "greenwashing", "controversy", "misconduct", "pollution",
                "bribery", "discrimination", "breach", "investigation", "boycott"]


def fetch(query: str, n: int = 6):
    if not DEPS:
        return []
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(url)
    except Exception:
        return []
    out = []
    for e in feed.entries[: n * 3]:
        text = f"{e.get('title','')}. {re.sub(r'<[^>]+>', '', e.get('summary',''))}".strip()
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
        out.append({"text": text, "pub": pub})
    out.sort(key=lambda a: a["pub"])
    return out[:n]


def score(articles):
    if not articles:
        return 0.50, "Insufficient Data", 0
    scores = []
    for a in articles:
        low = a["text"].lower()
        base = TextBlob(a["text"]).sentiment.polarity
        boost = sum(0.05 for k in ESG_POSITIVE if k in low) - sum(0.05 for k in ESG_NEGATIVE if k in low)
        scores.append(round((max(-1, min(1, base + boost)) + 1) / 2, 3))
    final = round(sum(scores) / len(scores), 2)
    if len(scores) < MIN_ARTICLES:
        return final, f"Low Confidence (<{MIN_ARTICLES} articles)", len(scores)
    mid = len(scores) // 2
    diff = (sum(scores[mid:]) / len(scores[mid:])) - (sum(scores[:mid]) / mid)
    trend = "Increasing" if diff > 0.05 else "Decreasing" if diff < -0.05 else "Stable"
    return final, trend, len(scores)


def main():
    print("Task 3 — News sentiment + trend (TextBlob + Google News RSS)")
    print(f"Window: last {MONTHS_BACK} months (cutoff {CUTOFF:%Y-%m-%d})")
    print("=" * 68)
    if not DEPS:
        print("feedparser/textblob not installed — showing method only.")
    for c in ANCHORS:
        arts = fetch(c["news_query"])
        s, trend, n = score(arts)
        print(f"  {c['name']:<20} score={s:<5} trend={trend:<28} ({n} articles)")
        time.sleep(0.5)
    print("\n(dry run — merge these into master_data.csv in production)")


if __name__ == "__main__":
    main()
