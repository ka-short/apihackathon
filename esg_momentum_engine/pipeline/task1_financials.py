from __future__ import annotations
import sys
import time
import csv
import os
from anchors import ANCHORS, FX_FALLBACK, MASTER_CSV

try:
    import yfinance as yf
except ImportError:
    yf = None


def fetch_fx(fx_ticker: str, currency: str, retries: int = 2) -> tuple[float, str]:
    """Return (rate, source). Falls back to a documented static rate on failure."""
    if fx_ticker is None:
        return 1.0, "USD (no conversion)"
    if yf is None:
        return FX_FALLBACK.get(currency, 1.0), "fallback (yfinance not installed)"
    for attempt in range(retries):
        try:
            t = yf.Ticker(fx_ticker)
            rate = (t.fast_info.get("lastPrice") if hasattr(t, "fast_info") else None) \
                or t.info.get("regularMarketPrice")
            if rate:
                return float(rate), "live (yfinance)"
        except Exception:
            time.sleep(1)
    return FX_FALLBACK.get(currency, 1.0), "fallback (live fetch failed)"


def fetch_revenue_usd_b(ticker: str, fx: float) -> tuple[float | None, str]:
    """Return (revenue_usd_billions, source) or (None, reason)."""
    if yf is None:
        return None, "yfinance not installed"
    try:
        info = yf.Ticker(ticker).info
        rev_local = info.get("totalRevenue")
        sector = info.get("sector", "N/A")
        if rev_local:
            return round(rev_local * fx / 1e9, 2), f"live · sector={sector}"
        return None, "no totalRevenue in yfinance"
    except Exception as e:
        return None, f"error: {e}"


def main(write: bool):
    print("Task 1 — Financials (revenue, USD-converted)")
    print("=" * 68)
    results = {}
    for c in ANCHORS:
        fx, fx_src = fetch_fx(c["fx_ticker"], c["currency"])
        rev, rev_src = fetch_revenue_usd_b(c["ticker"], fx)
        results[c["ticker"]] = rev
        status = "OK" if rev is not None else "keep calibrated"
        print(f"  {c['name']:<20} {c['ticker']:<10} "
              f"FX {c['currency']}/USD={fx:.6f} [{fx_src}]  "
              f"Rev={'$'+str(rev)+'B' if rev else 'N/A'} [{status}] {rev_src}")

    if not write:
        print("\n(dry run — pass --write to update the master CSV)")
        return

    # Merge live revenue into master_data.csv where a live value was obtained.
    path = os.path.join(os.path.dirname(__file__), MASTER_CSV)
    if not os.path.exists(path):
        print(f"\nMaster CSV not found at {path}; run build_master_data.py first.")
        return
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fields = rows[0].keys()
    updated = 0
    for r in rows:
        live = results.get(r["ticker"])
        if live:
            r["revenue_usd_b"] = live
            r["data_source"] = "live-financials (task1)"
            updated += 1
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fields))
        w.writeheader()
        w.writerows(rows)
    print(f"\nUpdated {updated} anchor revenue values in {MASTER_CSV}")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
