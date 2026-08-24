from __future__ import annotations
import csv
import math
import os
from dataclasses import dataclass, field

from weights import (PILLAR_SIGNALS, CROSS_SIGNALS, PILLAR_LABELS,
                     weights_for, rationale, group_for,
                     HIGH_GROWTH, MATURE)

# modes
SECTOR_RELATIVE = "sector"
UNIVERSE_RELATIVE = "universe"

# shrinkage
SHRINK_K = 5.0

TREND_VALUE = {"Increasing": 1.0, "Stable": 0.5, "Decreasing": 0.0}

# sliders
# app.py builds one slider per key. These are MULTIPLIERS on the lookup table, so
# 1.0 means "use the table as written" and 0 means "switch this axis off".
DEFAULT_WEIGHTS = {
    "E": 1.0, "S": 1.0, "G": 1.0, "I": 1.0,
    "sentiment": 1.0, "say_do": 1.0,
}

# legacy
# the original seven signal keys, still computed so the existing drilldown renders
POSITIVE_SIGNALS = [
    "esg_cagr", "hiring_growth", "ai_job_pct",
    "ai_patent_count", "ai_earnings_mentions", "sentiment_trend",
]
RISK_SIGNALS = ["controversy"]

LEGACY_RAW = {
    "esg_cagr": "esg_cagr_5yr",
    "hiring_growth": "hires_growth",
    "ai_job_pct": "ai_job_pct",
    "ai_patent_count": "ai_patent_count",
    "ai_earnings_mentions": "ai_earnings_mentions",
    "controversy": "controversy_flags_12mo",
}


# --------------------------------------------------------------------------- #
# 1. MODEL                                                                     #
# --------------------------------------------------------------------------- #

@dataclass
class Company:
    company: str
    country: str
    sector: str
    ticker: str
    company_stage: str
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
    raw: dict = field(default_factory=dict)
    signals_norm: dict = field(default_factory=dict)
    pillar_scores: dict = field(default_factory=dict)
    pillar_weights: dict = field(default_factory=dict)
    say_do_gap: float = 0.0
    momentum_score: float = 0.0
    quadrant: str = ""

    # explain
    def why_weights(self) -> str:
        return rationale(self.sector, self.company_stage)


