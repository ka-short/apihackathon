import json, sys, time

TICKERS = ["SE", "GRAB", "D05.SI", "1023.KL"]


def line(name, ok, detail=""):
    print(f"{'OK  ' if ok else 'FAIL'} | {name:<34} | {detail}")


print("probing ESG data sources\n" + "-" * 90)

# 1 yfinance sustainability, handles the cookie/crumb handshake itself
try:
    import yfinance as yf
    for t in TICKERS:
        try:
            s = yf.Ticker(t).sustainability
            if s is None or len(s) == 0:
                line("yfinance .sustainability", False, f"{t}: empty (no coverage)")
                continue
            d = s.to_dict().get("esgScores", s.iloc[:, 0].to_dict())
            keys = [k for k in ("totalEsg", "environmentScore", "socialScore",
                                "governanceScore") if k in d]
            line("yfinance .sustainability", True,
                 f"{t}: " + ", ".join(f"{k}={d[k]}" for k in keys))
        except Exception as e:
            line("yfinance .sustainability", False, f"{t}: {type(e).__name__} {e}")
except Exception as e:
    line("yfinance .sustainability", False, f"{type(e).__name__} {e}")
time.sleep(1)

# 2 esgChart through yfinance's authenticated session
try:
    from yfinance.data import YfData
    d = YfData()
    for t in TICKERS[:2]:
        try:
            r = d.get_raw_json(f"https://query2.finance.yahoo.com/v1/finance/esgChart?symbol={t}")
            n = len((r.get("esgChart", {}).get("result") or [{}])[0]
                    .get("symbolSeries", {}).get("timestamp", []))
            line("esgChart via yfinance session", n > 0, f"{t}: {n} history points")
        except Exception as e:
            line("esgChart via yfinance session", False, f"{t}: {type(e).__name__} {e}")
except Exception as e:
    line("esgChart via yfinance session", False, f"import: {e}")
time.sleep(1)

# 3 quoteSummary esgScores through yfinance session
try:
    from yfinance.data import YfData
    d = YfData()
    for t in TICKERS[:2]:
        try:
            r = d.get_raw_json(
                f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{t}",
                params={"modules": "esgScores"})
            res = (r.get("quoteSummary", {}).get("result") or [{}])[0].get("esgScores")
            line("quoteSummary esgScores", bool(res),
                 f"{t}: " + (json.dumps(res)[:110] if res else "no esgScores block"))
        except Exception as e:
            line("quoteSummary esgScores", False, f"{t}: {type(e).__name__} {e}")
except Exception as e:
    line("quoteSummary esgScores", False, f"import: {e}")
time.sleep(1)

# 4 gdelt, one call only, to see if the 429 has cleared
try:
    import urllib.request as u
    url = ("https://api.gdeltproject.org/api/v2/doc/doc?query=%22Grab+Holdings%22"
           "&mode=tonechart&timespan=3months&format=json")
    req = u.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = u.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    bins = json.loads(raw).get("tonechart", [])
    line("gdelt tonechart", bool(bins),
         f"{len(bins)} bins, {sum(int(b.get('count',0)) for b in bins)} articles")
except Exception as e:
    line("gdelt tonechart", False, f"{type(e).__name__} {e}")

print("-" * 90)
print("python", sys.version.split()[0])
