from __future__ import annotations
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from providers.http import get_json, ProviderError
from providers.climatetrace import BASE, _overlap
from universe import UNIVERSE

# targets
# only asset-heavy names are worth mapping; a bank has no emitting facilities
ASSET_HEAVY = ["PTTEP", "Tenaga Nasional", "Siam Cement (SCG)", "Bumi Resources",
               "Golden Agri-Res.", "First Resources", "Astra International",
               "Airports of Thailand", "Vingroup"]


# search
def candidates(name: str, limit: int = 8) -> list[dict]:
    for path, key in (("/search", "query"), ("/assets", "companies")):
        try:
            data = get_json(f"{BASE}{path}", {key: name, "limit": limit},
                            cache_hours=720)
        except ProviderError as e:
            print(f"    {path} failed: {e}")
            continue
        rows = data if isinstance(data, list) else (
            data.get("results") or data.get("data") or data.get("assets") or [])
        if rows:
            return rows
    return []


# report
def main() -> None:
    print("climate trace owner resolver")
    print("=" * 78)
    print("Paste the good matches into OWNER_OVERRIDE in providers/climatetrace.py\n")
    override = {}
    for name in ASSET_HEAVY:
        print(f"{name}")
        rows = candidates(name)
        if not rows:
            print("    no candidates\n")
            continue
        for r in rows[:5]:
            rid = r.get("id") or r.get("owner_id") or r.get("asset_id")
            rname = r.get("name") or r.get("owner_name") or "?"
            country = r.get("country") or r.get("iso3_country") or ""
            conf = _overlap(name.lower(), str(rname).lower())
            mark = "  <-- likely" if conf >= 0.6 else ""
            print(f"    {conf:.2f}  id={rid}  {rname}  {country}{mark}")
            if conf >= 0.6 and name not in override:
                override[name] = rid
        print()

    print("=" * 78)
    print("suggested OWNER_OVERRIDE block:\n")
    print("OWNER_OVERRIDE = {")
    for k, v in override.items():
        print(f'    "{k}": "{v}",')
    print("}")
    if not override:
        print("  (empty - no confident matches; map by hand at climatetrace.org/explore)")


if __name__ == "__main__":
    main()