# number
def _f(v, default=0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


# load
def load_master(csv_path: str) -> list[Company]:
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(Company(
                company=r["company"], country=r["country"], sector=r["sector"],
                ticker=r["ticker"],
                company_stage=r.get("company_stage") or MATURE,
                esg_score_today=_f(r["esg_score_today"]),
                esg_cagr_5yr=_f(r["esg_cagr_5yr"]),
                revenue_usd_b=_f(r["revenue_usd_b"]),
                hires_growth=_f(r["hires_growth"]),
                ai_job_pct=_f(r["ai_job_pct"]),
                ai_patent_count=_f(r["ai_patent_count"]),
                ai_earnings_mentions=_f(r["ai_earnings_mentions"]),
                sentiment_score=_f(r["sentiment_score"]),
                sentiment_trend=r.get("sentiment_trend", "Stable"),
                controversy_flags_12mo=int(_f(r.get("controversy_flags_12mo"))),
                data_source=r.get("data_source", ""),
                say_do_gap=_f(r.get("say_do_gap")),
                raw={k: r[k] for k in r},
            ))
    return rows


# --------------------------------------------------------------------------- #
# 2. NORMALISATION                                                             #
# --------------------------------------------------------------------------- #

# extract
def _raw_signal(c: Company, key: str) -> float:
    if key == "sentiment_trend":
        return 0.7 * TREND_VALUE.get(c.sentiment_trend, 0.5) + 0.3 * c.sentiment_score
    if key in LEGACY_RAW:
        return _f(c.raw.get(LEGACY_RAW[key]), getattr(c, LEGACY_RAW[key], 0.0))
    return _f(c.raw.get(key))


# zscore
def _z(values: list[float]) -> tuple[float, float]:
    n = len(values)
    if n == 0:
        return 0.0, 1.0
    mu = sum(values) / n
    var = sum((v - mu) ** 2 for v in values) / n
    sd = math.sqrt(var)
    return mu, (sd if sd > 1e-12 else 1.0)


# squash
def _to_unit(z: float) -> float:
    return round(0.5 + 0.5 * math.tanh(z / 2.0), 4)


# trust
def shrink_lambda(n: int) -> float:
    return n / (n + SHRINK_K)


# normalise
def normalize(companies: list[Company], mode: str = SECTOR_RELATIVE) -> None:
    keys = sorted({k for sig in PILLAR_SIGNALS.values() for k, _, _ in sig}
                  | {k for k, _, _ in CROSS_SIGNALS}
                  | set(POSITIVE_SIGNALS) | set(RISK_SIGNALS))

    by_sector: dict[str, list[Company]] = {}
    for c in companies:
        by_sector.setdefault(c.sector, []).append(c)

    for key in keys:
        uni = [_raw_signal(c, key) for c in companies]
        umu, usd = _z(uni)
        smu: dict[str, tuple[float, float]] = {}
        for sec, members in by_sector.items():
            smu[sec] = _z([_raw_signal(c, key) for c in members])

        for c in companies:
            v = _raw_signal(c, key)
            zu = (v - umu) / usd
            if mode == UNIVERSE_RELATIVE:
                z = zu
            else:
                mu, sd = smu[c.sector]
                zs = (v - mu) / sd
                lam = shrink_lambda(len(by_sector[c.sector]))
                z = lam * zs + (1 - lam) * zu
            c.signals_norm[key] = _to_unit(z)


# audit
def shrinkage_report(companies: list[Company]) -> list[dict]:
    counts: dict[str, int] = {}
    for c in companies:
        counts[c.sector] = counts.get(c.sector, 0) + 1
    return sorted(({"sector": s, "n": n,
                    "sector_trust": round(shrink_lambda(n), 2),
                    "universe_trust": round(1 - shrink_lambda(n), 2)}
                   for s, n in counts.items()),
                  key=lambda r: -r["n"])


# --------------------------------------------------------------------------- #
# 3. PILLARS AND COMPOSITE                                                     #
# --------------------------------------------------------------------------- #

# blend
def compute_pillars(companies: list[Company]) -> None:
    for c in companies:
        for pillar, signals in PILLAR_SIGNALS.items():
            num = den = 0.0
            for key, w, is_risk in signals:
                v = c.signals_norm.get(key, 0.5)
                num += w * ((1.0 - v) if is_risk else v)
                den += w
            c.pillar_scores[pillar] = round(num / den * 100, 1) if den else 50.0


# composite
def compute_momentum(companies: list[Company], weights: dict | None = None) -> None:
    mult = dict(DEFAULT_WEIGHTS)
    if weights:
        mult.update({k: v for k, v in weights.items() if k in mult})

    for c in companies:
        table = weights_for(c.sector, c.company_stage)
        eff = {p: table[p] * mult.get(p, 1.0) for p in ("E", "S", "G", "I")}
        total = sum(eff.values())
        if total <= 0:
            eff, total = {p: 1.0 for p in eff}, 4.0
        c.pillar_weights = {p: round(v / total, 3) for p, v in eff.items()}

        base = sum(c.pillar_weights[p] * c.pillar_scores[p] for p in eff)

        adj = 0.0
        for key, w, is_risk in CROSS_SIGNALS:
            slider = mult.get("sentiment" if key == "sentiment_trend" else "say_do", 1.0)
            v = c.signals_norm.get(key, 0.5)
            adj += w * slider * ((0.5 - v) if is_risk else (v - 0.5)) * 100

        c.momentum_score = round(max(0.0, min(100.0, base + adj)), 1)


# --------------------------------------------------------------------------- #
# 4. QUADRANTS AND BENCHMARKS                                                  #
# --------------------------------------------------------------------------- #

# median
def _median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    if not n:
        return 0.0
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


# split
def assign_quadrants(companies: list[Company],
                     esg_threshold: float | None = None,
                     momentum_threshold: float | None = None) -> dict:
    esg_t = esg_threshold if esg_threshold is not None else _median(
        [c.esg_score_today for c in companies])
    mom_t = momentum_threshold if momentum_threshold is not None else _median(
        [c.momentum_score for c in companies])

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


# benchmarks
def benchmarks(companies: list[Company]) -> dict:
    out = {"universe": {
        "esg": round(_median([c.esg_score_today for c in companies]), 1),
        "momentum": round(_median([c.momentum_score for c in companies]), 1)}}
    by_sector: dict[str, list[Company]] = {}
    for c in companies:
        by_sector.setdefault(c.sector, []).append(c)
    for sec, members in by_sector.items():
        out[sec] = {
            "n": len(members),
            "esg": round(_median([m.esg_score_today for m in members]), 1),
            "momentum": round(_median([m.momentum_score for m in members]), 1),
        }
    return out


QUADRANT_META = {
    "Hidden Winners":    {"color": "#16b8a6", "note": "Low score, improving fast. Tomorrow's leaders the market hasn't priced yet. The opportunity lives here."},
    "Future Leaders":    {"color": "#3b82f6", "note": "High score and still improving. Compounding quality with a strong ESG moat."},
    "Value Traps":       {"color": "#f59e0b", "note": "Low score and declining. Structural ESG risk. Avoid or short."},
    "Overrated Leaders": {"color": "#ef4444", "note": "High score but deteriorating. The market still pays a premium. Likely to underperform."},
}


# --------------------------------------------------------------------------- #
# 5. ENTRY POINT                                                               #
# --------------------------------------------------------------------------- #

# run
def score_universe(csv_path: str | None = None, weights: dict | None = None,
                   esg_threshold: float | None = None,
                   momentum_threshold: float | None = None,
                   mode: str = SECTOR_RELATIVE):
    if csv_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(here, "data", "master_data.csv")
    companies = load_master(csv_path)
    normalize(companies, mode)
    compute_pillars(companies)
    compute_momentum(companies, weights)
    thresholds = assign_quadrants(companies, esg_threshold, momentum_threshold)
    companies.sort(key=lambda c: c.momentum_score, reverse=True)
    return companies, thresholds


# export
def write_scores(companies: list[Company], path: str, mode: str) -> None:
    cols = ["rank", "company", "ticker", "country", "sector", "sector_group",
            "company_stage", "norm_mode", "esg_score_today",
            "e_momentum", "s_momentum", "g_momentum", "i_momentum",
            "w_E", "w_S", "w_G", "w_I",
            "say_do_gap", "momentum_score", "quadrant", "weight_rationale"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, c in enumerate(companies, 1):
            w.writerow({
                "rank": i, "company": c.company, "ticker": c.ticker,
                "country": c.country, "sector": c.sector,
                "sector_group": group_for(c.sector),
                "company_stage": c.company_stage, "norm_mode": mode,
                "esg_score_today": c.esg_score_today,
                "e_momentum": c.pillar_scores["E"], "s_momentum": c.pillar_scores["S"],
                "g_momentum": c.pillar_scores["G"], "i_momentum": c.pillar_scores["I"],
                "w_E": c.pillar_weights["E"], "w_S": c.pillar_weights["S"],
                "w_G": c.pillar_weights["G"], "w_I": c.pillar_weights["I"],
                "say_do_gap": c.say_do_gap, "momentum_score": c.momentum_score,
                "quadrant": c.quadrant, "weight_rationale": c.why_weights(),
            })


# cli
def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=[SECTOR_RELATIVE, UNIVERSE_RELATIVE],
                    default=SECTOR_RELATIVE)
    ap.add_argument("--compare", action="store_true",
                    help="show how far each company moves when the toggle flips")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    companies, thresholds = score_universe(mode=args.mode)

    print(f"ESG Momentum 2.0 — {args.mode}-relative")
    print("=" * 96)
    print(f"Thresholds: ESG >= {thresholds['esg_threshold']} | "
          f"Momentum >= {thresholds['momentum_threshold']}\n")
    print(f"{'#':<4}{'Company':<22}{'Stage':<6}{'ESG':>6}{'Mom':>7}"
          f"{'E':>6}{'S':>6}{'G':>6}{'I':>6}{'SayDo':>7}  Quadrant")
    print("-" * 96)
    for i, c in enumerate(companies, 1):
        st = "HG" if c.company_stage == HIGH_GROWTH else "MAT"
        print(f"{i:<4}{c.company:<22}{st:<6}{c.esg_score_today:>6}{c.momentum_score:>7}"
              f"{c.pillar_scores['E']:>6}{c.pillar_scores['S']:>6}"
              f"{c.pillar_scores['G']:>6}{c.pillar_scores['I']:>6}"
              f"{c.say_do_gap:>7}  {c.quadrant}")

    print("\nSector-relative trust (shrinkage toward the universe when n is small):")
    for r in shrinkage_report(companies):
        print(f"  {r['sector']:<26} n={r['n']:<3} sector {r['sector_trust']:.0%} / "
              f"universe {r['universe_trust']:.0%}")

    if args.compare:
        other = UNIVERSE_RELATIVE if args.mode == SECTOR_RELATIVE else SECTOR_RELATIVE
        alt, _ = score_universe(mode=other)
        rank_a = {c.company: i for i, c in enumerate(companies, 1)}
        rank_b = {c.company: i for i, c in enumerate(alt, 1)}
        print(f"\nRank change, {args.mode} vs {other} (this is the demo toggle):")
        moves = sorted(((rank_b[k] - rank_a[k], k) for k in rank_a),
                       key=lambda t: -abs(t[0]))
        for d, name in moves[:10]:
            arrow = "up" if d > 0 else "down" if d < 0 else "flat"
            print(f"  {name:<24} {rank_a[name]:>2} -> {rank_b[name]:<3} ({arrow} {abs(d)})")

    out = os.path.join(here, "data", "scores.csv")
    write_scores(companies, out, args.mode)
    print(f"\nPer-pillar sub-scores written to {out}")


if __name__ == "__main__":
    main()
