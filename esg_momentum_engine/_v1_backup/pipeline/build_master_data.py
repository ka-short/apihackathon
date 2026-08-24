from __future__ import annotations
import csv
import os
from datetime import datetime

# --------------------------------------------------------------------------- #
# 1. THE UNIVERSE — 24 ASEAN companies, hand-calibrated                        #
# --------------------------------------------------------------------------- #
# Column meanings for the raw authored fields:
#   esg_today / esg_5yr : ESG rating 0-100 (higher = better) now vs 5 years ago.
#                         The GAP between them is the original Momentum 1.0 signal.
#   rev_b               : annual revenue, USD billions (ballpark from public filings)
#   h6 / hprev          : new hires last 6 months vs the prior 6 months
#   ai_job              : % of current job postings that are AI/ML/data roles (0-100)
#   patents             : AI-related patent filings, trailing 12 months
#   ai_ment             : count of AI mentions in the latest earnings call
#   sent                : news sentiment 0-1 (1 = very positive)
#   trend               : direction of that sentiment over the last 12 months
#   contro              : count of high-controversy news flags in last 12 months
#
# The five ORIGINAL companies (PLDT, PTTEP, Telkom, Sea, CIMB) are kept as
# real-data anchors and marked anchor=True.

UNIVERSE = [
    # ---- HIDDEN WINNERS: low ESG today, strong forward momentum ------------- #
    dict(company="Sea Limited",        country="Singapore",  sector="Technology",             ticker="SE",       esg_today=44.6, esg_5yr=38.0, rev_b=16.80, h6=8200, hprev=6400, ai_job=34, patents=12, ai_ment=11, sent=0.62, trend="Increasing", contro=0, anchor=True),
    dict(company="Grab Holdings",      country="Singapore",  sector="Technology",             ticker="GRAB",     esg_today=46.0, esg_5yr=39.5, rev_b=2.80,  h6=4200, hprev=3500, ai_job=30, patents=8,  ai_ment=9,  sent=0.60, trend="Increasing", contro=1, anchor=False),
    dict(company="GoTo Group",         country="Indonesia",  sector="Technology",             ticker="GOTO",     esg_today=43.0, esg_5yr=36.0, rev_b=1.10,  h6=3200, hprev=2600, ai_job=31, patents=5,  ai_ment=8,  sent=0.55, trend="Increasing", contro=1, anchor=False),
    dict(company="FPT Corporation",    country="Vietnam",    sector="Technology",             ticker="FPT",      esg_today=50.0, esg_5yr=42.0, rev_b=2.20,  h6=5200, hprev=4200, ai_job=40, patents=18, ai_ment=13, sent=0.66, trend="Increasing", contro=0, anchor=False),
    dict(company="Vingroup",           country="Vietnam",    sector="Consumer Cyclical",      ticker="VIC",      esg_today=41.0, esg_5yr=36.5, rev_b=5.50,  h6=6000, hprev=5200, ai_job=22, patents=9,  ai_ment=7,  sent=0.52, trend="Increasing", contro=2, anchor=False),
    dict(company="PLDT",               country="Philippines",sector="Communication Services", ticker="TEL",      esg_today=52.3, esg_5yr=48.5, rev_b=3.59,  h6=470,  hprev=440,  ai_job=14, patents=4,  ai_ment=6,  sent=0.55, trend="Increasing", contro=1, anchor=True),

    # ---- FUTURE LEADERS: high ESG today, still improving -------------------- #
    dict(company="DBS Group",          country="Singapore",  sector="Financial Services",     ticker="D05",      esg_today=74.0, esg_5yr=66.0, rev_b=20.20, h6=3400, hprev=2900, ai_job=28, patents=22, ai_ment=14, sent=0.68, trend="Increasing", contro=0, anchor=False),
    dict(company="CapitaLand Invest",  country="Singapore",  sector="Real Estate",            ticker="9CI",      esg_today=78.0, esg_5yr=70.0, rev_b=2.10,  h6=1600, hprev=1350, ai_job=18, patents=6,  ai_ment=6,  sent=0.64, trend="Increasing", contro=0, anchor=False),
    dict(company="CIMB Group",         country="Malaysia",   sector="Financial Services",     ticker="1023.KL",  esg_today=67.8, esg_5yr=58.0, rev_b=5.21,  h6=1300, hprev=1250, ai_job=20, patents=7,  ai_ment=8,  sent=0.56, trend="Increasing", contro=0, anchor=True),
    dict(company="Bank Central Asia",  country="Indonesia",  sector="Financial Services",     ticker="BBCA",     esg_today=71.0, esg_5yr=62.0, rev_b=6.80,  h6=2600, hprev=2200, ai_job=19, patents=5,  ai_ment=7,  sent=0.62, trend="Increasing", contro=0, anchor=False),
    dict(company="Kasikornbank",       country="Thailand",   sector="Financial Services",     ticker="KBANK.BK", esg_today=70.0, esg_5yr=63.0, rev_b=7.20,  h6=2100, hprev=1950, ai_job=21, patents=6,  ai_ment=9,  sent=0.60, trend="Increasing", contro=0, anchor=False),
    dict(company="Maybank",            country="Malaysia",   sector="Financial Services",     ticker="1155.KL",  esg_today=72.0, esg_5yr=65.0, rev_b=6.50,  h6=1900, hprev=1700, ai_job=17, patents=4,  ai_ment=6,  sent=0.58, trend="Increasing", contro=0, anchor=False),
    dict(company="Siam Cement (SCG)",  country="Thailand",   sector="Basic Materials",        ticker="SCC.BK",   esg_today=66.0, esg_5yr=60.0, rev_b=15.50, h6=2600, hprev=2400, ai_job=11, patents=9,  ai_ment=5,  sent=0.58, trend="Increasing", contro=1, anchor=False),
    dict(company="Astra International", country="Indonesia",  sector="Consumer Cyclical",      ticker="ASII",     esg_today=63.0, esg_5yr=57.0, rev_b=20.00, h6=5000, hprev=4400, ai_job=15, patents=6,  ai_ment=5,  sent=0.60, trend="Increasing", contro=1, anchor=False),

    # ---- OVERRATED LEADERS: high ESG today, momentum fading ----------------- #
    dict(company="Singtel",            country="Singapore",  sector="Communication Services", ticker="Z74",      esg_today=73.0, esg_5yr=74.0, rev_b=11.50, h6=1800, hprev=1900, ai_job=14, patents=8,  ai_ment=6,  sent=0.52, trend="Stable",     contro=1, anchor=False),
    dict(company="Tenaga Nasional",    country="Malaysia",   sector="Utilities",              ticker="5347.KL",  esg_today=68.0, esg_5yr=69.0, rev_b=12.00, h6=2200, hprev=2400, ai_job=7,  patents=3,  ai_ment=3,  sent=0.48, trend="Decreasing", contro=2, anchor=False),
    dict(company="Airports of Thailand",country="Thailand",  sector="Industrials",            ticker="AOT.BK",   esg_today=64.0, esg_5yr=66.0, rev_b=3.20,  h6=1200, hprev=1300, ai_job=8,  patents=2,  ai_ment=3,  sent=0.47, trend="Decreasing", contro=1, anchor=False),
    dict(company="Telkom Indonesia",   country="Indonesia",  sector="Communication Services", ticker="TLK",      esg_today=58.4, esg_5yr=60.0, rev_b=2.18,  h6=260,  hprev=290,  ai_job=12, patents=4,  ai_ment=5,  sent=0.50, trend="Decreasing", contro=5, anchor=True),

    # ---- VALUE TRAPS: low ESG today, declining ----------------------------- #
    dict(company="PTTEP",              country="Thailand",   sector="Energy",                 ticker="PTTEP.BK", esg_today=55.0, esg_5yr=63.0, rev_b=8.87,  h6=700,  hprev=830,  ai_job=8,  patents=2,  ai_ment=4,  sent=0.44, trend="Decreasing", contro=3, anchor=True),
    dict(company="Genting Singapore",  country="Singapore",  sector="Consumer Cyclical",      ticker="G13",      esg_today=48.0, esg_5yr=52.0, rev_b=1.60,  h6=900,  hprev=1100, ai_job=6,  patents=1,  ai_ment=2,  sent=0.42, trend="Decreasing", contro=2, anchor=False),
    dict(company="Top Glove",          country="Malaysia",   sector="Healthcare",             ticker="7113.KL",  esg_today=45.0, esg_5yr=50.0, rev_b=1.00,  h6=800,  hprev=1400, ai_job=5,  patents=3,  ai_ment=1,  sent=0.38, trend="Decreasing", contro=4, anchor=False),
    dict(company="Golden Agri-Res.",   country="Singapore",  sector="Consumer Defensive",     ticker="E5H",      esg_today=42.0, esg_5yr=45.0, rev_b=9.50,  h6=1500, hprev=1700, ai_job=4,  patents=1,  ai_ment=1,  sent=0.40, trend="Decreasing", contro=3, anchor=False),
    dict(company="First Resources",    country="Singapore",  sector="Consumer Defensive",     ticker="EB5",      esg_today=47.0, esg_5yr=51.0, rev_b=1.10,  h6=650,  hprev=780,  ai_job=4,  patents=0,  ai_ment=1,  sent=0.43, trend="Decreasing", contro=2, anchor=False),
    dict(company="Bumi Resources",     country="Indonesia",  sector="Energy",                 ticker="BUMI",     esg_today=39.0, esg_5yr=46.0, rev_b=6.40,  h6=900,  hprev=1150, ai_job=3,  patents=0,  ai_ment=0,  sent=0.36, trend="Decreasing", contro=4, anchor=False),
]


