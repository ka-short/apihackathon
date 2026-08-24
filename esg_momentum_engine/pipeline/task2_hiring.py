from __future__ import annotations
import csv
import os
from anchors import ANCHORS, MASTER_CSV

# Sector hiring intensity: new hires per $M revenue per 6 months, by sector.
# People-heavy tech hires far more per revenue dollar than capital-heavy energy.
SECTOR_INTENSITY = {
    "Technology":             0.80,
    "Financial Services":     0.25,
    "Energy":                 0.10,
    "Communication Services": 0.15,
    "Consumer Cyclical":      0.30,
    "Basic Materials":        0.17,
}

# Company-specific overrides where the sector average is too blunt.
COMPANY_OVERRIDES = {
    "SE":       {"intensity": 1.50, "growth":  0.28},   # hyper-growth tech
    "PTTEP.BK": {"intensity": 0.08, "growth": -0.16},   # conservative energy major
    "TLK":      {"intensity": 0.12, "growth": -0.10},   # state telco, slow
    "TEL":      {"intensity": 0.13, "growth":  0.07},   # mature PH telco, turning up
    "1023.KL":  {"intensity": 0.25, "growth":  0.04},   # steady bank hiring
}

SECTOR_GROWTH = {
    "Technology":             0.22,
    "Financial Services":     0.05,
    "Energy":                -0.14,
    "Communication Services": 0.02,
    "Consumer Cyclical":      0.10,
    "Basic Materials":        0.06,
}


def load_revenue() -> dict[str, float]:
    path = os.path.join(os.path.dirname(__file__), MASTER_CSV)
    rev = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rev[r["ticker"]] = float(r["revenue_usd_b"])
    return rev


def main():
    print("Task 2 — Hiring momentum (deterministic estimate)")
    print("=" * 72)
    print(f"{'Company':<20}{'Rev $B':>8}{'Intensity':>11}{'Hires 6mo':>11}"
          f"{'Prev 6mo':>10}{'Growth':>9}")
    print("-" * 72)

    rev_map = load_revenue()
    for c in ANCHORS:
        t = c["ticker"]
        rev_b = rev_map.get(t, 3.0)
        rev_m = rev_b * 1000.0
        ov = COMPANY_OVERRIDES.get(t, {})
        intensity = ov.get("intensity", SECTOR_INTENSITY.get(c["sector"], 0.2))
        growth = ov.get("growth", SECTOR_GROWTH.get(c["sector"], 0.02))

        rounding = 10 if rev_b < 4 else 50
        hires_6mo = int(round(rev_m * intensity / rounding) * rounding)
        prev_6mo = int(round(hires_6mo / (1 + growth) / rounding) * rounding)
        actual_growth = (hires_6mo - prev_6mo) / prev_6mo if prev_6mo else 0

        print(f"{c['name']:<20}{rev_b:>8}{intensity:>11}{hires_6mo:>11,}"
              f"{prev_6mo:>10,}{actual_growth*100:>8.0f}%")

    print("\nMethodology (for the write-up):")
    print("  hires_6mo = revenue($M) × sector intensity × company adjustment")
    print("  prev_6mo  = hires_6mo ÷ (1 + growth rate)")
    print("  In production, replace both with a live job-postings vendor feed.")


if __name__ == "__main__":
    main()
