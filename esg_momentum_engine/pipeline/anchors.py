# One dict per anchor company, with everything the task scripts need.
ANCHORS = [
    {"ticker": "TEL",      "name": "PLDT",             "currency": "PHP", "fx_ticker": "PHPUSD=X",
     "sector": "Communication Services",
     "news_query": "PLDT Philippines telecom ESG sustainability",
     "controversy_query": "PLDT Philippines controversy fine investigation"},
    {"ticker": "PTTEP.BK", "name": "PTTEP",            "currency": "THB", "fx_ticker": "THBUSD=X",
     "sector": "Energy",
     "news_query": "PTTEP Thailand energy ESG sustainability",
     "controversy_query": "PTTEP Thailand oil spill controversy investigation"},
    {"ticker": "TLK",      "name": "Telkom Indonesia", "currency": "IDR", "fx_ticker": "IDRUSD=X",
     "sector": "Communication Services",
     "news_query": "Telkom Indonesia sustainability ESG digital",
     "controversy_query": "Telkom Indonesia controversy breach investigation"},
    {"ticker": "SE",       "name": "Sea Limited",      "currency": "USD", "fx_ticker": None,
     "sector": "Technology",
     "news_query": "Sea Limited Shopee ESG sustainability AI",
     "controversy_query": "Sea Limited Shopee controversy lawsuit layoffs"},
    {"ticker": "1023.KL",  "name": "CIMB Group",       "currency": "MYR", "fx_ticker": "MYRUSD=X",
     "sector": "Financial Services",
     "news_query": "CIMB Group Malaysia ESG green finance",
     "controversy_query": "CIMB Group Malaysia controversy fine breach"},
]

# Fallback FX rates (local -> USD) used only when a live FX pull fails, so the
# scripts never crash mid-demo.
FX_FALLBACK = {"PHP": 0.0175, "MYR": 0.225, "IDR": 0.0000615, "SGD": 0.742, "THB": 0.0277, "USD": 1.0}

MASTER_CSV = "../data/master_data.csv"
