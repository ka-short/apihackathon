from __future__ import annotations
from .http import get_json, ProviderError

BASE = "https://api.climatetrace.org/v7"
MIN_CONFIDENCE = 0.6

# handmapped
OWNER_OVERRIDE: dict[str, str] = {
    # "PTTEP": "<climate-trace-owner-id>",
    # "Tenaga Nasional": "<climate-trace-owner-id>",
    # "Siam Cement (SCG)": "<climate-trace-owner-id>",
}

# scope
SECTORS = ["power", "oil-and-gas-production", "mineral-extraction",
           "manufacturing", "transportation", "waste", "fossil-fuel-operations"]


# resolve
def find_owner(name: str) -> dict | None:
    if name in OWNER_OVERRIDE:
        return {"id": OWNER_OVERRIDE[name], "name": name, "confidence": 1.0}
    try:
        data = get_json(f"{BASE}/search", {"query": name, "limit": 5}, cache_hours=720)
    except ProviderError:
        return None
    hits = data if isinstance(data, list) else (data.get("results") or data.get("data") or [])
    for h in hits:
        hname = (h.get("name") or h.get("owner_name") or "").lower()
        if not hname:
            continue
        conf = _overlap(name.lower(), hname)
        if conf >= MIN_CONFIDENCE:
            return {"id": h.get("id") or h.get("owner_id"), "name": hname,
                    "confidence": round(conf, 2)}
    return None


# similarity
def _overlap(a: str, b: str) -> float:
    ta = {w for w in a.replace(".", " ").split() if len(w) > 2}
    tb = {w for w in b.replace(".", " ").split() if len(w) > 2}
    if not ta:
        return 0.0
    return len(ta & tb) / len(ta)


# emissions
def owner_emissions(owner_id: str, years: list[int]) -> dict[int, float]:
    out: dict[int, float] = {}
    try:
        data = get_json(f"{BASE}/assets", {
            "companies": owner_id, "years": ",".join(str(y) for y in years),
            "gas": "co2e_100yr", "limit": 500,
        }, cache_hours=720)
    except ProviderError:
        return out
    rows = data.get("assets") if isinstance(data, dict) else data
    for a in (rows or []):
        for e in (a.get("Emissions") or a.get("emissions") or []):
            for y, v in (e.items() if isinstance(e, dict) else []):
                try:
                    yi = int(str(y)[:4])
                    out[yi] = out.get(yi, 0.0) + float(v)
                except (TypeError, ValueError):
                    continue
    return out


# intensity
def fetch(company: str, revenue_usd_b: float, years=(2021, 2022, 2023, 2024)) -> dict:
    out = {"company": company, "ok": False, "source": "climate-trace-v7"}
    owner = find_owner(company)
    if not owner or not owner.get("id"):
        return out
    series = owner_emissions(owner["id"], list(years))
    if len(series) < 2 or revenue_usd_b <= 0:
        return out
    ys = sorted(series)
    first, last = series[ys[0]], series[ys[-1]]
    rev_musd = revenue_usd_b * 1000.0
    out.update({
        "ok": True,
        "match_confidence": owner["confidence"],
        "emissions_tco2e_latest": round(last, 1),
        "emissions_intensity": round(last / rev_musd, 3),
        "emissions_intensity_trend": round((last / first) ** (1 / max(1, ys[-1] - ys[0])) - 1, 4),
        "emissions_years": f"{ys[0]}-{ys[-1]}",
    })
    return out


if __name__ == "__main__":
    import sys, json
    print(json.dumps(fetch(sys.argv[1] if len(sys.argv) > 1 else "PTTEP", 8.87), indent=2))
