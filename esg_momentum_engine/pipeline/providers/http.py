"""shared http layer for every live provider — cache, retry, never crash the build"""
from __future__ import annotations
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cache")
UA = "Mozilla/5.0 (compatible; ESGMomentumEngine/2.0; hackathon research)"
TIMEOUT = 20
RETRIES = 2


class ProviderError(RuntimeError):
    pass


# flag
def offline() -> bool:
    return os.environ.get("ESG_OFFLINE", "").lower() in ("1", "true", "yes")


# key
def _cache_path(url: str) -> str:
    import hashlib
    h = hashlib.sha1(url.encode()).hexdigest()[:20]
    return os.path.join(CACHE_DIR, f"{h}.json")


# read
def _cache_get(url: str, max_age_s: int):
    p = _cache_path(url)
    if not os.path.exists(p):
        return None
    if max_age_s and (time.time() - os.path.getmtime(p)) > max_age_s:
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# write
def _cache_put(url: str, payload) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
        with open(_cache_path(url), "w", encoding="utf-8") as f:
            json.dump(payload, f)
    except Exception:
        pass


# fetch
def get_json(url: str, params: dict | None = None, headers: dict | None = None,
             cache_hours: int = 24):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)

    cached = _cache_get(url, cache_hours * 3600)
    if cached is not None:
        return cached
    if offline():
        raise ProviderError("offline mode and no cached response")

    hdrs = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)

    last = None
    for attempt in range(RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                raw = r.read().decode("utf-8", "replace")
            payload = json.loads(raw)
            _cache_put(url, payload)
            return payload
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            last = e
            if attempt < RETRIES:
                time.sleep(1.5 * (attempt + 1))
    raise ProviderError(f"{url} -> {last}")
