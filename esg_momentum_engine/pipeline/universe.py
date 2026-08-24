from __future__ import annotations

# stages
HIGH_GROWTH = "High-Growth/Scaling"
MATURE = "Mature/Established"

# columns
#   esg_today/esg_5yr : blended rating 0-100, higher = better
#   e/s/g_today,_5yr  : same scale, per pillar; mean == blended
#   contro_*          : high-controversy news flags, 12mo, split by pillar
#   rev_g             : revenue growth YoY, the stage-classifier input
#   commit            : count of public, dated ESG commitments (say-do numerator)
#   women / board     : % women in workforce, % independent board members
#   renew / gcapex    : renewable share of energy, green share of capex
UNIVERSE = [
    # ---- hidden winners: low blended score, improving fast -------------------
    dict(company="Sea Limited", country="Singapore", sector="Technology", ticker="SE",
         esg_today=44.6, esg_5yr=38.0, e_today=62, e_5yr=58, s_today=40, s_5yr=33, g_today=31.8, g_5yr=23,
         rev_b=16.80, rev_g=0.28, h6=8200, hprev=6400, ai_job=34, patents=12, ai_ment=11,
         sent=0.62, trend="Increasing", contro_e=0, contro_s=0, contro_g=0,
         commit=6, women=41, renew=34, gcapex=11, anchor=True),
    dict(company="Grab Holdings", country="Singapore", sector="Technology", ticker="GRAB",
         esg_today=46.0, esg_5yr=39.5, e_today=60, e_5yr=55, s_today=42, s_5yr=35, g_today=36, g_5yr=28.5,
         rev_b=2.80, rev_g=0.24, h6=4200, hprev=3500, ai_job=30, patents=8, ai_ment=9,
         sent=0.60, trend="Increasing", contro_e=0, contro_s=1, contro_g=0,
         commit=8, women=39, renew=28, gcapex=14, anchor=False),
    dict(company="GoTo Group", country="Indonesia", sector="Technology", ticker="GOTO",
         esg_today=43.0, esg_5yr=36.0, e_today=58, e_5yr=52, s_today=39, s_5yr=32, g_today=32, g_5yr=24,
         rev_b=1.10, rev_g=0.19, h6=3200, hprev=2600, ai_job=31, patents=5, ai_ment=8,
         sent=0.55, trend="Increasing", contro_e=0, contro_s=1, contro_g=0,
         commit=7, women=37, renew=22, gcapex=9, anchor=False),
    dict(company="FPT Corporation", country="Vietnam", sector="Technology", ticker="FPT",
         esg_today=50.0, esg_5yr=42.0, e_today=61, e_5yr=54, s_today=48, s_5yr=40, g_today=41, g_5yr=32,
         rev_b=2.20, rev_g=0.21, h6=5200, hprev=4200, ai_job=40, patents=18, ai_ment=13,
         sent=0.66, trend="Increasing", contro_e=0, contro_s=0, contro_g=0,
         commit=5, women=36, renew=19, gcapex=8, anchor=False),
    dict(company="Vingroup", country="Vietnam", sector="Consumer Cyclical", ticker="VIC",
         esg_today=41.0, esg_5yr=36.5, e_today=38, e_5yr=34, s_today=44, s_5yr=39, g_today=41, g_5yr=36.5,
         rev_b=5.50, rev_g=0.17, h6=6000, hprev=5200, ai_job=22, patents=9, ai_ment=7,
         sent=0.52, trend="Increasing", contro_e=1, contro_s=0, contro_g=1,
         commit=9, women=33, renew=26, gcapex=21, anchor=False),
    dict(company="PLDT", country="Philippines", sector="Communication Services", ticker="TEL",
         esg_today=52.3, esg_5yr=48.5, e_today=55, e_5yr=52, s_today=52, s_5yr=48, g_today=49.9, g_5yr=45.5,
         rev_b=3.59, rev_g=0.04, h6=470, hprev=440, ai_job=14, patents=4, ai_ment=6,
         sent=0.55, trend="Increasing", contro_e=0, contro_s=0, contro_g=1,
         commit=6, women=44, renew=31, gcapex=13, anchor=True),

    # ---- future leaders: high score, still improving --------------------------
    dict(company="DBS Group", country="Singapore", sector="Financial Services", ticker="D05",
         esg_today=74.0, esg_5yr=66.0, e_today=70, e_5yr=60, s_today=74, s_5yr=67, g_today=78, g_5yr=71,
         rev_b=20.20, rev_g=0.09, h6=3400, hprev=2900, ai_job=28, patents=22, ai_ment=14,
         sent=0.68, trend="Increasing", contro_e=0, contro_s=0, contro_g=0,
         commit=12, women=52, renew=58, gcapex=26, anchor=False),
    dict(company="CapitaLand Invest", country="Singapore", sector="Real Estate", ticker="9CI",
         esg_today=78.0, esg_5yr=70.0, e_today=82, e_5yr=73, s_today=74, s_5yr=68, g_today=78, g_5yr=69,
         rev_b=2.10, rev_g=0.06, h6=1600, hprev=1350, ai_job=18, patents=6, ai_ment=6,
         sent=0.64, trend="Increasing", contro_e=0, contro_s=0, contro_g=0,
         commit=14, women=47, renew=64, gcapex=38, anchor=False),
    dict(company="CIMB Group", country="Malaysia", sector="Financial Services", ticker="1023.KL",
         esg_today=67.8, esg_5yr=58.0, e_today=64, e_5yr=52, s_today=68, s_5yr=60, g_today=71.4, g_5yr=62,
         rev_b=5.21, rev_g=0.07, h6=1300, hprev=1250, ai_job=20, patents=7, ai_ment=8,
         sent=0.56, trend="Increasing", contro_e=0, contro_s=0, contro_g=0,
         commit=10, women=54, renew=41, gcapex=19, anchor=True),
    dict(company="Bank Central Asia", country="Indonesia", sector="Financial Services", ticker="BBCA",
         esg_today=71.0, esg_5yr=62.0, e_today=66, e_5yr=56, s_today=71, s_5yr=62, g_today=76, g_5yr=68,
         rev_b=6.80, rev_g=0.11, h6=2600, hprev=2200, ai_job=19, patents=5, ai_ment=7,
         sent=0.62, trend="Increasing", contro_e=0, contro_s=0, contro_g=0,
         commit=8, women=49, renew=33, gcapex=15, anchor=False),
    dict(company="Kasikornbank", country="Thailand", sector="Financial Services", ticker="KBANK.BK",
         esg_today=70.0, esg_5yr=63.0, e_today=68, e_5yr=60, s_today=70, s_5yr=63, g_today=72, g_5yr=66,
         rev_b=7.20, rev_g=0.05, h6=2100, hprev=1950, ai_job=21, patents=6, ai_ment=9,
         sent=0.60, trend="Increasing", contro_e=0, contro_s=0, contro_g=0,
         commit=11, women=56, renew=44, gcapex=17, anchor=False),
    dict(company="Maybank", country="Malaysia", sector="Financial Services", ticker="1155.KL",
         esg_today=72.0, esg_5yr=65.0, e_today=69, e_5yr=61, s_today=72, s_5yr=65, g_today=75, g_5yr=69,
         rev_b=6.50, rev_g=0.06, h6=1900, hprev=1700, ai_job=17, patents=4, ai_ment=6,
         sent=0.58, trend="Increasing", contro_e=0, contro_s=0, contro_g=0,
         commit=9, women=53, renew=39, gcapex=16, anchor=False),
    dict(company="Siam Cement (SCG)", country="Thailand", sector="Basic Materials", ticker="SCC.BK",
         esg_today=66.0, esg_5yr=60.0, e_today=58, e_5yr=50, s_today=68, s_5yr=63, g_today=72, g_5yr=67,
         rev_b=15.50, rev_g=0.03, h6=2600, hprev=2400, ai_job=11, patents=9, ai_ment=5,
         sent=0.58, trend="Increasing", contro_e=1, contro_s=0, contro_g=0,
         commit=13, women=28, renew=37, gcapex=31, anchor=False),
    dict(company="Astra International", country="Indonesia", sector="Consumer Cyclical", ticker="ASII",
         esg_today=63.0, esg_5yr=57.0, e_today=55, e_5yr=48, s_today=64, s_5yr=58, g_today=70, g_5yr=65,
         rev_b=20.00, rev_g=0.04, h6=5000, hprev=4400, ai_job=15, patents=6, ai_ment=5,
         sent=0.60, trend="Increasing", contro_e=1, contro_s=0, contro_g=0,
         commit=7, women=31, renew=24, gcapex=18, anchor=False),

    # ---- overrated leaders: high score, momentum fading -----------------------
    dict(company="Singtel", country="Singapore", sector="Communication Services", ticker="Z74",
         esg_today=73.0, esg_5yr=74.0, e_today=76, e_5yr=76, s_today=70, s_5yr=72, g_today=73, g_5yr=74,
         rev_b=11.50, rev_g=-0.01, h6=1800, hprev=1900, ai_job=14, patents=8, ai_ment=6,
         sent=0.52, trend="Stable", contro_e=0, contro_s=0, contro_g=1,
         commit=11, women=42, renew=48, gcapex=14, anchor=False),
    dict(company="Tenaga Nasional", country="Malaysia", sector="Utilities", ticker="5347.KL",
         esg_today=68.0, esg_5yr=69.0, e_today=52, e_5yr=54, s_today=72, s_5yr=72, g_today=80, g_5yr=81,
         rev_b=12.00, rev_g=0.02, h6=2200, hprev=2400, ai_job=7, patents=3, ai_ment=3,
         sent=0.48, trend="Decreasing", contro_e=2, contro_s=0, contro_g=0,
         commit=10, women=26, renew=21, gcapex=29, anchor=False),
    dict(company="Airports of Thailand", country="Thailand", sector="Industrials", ticker="AOT.BK",
         esg_today=64.0, esg_5yr=66.0, e_today=60, e_5yr=63, s_today=65, s_5yr=66, g_today=67, g_5yr=69,
         rev_b=3.20, rev_g=0.08, h6=1200, hprev=1300, ai_job=8, patents=2, ai_ment=3,
         sent=0.47, trend="Decreasing", contro_e=0, contro_s=1, contro_g=0,
         commit=5, women=38, renew=18, gcapex=12, anchor=False),
    dict(company="Telkom Indonesia", country="Indonesia", sector="Communication Services", ticker="TLK",
         esg_today=58.4, esg_5yr=60.0, e_today=62, e_5yr=62, s_today=56, s_5yr=58, g_today=57.2, g_5yr=60,
         rev_b=2.18, rev_g=-0.02, h6=260, hprev=290, ai_job=12, patents=4, ai_ment=5,
         sent=0.50, trend="Decreasing", contro_e=0, contro_s=2, contro_g=3,
         commit=6, women=35, renew=27, gcapex=10, anchor=True),

    # ---- value traps: low score, declining ------------------------------------
    dict(company="PTTEP", country="Thailand", sector="Energy", ticker="PTTEP.BK",
         esg_today=55.0, esg_5yr=63.0, e_today=40, e_5yr=50, s_today=60, s_5yr=66, g_today=65, g_5yr=73,
         rev_b=8.87, rev_g=-0.06, h6=700, hprev=830, ai_job=8, patents=2, ai_ment=4,
         sent=0.44, trend="Decreasing", contro_e=2, contro_s=0, contro_g=1,
         commit=12, women=22, renew=9, gcapex=7, anchor=True),
    dict(company="Genting Singapore", country="Singapore", sector="Consumer Cyclical", ticker="G13",
         esg_today=48.0, esg_5yr=52.0, e_today=50, e_5yr=53, s_today=45, s_5yr=49, g_today=49, g_5yr=54,
         rev_b=1.60, rev_g=-0.03, h6=900, hprev=1100, ai_job=6, patents=1, ai_ment=2,
         sent=0.42, trend="Decreasing", contro_e=0, contro_s=1, contro_g=1,
         commit=4, women=45, renew=16, gcapex=6, anchor=False),
    dict(company="Top Glove", country="Malaysia", sector="Healthcare", ticker="7113.KL",
         esg_today=45.0, esg_5yr=50.0, e_today=48, e_5yr=52, s_today=36, s_5yr=44, g_today=51, g_5yr=54,
         rev_b=1.00, rev_g=-0.18, h6=800, hprev=1400, ai_job=5, patents=3, ai_ment=1,
         sent=0.38, trend="Decreasing", contro_e=0, contro_s=3, contro_g=1,
         commit=8, women=34, renew=14, gcapex=5, anchor=False),
    dict(company="Golden Agri-Res.", country="Singapore", sector="Consumer Defensive", ticker="E5H",
         esg_today=42.0, esg_5yr=45.0, e_today=32, e_5yr=36, s_today=44, s_5yr=47, g_today=50, g_5yr=52,
         rev_b=9.50, rev_g=-0.04, h6=1500, hprev=1700, ai_job=4, patents=1, ai_ment=1,
         sent=0.40, trend="Decreasing", contro_e=2, contro_s=1, contro_g=0,
         commit=11, women=29, renew=23, gcapex=8, anchor=False),
    dict(company="First Resources", country="Singapore", sector="Consumer Defensive", ticker="EB5",
         esg_today=47.0, esg_5yr=51.0, e_today=38, e_5yr=43, s_today=50, s_5yr=53, g_today=53, g_5yr=57,
         rev_b=1.10, rev_g=-0.02, h6=650, hprev=780, ai_job=4, patents=0, ai_ment=1,
         sent=0.43, trend="Decreasing", contro_e=1, contro_s=1, contro_g=0,
         commit=7, women=27, renew=20, gcapex=6, anchor=False),
    dict(company="Bumi Resources", country="Indonesia", sector="Energy", ticker="BUMI",
         esg_today=39.0, esg_5yr=46.0, e_today=28, e_5yr=35, s_today=40, s_5yr=47, g_today=49, g_5yr=56,
         rev_b=6.40, rev_g=-0.09, h6=900, hprev=1150, ai_job=3, patents=0, ai_ment=0,
         sent=0.36, trend="Decreasing", contro_e=2, contro_s=0, contro_g=2,
         commit=5, women=19, renew=6, gcapex=3, anchor=False),
]

# intensity
# sector baseline tCO2e per $M revenue, used to synthesise emissions_intensity when
# Climate TRACE cannot map the company to an owning entity.
SECTOR_CARBON_BASE = {
    "Energy": 1400.0, "Utilities": 1900.0, "Basic Materials": 1100.0,
    "Industrials": 320.0, "Consumer Defensive": 480.0, "Consumer Cyclical": 190.0,
    "Real Estate": 120.0, "Healthcare": 110.0, "Communication Services": 70.0,
    "Technology": 40.0, "Financial Services": 25.0,
}

# growth
GROWTH_STAGE_THRESHOLD = 0.15


# classify
def classify_stage(sector: str, rev_growth: float | None) -> str:
    if rev_growth is None:
        return MATURE
    if rev_growth >= GROWTH_STAGE_THRESHOLD:
        return HIGH_GROWTH
    if sector == "Technology" and rev_growth >= 0.08:
        return HIGH_GROWTH
    return MATURE


# lookup
def by_ticker(ticker: str) -> dict | None:
    for c in UNIVERSE:
        if c["ticker"] == ticker:
            return c
    return None
