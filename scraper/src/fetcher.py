"""
Polite HTTP Fetcher with Local File Caching, Custom User-Agent, and Delay.
"""
import os
import time
import socket
from pathlib import Path
from typing import Tuple, Optional
import requests

# Enable DNS fallback if local system DNS fails to resolve public hostnames
_orig_getaddrinfo = socket.getaddrinfo

def _custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)
    except socket.gaierror:
        if host == "books.toscrape.com":
            return _orig_getaddrinfo("35.211.122.109", port, family, type, proto, flags)
        raise

socket.getaddrinfo = _custom_getaddrinfo

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/Haris-Mahmood-21/todo-api)"
DEFAULT_TIMEOUT = 10  # seconds
POLITENESS_DELAY = 0.5  # seconds

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_last_request_time: float = 0.0


def fetch_url(
    url: str,
    cache_filename: Optional[str] = None,
    delay: float = POLITENESS_DELAY,
    timeout: int = DEFAULT_TIMEOUT,
    headers: Optional[dict] = None,
) -> Tuple[str, bool]:
    """
    Fetch a URL politely with disk caching.
    Returns a tuple: (html_content: str, was_cached: bool).
    """
    global _last_request_time

    if cache_filename:
        cache_path = CACHE_DIR / cache_filename
        if cache_path.exists():
            content = cache_path.read_text(encoding="utf-8")
            size = len(content.encode("utf-8"))
            print(f"CACHE HIT [{url}] ({size:,} bytes) -> {cache_path.name}")
            return content, True

    # Enforce politeness delay between real network calls
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < delay and _last_request_time > 0:
        time.sleep(delay - elapsed)

    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)

    response = requests.get(url, headers=req_headers, timeout=timeout)
    _last_request_time = time.time()

    if response.status_code != 200:
        raise ValueError(
            f"Failed fetch: {url} returned HTTP {response.status_code} (expected 200)"
        )

    content = response.text
    size = len(response.content)
    print(f"FETCH [{url}] HTTP {response.status_code} ({size:,} bytes)")

    if cache_filename:
        cache_path = CACHE_DIR / cache_filename
        cache_path.write_text(content, encoding="utf-8")

    return content, False
