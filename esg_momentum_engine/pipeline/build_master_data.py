from __future__ import annotations
import argparse
import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from universe import (UNIVERSE, SECTOR_CARBON_BASE, classify_stage,
                      HIGH_GROWTH, MATURE)

# --------------------------------------------------------------------------- #
# 1. DERIVED FIELDS                                                            #
# --------------------------------------------------------------------------- #

# cagr
def cagr(today: float, five_yr_ago: float, years: float = 5.0) -> float:
    if five_yr_ago <= 0 or today <= 0:
        return 0.0
    return (today / five_yr_ago) ** (1 / years) - 1


# hiring
def hires_growth(h6: int, hprev: int) -> float:
    return (h6 - hprev) / hprev if hprev > 0 else 0.0


# intensity
def hires_per_m_rev(h6: int, rev_b: float) -> float:
    rev_m = rev_b * 1000.0
    return h6 / rev_m if rev_m > 0 else 0.0


# carbon
def synth_emissions_intensity(sector: str, e_today: float) -> float:
    base = SECTOR_CARBON_BASE.get(sector, 200.0)
    return round(base * (1.6 - e_today / 100.0), 1)


# saydo
def say_do_gap(commit: int, e_cagr: float, env_fines: int,
               emissions_trend: float | None) -> float:
    talk = min(1.0, commit / 12.0)
    proof = 0.0
    proof += max(0.0, min(1.0, (e_cagr + 0.03) / 0.09)) * 0.45
    proof += max(0.0, 1.0 - env_fines / 3.0) * 0.25
    if emissions_trend is None:
        proof += 0.15
    else:
        proof += max(0.0, min(1.0, (0.03 - emissions_trend) / 0.09)) * 0.30
    return round(max(0.0, talk - proof), 3)


# --------------------------------------------------------------------------- #
# 2. LIVE OVERLAY                                                              #
# --------------------------------------------------------------------------- #
PROVENANCE: dict[str, dict[str, str]] = {}


# record
def tag(company: str, column: str, source: str) -> None:
    PROVENANCE.setdefault(company, {})[column] = source


# overlay
def pull_live(c: dict, row: dict) -> None:
    from providers import yahoo_esg, gdelt, climatetrace, wikirate, yfin

    y = yahoo_esg.fetch(c["ticker"])
    if y.get("ok"):
        for p, col in (("total", "esg_score_today"), ("e", "esg_e_today"),
                       ("s", "esg_s_today"), ("g", "esg_g_today")):
            if y.get(f"{p}_today") is not None:
                row[col] = y[f"{p}_today"]
                tag(c["company"], col, "yahoo-sustainalytics")
        for p, col in (("total", "esg_cagr_5yr"), ("e", "esg_e_cagr"),
                       ("s", "esg_s_cagr"), ("g", "esg_g_cagr")):
            if y.get(f"{p}_cagr") is not None:
                row[col] = y[f"{p}_cagr"]
                tag(c["company"], col, "yahoo-sustainalytics")

    g = gdelt.fetch(c["company"])
    if g.get("ok"):
        for p in ("e", "s", "g"):
            if g.get(f"controversy_flags_{p}") is not None:
                row[f"controversy_flags_{p}"] = g[f"controversy_flags_{p}"]
                row[f"controversy_intensity_{p}"] = g[f"controversy_intensity_{p}"]
                tag(c["company"], f"controversy_flags_{p}", "gdelt")
        row["controversy_flags_12mo"] = sum(
            row.get(f"controversy_flags_{p}") or 0 for p in ("e", "s", "g"))
        row["env_fines_12mo"] = row.get("controversy_flags_e") or 0
        row["litigation_actions_12mo"] = row.get("controversy_flags_g") or 0
        if g.get("sentiment_score") is not None:
            row["sentiment_score"] = g["sentiment_score"]
            row["sentiment_trend"] = g["sentiment_trend"]
            tag(c["company"], "sentiment_score", "gdelt")

    f = yfin.fetch(c["ticker"])
    if f.get("ok"):
        for src, col in (("revenue_usd_b", "revenue_usd_b"),
                         ("rev_growth_yoy", "rev_growth_yoy"),
                         ("pe_ratio", "pe_ratio"), ("pb_ratio", "pb_ratio"),
                         ("insider_sell_ratio", "insider_sell_ratio")):
            if f.get(src) is not None:
                row[col] = f[src]
                tag(c["company"], col, "yfinance")

    ct = climatetrace.fetch(c["company"], row["revenue_usd_b"])
    if ct.get("ok"):
        row["emissions_intensity"] = ct["emissions_intensity"]
        row["emissions_intensity_trend"] = ct["emissions_intensity_trend"]
        tag(c["company"], "emissions_intensity", "climate-trace")
        tag(c["company"], "emissions_intensity_trend", "climate-trace")

    w = wikirate.fetch(c["company"])
    if w.get("ok"):
        for src, col in (("renewable_pct", "renewable_pct"),
                         ("women_workforce_pct", "diversity_women_pct"),
                         ("board_independence_pct", "board_independence_pct")):
            if w.get(src) is not None:
                row[col] = w[src]
                tag(c["company"], col, "wikirate")
            if w.get(f"{src}_trend") is not None:
                row[f"{col}_trend"] = w[f"{src}_trend"]
                tag(c["company"], f"{col}_trend", "wikirate")


