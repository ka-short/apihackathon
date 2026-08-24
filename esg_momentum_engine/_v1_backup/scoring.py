from __future__ import annotations
import csv
import os
from dataclasses import dataclass, field

DEFAULT_WEIGHTS = {
    "esg_cagr": 1.3,
    "hiring_growth": 1.0,
    "ai_job_pct": 1.0,
    "ai_patent_count": 1.0,
    "ai_earnings_mentions": 1.0,
    "sentiment_trend": 0.7,
    "controversy": 1.5,
}

TREND_VALUE = {"Increasing": 1.0, "Stable": 0.5, "Decreasing": 0.0}

POSITIVE_SIGNALS = [
    "esg_cagr", "hiring_growth", "ai_job_pct",
    "ai_patent_count", "ai_earnings_mentions", "sentiment_trend",
]
RISK_SIGNALS = ["controversy"]


@dataclass
class Company:
    company: str
    country: str
    sector: str
    ticker: str
    esg_score_today: float
    esg_cagr_5yr: float
    revenue_usd_b: float
    hires_growth: float
    ai_job_pct: float
    ai_patent_count: float
    ai_earnings_mentions: float
    sentiment_score: float
    sentiment_trend: str
    controversy_flags_12mo: int
    data_source: str = ""
    signals_norm: dict = field(default_factory=dict)
    momentum_score: float = 0.0
    quadrant: str = ""


def load_master(csv_path: str) -> list[Company]:
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(Company(
                company=r["company"],
                country=r["country"],
                sector=r["sector"],
                ticker=r["ticker"],
                esg_score_today=float(r["esg_score_today"]),
                esg_cagr_5yr=float(r["esg_cagr_5yr"]),
                revenue_usd_b=float(r["revenue_usd_b"]),
                hires_growth=float(r["hires_growth"]),
                ai_job_pct=float(r["ai_job_pct"]),
                ai_patent_count=float(r["ai_patent_count"]),
                ai_earnings_mentions=float(r["ai_earnings_mentions"]),
                sentiment_score=float(r["sentiment_score"]),
                sentiment_trend=r["sentiment_trend"],
                controversy_flags_12mo=int(r["controversy_flags_12mo"]),
                data_source=r.get("data_source", ""),
            ))
    return rows


def _minmax(values: list[float]) -> callable:
    lo, hi = min(values), max(values)
    span = hi - lo
    if span == 0:
        return lambda v: 0.5
    return lambda v: (v - lo) / span


def _raw_signal(c: Company, key: str) -> float:
    if key == "esg_cagr":
        return c.esg_cagr_5yr
    if key == "hiring_growth":
        return c.hires_growth
    if key == "ai_job_pct":
        return c.ai_job_pct
    if key == "ai_patent_count":
        return c.ai_patent_count
    if key == "ai_earnings_mentions":
        return c.ai_earnings_mentions
    if key == "sentiment_trend":
        return 0.7 * TREND_VALUE.get(c.sentiment_trend, 0.5) + 0.3 * c.sentiment_score
    if key == "controversy":
        return float(c.controversy_flags_12mo)
    raise KeyError(key)


def normalize(companies: list[Company]) -> None:
    all_keys = POSITIVE_SIGNALS + RISK_SIGNALS
    scalers = {}
    for key in all_keys:
        col = [_raw_signal(c, key) for c in companies]
        scalers[key] = _minmax(col)
    for c in companies:
        c.signals_norm = {key: scalers[key](_raw_signal(c, key)) for key in all_keys}


def compute_momentum(companies: list[Company], weights: dict | None = None) -> None:
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    pos_weight_sum = sum(w[k] for k in POSITIVE_SIGNALS)
    risk_weight_sum = sum(w[k if k != "controversy" else "controversy"] for k in RISK_SIGNALS)
    total_weight = pos_weight_sum + risk_weight_sum

    for c in companies:
        pos = sum(w[k] * c.signals_norm[k] for k in POSITIVE_SIGNALS)
        risk = w["controversy"] * c.signals_norm["controversy"]
        raw = pos - risk
        c.momentum_score = round(
            (raw + risk_weight_sum) / total_weight * 100, 1
        )


def _median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def assign_quadrants(companies: list[Company],
                     esg_threshold: float | None = None,
                     momentum_threshold: float | None = None) -> dict:
    esg_t = esg_threshold if esg_threshold is not None else _median([c.esg_score_today for c in companies])
    mom_t = momentum_threshold if momentum_threshold is not None else _median([c.momentum_score for c in companies])

    for c in companies:
        high_esg = c.esg_score_today >= esg_t
        high_mom = c.momentum_score >= mom_t
        if not high_esg and high_mom:
            c.quadrant = "Hidden Winners"
        elif high_esg and high_mom:
            c.quadrant = "Future Leaders"
        elif not high_esg and not high_mom:
            c.quadrant = "Value Traps"
        else:
            c.quadrant = "Overrated Leaders"

    return {"esg_threshold": round(esg_t, 1), "momentum_threshold": round(mom_t, 1)}


QUADRANT_META = {
    "Hidden Winners":    {"color": "#16b8a6", "note": "Low score, improving fast. Tomorrow's leaders the market hasn't priced yet. The opportunity lives here."},
    "Future Leaders":    {"color": "#3b82f6", "note": "High score and still improving. Compounding quality with a strong ESG moat."},
    "Value Traps":       {"color": "#f59e0b", "note": "Low score and declining. Structural ESG risk. Avoid or short."},
    "Overrated Leaders": {"color": "#ef4444", "note": "High score but deteriorating. The market still pays a premium. Likely to underperform."},
}


def score_universe(csv_path: str | None = None, weights: dict | None = None,
                   esg_threshold: float | None = None,
                   momentum_threshold: float | None = None):
    if csv_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(here, "data", "master_data.csv")
    companies = load_master(csv_path)
    normalize(companies)
    compute_momentum(companies, weights)
    thresholds = assign_quadrants(companies, esg_threshold, momentum_threshold)
    companies.sort(key=lambda c: c.momentum_score, reverse=True)
    return companies, thresholds


if __name__ == "__main__":
    companies, thresholds = score_universe()
    print("ESG Momentum 2.0 — scored universe")
    print("=" * 74)
    print(f"Thresholds: ESG >= {thresholds['esg_threshold']} | "
          f"Momentum >= {thresholds['momentum_threshold']}\n")
    print(f"{'Rank':<5}{'Company':<22}{'ESG':>6}{'Momentum':>10}  Quadrant")
    print("-" * 74)
    for i, c in enumerate(companies, 1):
        print(f"{i:<5}{c.company:<22}{c.esg_score_today:>6}{c.momentum_score:>10}  {c.quadrant}")

    print("\nQuadrant counts:")
    from collections import Counter
    for q, n in Counter(c.quadrant for c in companies).most_common():
        print(f"  {q:<20} {n}")
