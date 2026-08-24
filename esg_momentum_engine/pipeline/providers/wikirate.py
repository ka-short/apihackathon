from __future__ import annotations
import os
import urllib.parse
from .http import get_json, ProviderError

BASE = "https://wikirate.org"

# metrics
METRICS = {
    "renewable_pct": "Global_Reporting_Initiative+Renewable_energy_consumption",
    "women_workforce_pct": "Global_Reporting_Initiative+Percentage_of_women_in_the_workforce",
    "women_leadership_pct": "Global_Reporting_Initiative+Percentage_of_women_in_management",
    "board_independence_pct": "Global_Reporting_Initiative+Percentage_of_independent_board_members",
}


# key
def _key() -> str:
    k = os.environ.get("WIKIRATE_API_KEY", "").strip()
    if not k:
        raise ProviderError("WIKIRATE_API_KEY not set")
    return k


# lookup
def answer(metric: str, company: str, year: int) -> float | None:
    slug = urllib.parse.quote(f"{metric}+{company.replace(' ', '_')}+{year}")
    try:
        data = get_json(f"{BASE}/{slug}.json", {"api_key": _key()}, cache_hours=720)
    except ProviderError:
        return None
    val = data.get("content") or data.get("value")
    if isinstance(val, list):
        val = val[0] if val else None
    try:
        return float(str(val).replace("%", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


# series
def metric_trend(metric: str, company: str, years: list[int]) -> dict:
    pts = {y: answer(metric, company, y) for y in years}
    pts = {y: v for y, v in pts.items() if v is not None}
    if not pts:
        return {"latest": None, "trend": None}
    ys = sorted(pts)
    latest = pts[ys[-1]]
    if len(ys) < 2:
        return {"latest": latest, "trend": None}
    span = max(1, ys[-1] - ys[0])
    return {"latest": latest, "trend": round((latest - pts[ys[0]]) / span, 3)}


# combine
def fetch(company: str, years=(2021, 2022, 2023, 2024)) -> dict:
    out = {"company": company, "ok": False, "source": "wikirate"}
    try:
        _key()
    except ProviderError:
        return out
    for field, metric in METRICS.items():
        r = metric_trend(metric, company, list(years))
        out[field] = r["latest"]
        out[f"{field}_trend"] = r["trend"]
        if r["latest"] is not None:
            out["ok"] = True
    return out


if __name__ == "__main__":
    import sys, json
    print(json.dumps(fetch(sys.argv[1] if len(sys.argv) > 1 else "Sea Limited"), indent=2))