# --------------------------------------------------------------------------- #
# 2. DERIVED FIELDS                                                            #
# --------------------------------------------------------------------------- #
def esg_cagr_5yr(today: float, five_yr_ago: float) -> float:
    if five_yr_ago <= 0:
        return 0.0
    return (today / five_yr_ago) ** (1 / 5) - 1


def hires_growth(h6: int, hprev: int) -> float:
    if hprev <= 0:
        return 0.0
    return (h6 - hprev) / hprev


def hires_per_m_rev(h6: int, rev_b: float) -> float:
    rev_m = rev_b * 1000.0
    if rev_m <= 0:
        return 0.0
    return h6 / rev_m


# --------------------------------------------------------------------------- #
# 3. BUILD + EXPORT                                                            #
# --------------------------------------------------------------------------- #
FIELDNAMES = [
    "company", "country", "sector", "ticker",
    "esg_score_today", "esg_score_5yr_ago", "esg_cagr_5yr",
    "revenue_usd_b",
    "hires_6mo", "hires_prev_6mo", "hires_growth", "hires_per_m_rev",
    "ai_job_pct", "ai_patent_count", "ai_earnings_mentions",
    "sentiment_score", "sentiment_trend", "controversy_flags_12mo",
    "data_source",
]


def build_rows() -> list[dict]:
    rows = []
    for c in UNIVERSE:
        rows.append({
            "company": c["company"],
            "country": c["country"],
            "sector": c["sector"],
            "ticker": c["ticker"],
            "esg_score_today": round(c["esg_today"], 1),
            "esg_score_5yr_ago": round(c["esg_5yr"], 1),
            "esg_cagr_5yr": round(esg_cagr_5yr(c["esg_today"], c["esg_5yr"]), 4),
            "revenue_usd_b": round(c["rev_b"], 2),
            "hires_6mo": c["h6"],
            "hires_prev_6mo": c["hprev"],
            "hires_growth": round(hires_growth(c["h6"], c["hprev"]), 4),
            "hires_per_m_rev": round(hires_per_m_rev(c["h6"], c["rev_b"]), 3),
            "ai_job_pct": c["ai_job"],
            "ai_patent_count": c["patents"],
            "ai_earnings_mentions": c["ai_ment"],
            "sentiment_score": round(c["sent"], 2),
            "sentiment_trend": c["trend"],
            "controversy_flags_12mo": c["contro"],
            "data_source": "real-anchor (calibrated)" if c["anchor"] else "illustrative (calibrated)",
        })
    return rows


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.abspath(os.path.join(out_dir, "master_data.csv"))

    rows = build_rows()
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    # ---- console summary --------------------------------------------------- #
    print("ESG Momentum Engine 2.0 — master dataset built")
    print("=" * 62)
    print(f"Companies : {len(rows)}")
    print(f"Sectors   : {len(set(r['sector'] for r in rows))}")
    print(f"Countries : {len(set(r['country'] for r in rows))}")
    print(f"Output    : {out_path}")
    print(f"Built at  : {datetime.now():%Y-%m-%d %H:%M}")
    print("-" * 62)
    print(f"{'Company':<22}{'ESG':>6}{'ESG CAGR':>10}{'HireΔ':>8}{'Sent':>6}{'Flags':>7}")
    for r in rows:
        print(f"{r['company']:<22}{r['esg_score_today']:>6}"
              f"{r['esg_cagr_5yr']*100:>9.1f}%{r['hires_growth']*100:>7.0f}%"
              f"{r['sentiment_score']:>6}{r['controversy_flags_12mo']:>7}")


if __name__ == "__main__":
    main()
