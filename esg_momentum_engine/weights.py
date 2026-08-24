from __future__ import annotations

# stages
HIGH_GROWTH = "High-Growth/Scaling"
MATURE = "Mature/Established"

# grouping
# 11 raw sectors collapse to 6 groups. At n=24 a per-sector table would have cells
# holding one company, which is the statistical honesty problem the handoff flags.
SECTOR_GROUP = {
    "Energy": "Carbon-Intensive",
    "Utilities": "Carbon-Intensive",
    "Basic Materials": "Carbon-Intensive",
    "Industrials": "Industrial",
    "Real Estate": "Industrial",
    "Consumer Cyclical": "Consumer",
    "Consumer Defensive": "Consumer",
    "Financial Services": "Financial",
    "Technology": "Digital",
    "Communication Services": "Digital",
    "Healthcare": "Health",
}
DEFAULT_GROUP = "Industrial"

# table
# pillar weights sum to 1.0 in every cell
PILLAR_WEIGHTS: dict[tuple[str, str], dict] = {
    ("Carbon-Intensive", MATURE): dict(
        E=0.50, S=0.18, G=0.24, I=0.08,
        why="The energy transition IS the investment case here, so the emissions "
            "trend outweighs everything else; AI adoption is a rounding error on a refinery."),
    ("Carbon-Intensive", HIGH_GROWTH): dict(
        E=0.45, S=0.20, G=0.25, I=0.10,
        why="Same E dominance, but a scaling asset-heavy firm is still choosing its "
            "capex mix, so governance of that choice carries slightly more."),

    ("Financial", MATURE): dict(
        E=0.15, S=0.25, G=0.45, I=0.15,
        why="A bank's own footprint is negligible; what actually breaks a bank is "
            "governance, so G leads and E enters only through financed exposure."),
    ("Financial", HIGH_GROWTH): dict(
        E=0.12, S=0.26, G=0.40, I=0.22,
        why="A scaling lender lives or dies on digital distribution, so innovation "
            "is load-bearing rather than decorative, funded partly out of the G weight."),

    ("Digital", HIGH_GROWTH): dict(
        E=0.10, S=0.38, G=0.27, I=0.25,
        why="No material footprint. The real risks are labour practice, data handling "
            "and founder control, and at this stage innovation genuinely is the moat."),
    ("Digital", MATURE): dict(
        E=0.14, S=0.34, G=0.34, I=0.18,
        why="A mature platform is judged on how it treats workers and users and on "
            "board discipline; being early to AI matters less once growth has settled."),

    ("Consumer", MATURE): dict(
        E=0.30, S=0.34, G=0.26, I=0.10,
        why="The supply chain sits in both E and S — land use, sourcing, labour — "
            "and that is where consumer-facing scandals actually originate."),
    ("Consumer", HIGH_GROWTH): dict(
        E=0.27, S=0.36, G=0.25, I=0.12,
        why="Same supply-chain exposure, with hiring and workforce practice weighted "
            "up because rapid expansion is where labour standards slip first."),

    ("Industrial", MATURE): dict(
        E=0.34, S=0.30, G=0.26, I=0.10,
        why="Physical operations carry a real footprint and real worker-safety "
            "exposure, so E and S are close to balanced."),
    ("Industrial", HIGH_GROWTH): dict(
        E=0.30, S=0.30, G=0.25, I=0.15,
        why="Balanced E and S as above, with more room for innovation because a "
            "scaling operator is still choosing its process technology."),

    ("Health", MATURE): dict(
        E=0.12, S=0.46, G=0.30, I=0.12,
        why="Product safety, labour conditions and access dominate; the footprint of "
            "a glove or device maker is small next to what a recall costs."),
    ("Health", HIGH_GROWTH): dict(
        E=0.10, S=0.44, G=0.28, I=0.18,
        why="Same S dominance, with innovation up because a scaling health firm is "
            "still proving its product pipeline."),
}

# signals
# within-pillar signal weights. `risk` means high raw value is BAD and gets inverted
# before it enters the pillar score.
PILLAR_SIGNALS: dict[str, list[tuple[str, float, bool]]] = {
    "E": [
        ("esg_e_cagr", 1.2, False),
        ("emissions_intensity_trend", 1.3, True),
        ("renewable_pct_trend", 0.9, False),
        ("green_capex_pct_trend", 0.8, False),
        ("env_fines_12mo", 1.1, True),
    ],
    "S": [
        ("esg_s_cagr", 1.2, False),
        ("hires_growth", 1.0, False),
        ("employee_sentiment_trend", 0.8, False),
        ("diversity_women_pct_trend", 0.7, False),
        ("labour_controversy_12mo", 1.2, True),
    ],
    "G": [
        ("esg_g_cagr", 1.2, False),
        ("board_independence_pct_trend", 0.9, False),
        ("exec_turnover_12mo", 1.0, True),
        ("insider_sell_ratio", 0.8, True),
        ("litigation_actions_12mo", 1.2, True),
    ],
    "I": [
        ("ai_job_pct", 1.0, False),
        ("ai_patent_count", 1.1, False),
        ("ai_earnings_mentions", 0.7, False),
    ],
}

# crosscutting
# applied after the pillars blend, because neither belongs to a single pillar
CROSS_SIGNALS: list[tuple[str, float, bool]] = [
    ("sentiment_trend", 0.10, False),
    ("say_do_gap", 0.14, True),
]

PILLAR_LABELS = {"E": "Environmental", "S": "Social",
                 "G": "Governance", "I": "Innovation / Digital"}


# resolve
def group_for(sector: str) -> str:
    return SECTOR_GROUP.get(sector, DEFAULT_GROUP)


# lookup
def weights_for(sector: str, stage: str) -> dict:
    g = group_for(sector)
    cell = PILLAR_WEIGHTS.get((g, stage)) or PILLAR_WEIGHTS.get((g, MATURE))
    if cell is None:
        return dict(E=0.25, S=0.25, G=0.25, I=0.25,
                    why="No table entry; falling back to equal pillar weights.")
    return dict(cell)


# explain
def rationale(sector: str, stage: str) -> str:
    return weights_for(sector, stage)["why"]


# audit
def as_table() -> list[dict]:
    rows = []
    for (grp, stage), w in PILLAR_WEIGHTS.items():
        rows.append({"sector_group": grp, "stage": stage,
                     "E": w["E"], "S": w["S"], "G": w["G"], "I": w["I"],
                     "rationale": w["why"]})
    rows.sort(key=lambda r: (r["sector_group"], r["stage"]))
    return rows


if __name__ == "__main__":
    for r in as_table():
        print(f"{r['sector_group']:<18}{r['stage']:<21}"
              f"E{r['E']:.2f} S{r['S']:.2f} G{r['G']:.2f} I{r['I']:.2f}")
        print(f"    {r['rationale']}")
        assert abs(r["E"] + r["S"] + r["G"] + r["I"] - 1.0) < 1e-9
    print("\nall cells sum to 1.0")
