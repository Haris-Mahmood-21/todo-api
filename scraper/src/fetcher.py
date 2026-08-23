"""
Polite HTTP Fetcher with Local File Caching, Smart Retries, and Metrics Tracking.
"""
import os
import time
from pathlib import Path
from typing import Tuple, Optional, Dict
import requests

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/Haris-Mahmood-21/todo-api)"
DEFAULT_TIMEOUT = 10  # seconds
POLITENESS_DELAY = 0.5  # seconds

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_last_request_time: float = 0.0

# Session metrics
_metrics: Dict[str, int] = {
    "pages_fetched": 0,
    "cache_hits": 0,
}


def reset_metrics():
    """Reset fetcher metrics counters."""
    global _metrics
    _metrics = {"pages_fetched": 0, "cache_hits": 0}


def get_metrics() -> Dict[str, int]:
    """Retrieve current fetcher metrics."""
    return dict(_metrics)


def _polite_sleep(delay: float):
    """Enforce delay between consecutive network requests."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < delay and _last_request_time > 0:
        time.sleep(delay - elapsed)


def fetch_url(
    url: str,
    cache_filename: Optional[str] = None,
    delay: float = POLITENESS_DELAY,
    timeout: int = DEFAULT_TIMEOUT,
    headers: Optional[dict] = None,
    max_retries: int = 1,
) -> Tuple[str, bool]:
    """
    Fetch a URL politely with disk caching and single retry on 5xx or timeout.
    Will NOT retry on 404 or 403.
    Returns: (html_content: str, was_cached: bool)
    """
    global _last_request_time, _metrics

    if cache_filename:
        cache_path = CACHE_DIR / cache_filename
        if cache_path.exists():
            content = cache_path.read_text(encoding="utf-8")
            size = len(content.encode("utf-8"))
            _metrics["cache_hits"] += 1
            print(f"CACHE HIT [{url}] ({size:,} bytes) -> {cache_path.name}")
            return content, True

    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)

    attempts = 0
    while attempts <= max_retries:
        attempts += 1
        _polite_sleep(delay)

        try:
            response = requests.get(url, headers=req_headers, timeout=timeout)
            response.encoding = "utf-8"
            _last_request_time = time.time()

            status = response.status_code

            # Success
            if status == 200:
                content = response.text
                size = len(response.content)
                _metrics["pages_fetched"] += 1
                print(f"FETCH [{url}] HTTP 200 ({size:,} bytes)")

                if cache_filename:
                    cache_path = CACHE_DIR / cache_filename
                    cache_path.write_text(content, encoding="utf-8")

                return content, False

            # Permanent client errors — DO NOT RETRY
            if status in (404, 403):
                raise ValueError(
                    f"HTTP {status} Client Error on {url}: Do not retry."
                )

            # Server errors (5xx) — retry once if attempts <= max_retries
            if 500 <= status <= 599:
                if attempts <= max_retries:
                    print(f"WARNING: HTTP {status} on {url}. Retrying once...")
                    time.sleep(1.0)
                    continue
                else:
                    raise ValueError(f"HTTP {status} Server Error on {url} after retry.")

            # Other non-200 status
            raise ValueError(f"Unexpected HTTP {status} on {url}")

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            _last_request_time = time.time()
            if attempts <= max_retries:
                print(f"WARNING: Network error ({exc.__class__.__name__}) on {url}. Retrying once...")
                time.sleep(1.0)
                continue
            else:
                raise ValueError(f"Network error on {url} after retry: {exc}")

    raise ValueError(f"Failed to fetch {url}")
