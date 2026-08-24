from __future__ import annotations

try:
    import yfinance as yf
except ImportError:
    yf = None


# guard
def available() -> bool:
    return yf is not None


# growth
def _cagr(new: float, old: float, years: float) -> float | None:
    if not old or old <= 0 or not new or new <= 0:
        return None
    return round((new / old) ** (1 / years) - 1, 4)


# financials
def fetch(ticker: str) -> dict:
    out = {"ticker": ticker, "ok": False, "source": "yfinance"}
    if yf is None:
        return out
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
    except Exception:
        return out

    rev = info.get("totalRevenue")
    out["revenue_usd_b"] = round(rev / 1e9, 3) if rev else None
    out["rev_growth_yoy"] = info.get("revenueGrowth")
    out["pe_ratio"] = info.get("trailingPE") or info.get("forwardPE")
    out["pb_ratio"] = info.get("priceToBook")
    out["market_cap_usd_b"] = round(info.get("marketCap", 0) / 1e9, 3) or None
    out["employees"] = info.get("fullTimeEmployees")

    try:
        fin = t.financials
        if fin is not None and "Total Revenue" in fin.index and fin.shape[1] >= 2:
            row = fin.loc["Total Revenue"].dropna()
            if len(row) >= 2:
                out["rev_cagr"] = _cagr(float(row.iloc[0]), float(row.iloc[-1]),
                                        max(1, len(row) - 1))
    except Exception:
        pass

    try:
        tx = t.insider_transactions
        if tx is not None and len(tx):
            col = "Text" if "Text" in tx.columns else None
            sells = sum(1 for v in tx[col] if "sale" in str(v).lower()) if col else 0
            out["insider_sell_ratio"] = round(sells / len(tx), 3)
            out["insider_tx_count"] = int(len(tx))
    except Exception:
        pass

    try:
        out["exec_count"] = len(info.get("companyOfficers") or []) or None
    except Exception:
        pass

    out["ok"] = out.get("revenue_usd_b") is not None
    return out


if __name__ == "__main__":
    import sys, json
    print(json.dumps(fetch(sys.argv[1] if len(sys.argv) > 1 else "SE"), indent=2, default=str))