# --------------------------------------------------------------------------- #
# 3. SCHEMA                                                                    #
# --------------------------------------------------------------------------- #
FIELDNAMES = [
    # identity
    "company", "country", "sector", "ticker", "company_stage",
    # blended, kept so nothing downstream breaks
    "esg_score_today", "esg_score_5yr_ago", "esg_cagr_5yr",
    # per pillar, new
    "esg_e_today", "esg_s_today", "esg_g_today",
    "esg_e_cagr", "esg_s_cagr", "esg_g_cagr",
    # financial
    "revenue_usd_b", "rev_growth_yoy", "pe_ratio", "pb_ratio",
    # environmental
    "emissions_intensity", "emissions_intensity_trend",
    "renewable_pct", "renewable_pct_trend",
    "green_capex_pct", "green_capex_pct_trend", "env_fines_12mo",
    # social
    "hires_6mo", "hires_prev_6mo", "hires_growth", "hires_per_m_rev",
    "employee_sentiment_trend",
    "diversity_women_pct", "diversity_women_pct_trend", "labour_controversy_12mo",
    # governance
    "board_independence_pct", "board_independence_pct_trend",
    "exec_turnover_12mo", "insider_sell_ratio", "litigation_actions_12mo",
    # innovation, pulled out of the pillars per handoff §3
    "ai_job_pct", "ai_patent_count", "ai_earnings_mentions",
    # crosscutting
    "sentiment_score", "sentiment_trend",
    "controversy_flags_12mo",
    "controversy_flags_e", "controversy_flags_s", "controversy_flags_g",
    "controversy_intensity_e", "controversy_intensity_s", "controversy_intensity_g",
    "stated_commitments", "say_do_gap",
    "data_source",
]


# assemble
def build_row(c: dict) -> dict:
    e_cagr = cagr(c["e_today"], c["e_5yr"])
    s_cagr = cagr(c["s_today"], c["s_5yr"])
    g_cagr = cagr(c["g_today"], c["g_5yr"])
    contro = c["contro_e"] + c["contro_s"] + c["contro_g"]
    emis = synth_emissions_intensity(c["sector"], c["e_today"])
    emis_trend = round(-e_cagr * 1.4, 4)

    row = {
        "company": c["company"], "country": c["country"], "sector": c["sector"],
        "ticker": c["ticker"],
        "company_stage": classify_stage(c["sector"], c["rev_g"]),

        "esg_score_today": round(c["esg_today"], 1),
        "esg_score_5yr_ago": round(c["esg_5yr"], 1),
        "esg_cagr_5yr": round(cagr(c["esg_today"], c["esg_5yr"]), 4),

        "esg_e_today": round(c["e_today"], 1),
        "esg_s_today": round(c["s_today"], 1),
        "esg_g_today": round(c["g_today"], 1),
        "esg_e_cagr": round(e_cagr, 4),
        "esg_s_cagr": round(s_cagr, 4),
        "esg_g_cagr": round(g_cagr, 4),

        "revenue_usd_b": round(c["rev_b"], 2),
        "rev_growth_yoy": round(c["rev_g"], 3),
        "pe_ratio": "", "pb_ratio": "",

        "emissions_intensity": emis,
        "emissions_intensity_trend": emis_trend,
        "renewable_pct": c["renew"],
        "renewable_pct_trend": round(e_cagr * 55, 2),
        "green_capex_pct": c["gcapex"],
        "green_capex_pct_trend": round(e_cagr * 40, 2),
        "env_fines_12mo": c["contro_e"],

        "hires_6mo": c["h6"], "hires_prev_6mo": c["hprev"],
        "hires_growth": round(hires_growth(c["h6"], c["hprev"]), 4),
        "hires_per_m_rev": round(hires_per_m_rev(c["h6"], c["rev_b"]), 3),
        "employee_sentiment_trend": round(s_cagr * 9, 3),
        "diversity_women_pct": c["women"],
        "diversity_women_pct_trend": round(s_cagr * 26, 2),
        "labour_controversy_12mo": c["contro_s"],

        "board_independence_pct": round(38 + c["g_today"] * 0.35, 1),
        "board_independence_pct_trend": round(g_cagr * 32, 2),
        "exec_turnover_12mo": max(0, round(2.4 - g_cagr * 26, 1)),
        "insider_sell_ratio": round(max(0.0, min(1.0, 0.55 - g_cagr * 4.2)), 3),
        "litigation_actions_12mo": c["contro_g"],

        "ai_job_pct": c["ai_job"], "ai_patent_count": c["patents"],
        "ai_earnings_mentions": c["ai_ment"],

        "sentiment_score": round(c["sent"], 2),
        "sentiment_trend": c["trend"],
        "controversy_flags_12mo": contro,
        "controversy_flags_e": c["contro_e"],
        "controversy_flags_s": c["contro_s"],
        "controversy_flags_g": c["contro_g"],
        "controversy_intensity_e": round(min(1.0, c["contro_e"] / 5.0), 3),
        "controversy_intensity_s": round(min(1.0, c["contro_s"] / 5.0), 3),
        "controversy_intensity_g": round(min(1.0, c["contro_g"] / 5.0), 3),
        "stated_commitments": c["commit"],
        "say_do_gap": 0.0,
        "data_source": "real-anchor (calibrated)" if c["anchor"] else "illustrative (calibrated)",
    }
    for col in FIELDNAMES:
        tag(c["company"], col, "calibrated")
    return row


