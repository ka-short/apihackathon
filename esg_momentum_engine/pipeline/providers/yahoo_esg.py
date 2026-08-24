from __future__ import annotations
from .http import get_json, ProviderError

CHART = "https://query2.finance.yahoo.com/v1/finance/esgChart"
SUMMARY = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{}"

RISK_CAP = 60.0


# invert
def to_quality(risk: float | None) -> float | None:
    if risk is None:
        return None
    return round(max(0.0, min(100.0, 100.0 - (float(risk) / RISK_CAP) * 100.0)), 2)


# unwrap
def _num(v):
    if isinstance(v, dict):
        v = v.get("raw")
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# history
def esg_history(ticker: str) -> list[dict]:
    data = get_json(CHART, {"symbol": ticker}, cache_hours=168)
    res = (data.get("esgChart") or {}).get("result") or []
    if not res:
        raise ProviderError(f"no esgChart series for {ticker}")
    series = res[0].get("symbolSeries") or {}
    ts = series.get("timestamp") or []
    out = []
    for i, t in enumerate(ts):
        row = {"ts": t}
        for src, dst in (("esgScore", "total"), ("environmentScore", "e"),
                         ("socialScore", "s"), ("governanceScore", "g")):
            col = series.get(src) or []
            row[dst] = to_quality(col[i]) if i < len(col) and col[i] is not None else None
        out.append(row)
    return out


# trend
def pillar_cagr(history: list[dict], pillar: str, years: float = 5.0) -> float | None:
    pts = [r for r in history if r.get(pillar) is not None]
    if len(pts) < 4:
        return None
    first, last = pts[0][pillar], pts[-1][pillar]
    span = max(1.0, (pts[-1]["ts"] - pts[0]["ts"]) / (365.25 * 86400))
    span = min(span, years)
    if first <= 0:
        return None
    return round((last / first) ** (1 / span) - 1, 4)


# snapshot
def esg_snapshot(ticker: str) -> dict:
    data = get_json(SUMMARY.format(ticker), {"modules": "esgScores"}, cache_hours=168)
    res = ((data.get("quoteSummary") or {}).get("result") or [])
    if not res or not res[0].get("esgScores"):
        raise ProviderError(f"no esgScores for {ticker}")
    e = res[0]["esgScores"]
    return {
        "total": to_quality(_num(e.get("totalEsg"))),
        "e": to_quality(_num(e.get("environmentScore"))),
        "s": to_quality(_num(e.get("socialScore"))),
        "g": to_quality(_num(e.get("governanceScore"))),
        "highest_controversy": _num(e.get("highestControversy")),
        "peer_group": e.get("peerGroup"),
        "percentile": _num(e.get("percentile")),
    }


# combine
def fetch(ticker: str) -> dict:
    out = {"ticker": ticker, "ok": False, "source": "yahoo-sustainalytics"}
    try:
        hist = esg_history(ticker)
        out["history_points"] = len(hist)
        for p in ("total", "e", "s", "g"):
            latest = [r[p] for r in hist if r.get(p) is not None]
            out[f"{p}_today"] = latest[-1] if latest else None
            out[f"{p}_cagr"] = pillar_cagr(hist, p)
        out["ok"] = out.get("total_today") is not None
    except ProviderError:
        pass
    try:
        snap = esg_snapshot(ticker)
        for p in ("total", "e", "s", "g"):
            if out.get(f"{p}_today") is None:
                out[f"{p}_today"] = snap.get(p)
        out["peer_group"] = snap.get("peer_group")
        out["highest_controversy"] = snap.get("highest_controversy")
        out["ok"] = out.get("total_today") is not None
    except ProviderError:
        pass
    return out


if __name__ == "__main__":
    import sys, json
    print(json.dumps(fetch(sys.argv[1] if len(sys.argv) > 1 else "SE"), indent=2))
