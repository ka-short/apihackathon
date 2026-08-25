from __future__ import annotations
import time
from .http import get_json, ProviderError

BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

NEG_TONE = -2.0
WINDOW = "12months"
POLITE_SLEEP = 1.2

# pillars
# claims
# the TALK side of the say-do gap. These are the phrases companies use when they
# announce an ESG commitment, so counting them measures how loudly a company is
# promising - independent of whether it delivers.
CLAIM_TERMS = [
    "net zero", "carbon neutral", "carbon neutrality", "net-zero target",
    "science-based target", "emissions target", "emission reduction target",
    "sustainability commitment", "ESG commitment", "sustainability pledge",
    "pledges to", "commits to reduce", "renewable energy target",
    "sustainability roadmap", "decarbonisation plan", "decarbonization plan",
    "green financing target", "sustainability-linked",
]

# pillars
PILLAR_TERMS = {
    "e": {
        "themes": ["ENV_OIL", "ENV_MINING", "ENV_CLIMATECHANGE", "ENV_COAL",
                   "ENV_FORESTRY", "ENV_WATERWAYS", "ENV_POACHING",
                   "ENV_SPECIESENDANGERED"],
        "words": ["pollution", "oil spill", "emissions breach", "environmental fine",
                  "deforestation", "toxic waste", "haze", "permit revoked",
                  "environmental violation"],
    },
    "s": {
        "themes": ["STRIKE", "LABOR_STANDARDS", "WORKING_CONDITIONS",
                   "COLLECTIVE_BARGAINING", "DISCRIMINATION", "HUMAN_RIGHTS_ABUSES"],
        "words": ["strike", "layoffs", "forced labour", "forced labor",
                  "workplace death", "safety incident", "discrimination suit",
                  "union dispute", "wage theft", "data breach"],
    },
    "g": {
        "themes": ["CORRUPTION", "TRIAL", "SCANDAL", "LEGISLATION"],
        "words": ["fraud", "bribery", "corruption probe", "regulatory fine",
                  "accounting irregularities", "lawsuit", "insider trading",
                  "board resignation", "auditor resigned"],
    },
}


# escape
def _q(company: str, pillar: str | None) -> str:
    name = f'"{company}"'
    if pillar is None:
        return name
    t = PILLAR_TERMS[pillar]
    themes = " OR ".join(f"theme:{x}" for x in t["themes"])
    words = " OR ".join(f'"{w}"' for w in t["words"])
    return f"{name} ({themes} OR {words})"


# claims
def claims(company: str, timespan: str = WINDOW) -> dict:
    words = " OR ".join(f'"{w}"' for w in CLAIM_TERMS)
    q = f'"{company}" ({words})'
    try:
        claim = tone_chart(q, timespan)
        overall = tone_chart(_q(company, None), timespan)
    except ProviderError:
        return {"claim_articles": None, "claim_share": None, "talk": None}

    share = (claim["total"] / overall["total"]) if overall["total"] else 0.0
    # blend volume with share so a giant with huge coverage does not
    # automatically out-talk a small company that promises constantly
    talk = 0.6 * min(1.0, claim["total"] / 25.0) + 0.4 * min(1.0, share / 0.06)
    return {
        "claim_articles": claim["total"],
        "total_articles": overall["total"],
        "claim_share": round(share, 4),
        "talk": round(min(1.0, talk), 3),
        "evidence_claims": examples_positive(q, 3, timespan),
    }


# pledges
def examples_positive(query: str, n: int = 3, timespan: str = WINDOW) -> list[dict]:
    try:
        data = get_json(BASE, {"query": query, "mode": "artlist",
                               "maxrecords": min(n, 250), "timespan": timespan,
                               "sort": "hybridrel", "format": "json"},
                        cache_hours=72)
    except ProviderError:
        return []
    return [{"title": a.get("title"), "url": a.get("url"),
             "domain": a.get("domain"), "date": a.get("seendate")}
            for a in (data.get("articles") or [])[:n]]


# histogram
def tone_chart(query: str, timespan: str = WINDOW) -> dict:
    data = get_json(BASE, {"query": query, "mode": "tonechart",
                           "timespan": timespan, "format": "json"},
                    cache_hours=72)
    bins = data.get("tonechart") or []
    total = sum(int(b.get("count", 0)) for b in bins)
    neg = sum(int(b.get("count", 0)) for b in bins
              if float(b.get("bin", 0)) <= NEG_TONE)
    weighted = sum(float(b.get("bin", 0)) * int(b.get("count", 0)) for b in bins)
    return {
        "total": total,
        "negative": neg,
        "neg_share": round(neg / total, 4) if total else 0.0,
        "mean_tone": round(weighted / total, 3) if total else 0.0,
    }


# headlines
def examples(query: str, n: int = 5, timespan: str = WINDOW) -> list[dict]:
    try:
        data = get_json(BASE, {"query": f"{query} tone<{NEG_TONE}", "mode": "artlist",
                               "maxrecords": min(n, 250), "timespan": timespan,
                               "sort": "hybridrel", "format": "json"},
                        cache_hours=72)
    except ProviderError:
        return []
    return [{"title": a.get("title"), "url": a.get("url"),
             "domain": a.get("domain"), "date": a.get("seendate")}
            for a in (data.get("articles") or [])[:n]]


# trend
def tone_trend(company: str) -> dict:
    try:
        recent = tone_chart(_q(company, None), "6months")
        prior = tone_chart(_q(company, None), "12months")
    except ProviderError:
        return {"sentiment_score": None, "sentiment_trend": None}
    older_total = max(0, prior["total"] - recent["total"])
    older_tone = ((prior["mean_tone"] * prior["total"] -
                   recent["mean_tone"] * recent["total"]) / older_total
                  if older_total else recent["mean_tone"])
    delta = recent["mean_tone"] - older_tone
    label = "Increasing" if delta > 0.3 else "Decreasing" if delta < -0.3 else "Stable"
    return {
        "sentiment_score": round(min(1.0, max(0.0, (recent["mean_tone"] + 10) / 20)), 3),
        "sentiment_trend": label,
        "tone_delta": round(delta, 3),
        "articles_12mo": prior["total"],
    }


# bucket
def to_flags(neg_count: int, neg_share: float) -> int:
    if neg_count < 3:
        return 0
    score = min(5.0, (neg_count / 25.0) + (neg_share * 6.0))
    return int(round(score))


# combine
def fetch(company: str, with_examples: bool = True) -> dict:
    out = {"company": company, "ok": False, "source": "gdelt-doc-2.0"}
    got = 0
    for pillar in ("e", "s", "g"):
        try:
            tc = tone_chart(_q(company, pillar))
            got += 1
        except ProviderError:
            out[f"controversy_flags_{pillar}"] = None
            out[f"controversy_intensity_{pillar}"] = None
            continue
        out[f"controversy_flags_{pillar}"] = to_flags(tc["negative"], tc["neg_share"])
        out[f"controversy_intensity_{pillar}"] = tc["neg_share"]
        out[f"controversy_articles_{pillar}"] = tc["negative"]
        if with_examples:
            out[f"evidence_{pillar}"] = examples(_q(company, pillar), 3)
        time.sleep(POLITE_SLEEP)
    out.update(tone_trend(company))
    out.update(claims(company))
    out["ok"] = got > 0
    return out


if __name__ == "__main__":
    import sys, json
    print(json.dumps(fetch(sys.argv[1] if len(sys.argv) > 1 else "Grab Holdings"),
                     indent=2))