# --------------------------------------------------------------------------- #
# 4. MAIN                                                                      #
# --------------------------------------------------------------------------- #

# entry
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="try the real providers")
    ap.add_argument("--only", default="", help="comma-separated tickers")
    args = ap.parse_args()

    keep = {t.strip() for t in args.only.split(",") if t.strip()}
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.abspath(os.path.join(here, "..", "data"))
    os.makedirs(out_dir, exist_ok=True)

    rows = []
    for c in UNIVERSE:
        row = build_row(c)
        if args.live and (not keep or c["ticker"] in keep):
            try:
                pull_live(c, row)
                row["company_stage"] = classify_stage(c["sector"], row["rev_growth_yoy"])
                row["controversy_flags_12mo"] = sum(
                    row.get(f"controversy_flags_{p}") or 0 for p in ("e", "s", "g"))
            except Exception as e:
                print(f"  ! live pull failed for {c['company']}: {e}", file=sys.stderr)
        row["say_do_gap"] = say_do_gap(
            row["stated_commitments"], row["esg_e_cagr"],
            row["env_fines_12mo"], row["emissions_intensity_trend"])
        rows.append(row)

    master = os.path.join(out_dir, "master_data.csv")
    with open(master, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)

    prov = os.path.join(out_dir, "provenance.csv")
    with open(prov, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["company", "column", "source", "is_real"])
        for comp, cols in PROVENANCE.items():
            for col, src in sorted(cols.items()):
                w.writerow([comp, col, src, "no" if src == "calibrated" else "yes"])

    real = sum(1 for cols in PROVENANCE.values()
               for s in cols.values() if s != "calibrated")
    total = sum(len(cols) for cols in PROVENANCE.values())
    stages = {}
    for r in rows:
        stages[r["company_stage"]] = stages.get(r["company_stage"], 0) + 1

    print("ESG Momentum Engine 2.0 — master dataset built")
    print("=" * 74)
    print(f"Mode      : {'LIVE (providers first)' if args.live else 'FROZEN (calibrated)'}")
    print(f"Companies : {len(rows)}   Sectors: {len(set(r['sector'] for r in rows))}"
          f"   Countries: {len(set(r['country'] for r in rows))}")
    print(f"Stages    : " + "  ".join(f"{k}={v}" for k, v in stages.items()))
    print(f"Real cells: {real}/{total} ({real/total*100:.0f}%)  -> see provenance.csv")
    print(f"Output    : {master}")
    print(f"Built at  : {datetime.now():%Y-%m-%d %H:%M}")
    print("-" * 74)
    print(f"{'Company':<22}{'Stage':<21}{'E':>5}{'S':>5}{'G':>5}"
          f"{'Ecagr':>8}{'flags e/s/g':>13}{'SayDo':>7}")
    for r in rows:
        st = "HG" if r["company_stage"] == HIGH_GROWTH else "MAT"
        print(f"{r['company']:<22}{r['company_stage']:<21}"
              f"{r['esg_e_today']:>5.0f}{r['esg_s_today']:>5.0f}{r['esg_g_today']:>5.0f}"
              f"{r['esg_e_cagr']*100:>7.1f}%"
              f"{str(r['controversy_flags_e'])+'/'+str(r['controversy_flags_s'])+'/'+str(r['controversy_flags_g']):>13}"
              f"{r['say_do_gap']:>7.2f}")


if __name__ == "__main__":
    main()
