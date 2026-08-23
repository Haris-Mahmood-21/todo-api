"""
AI-Generated Rematch Scraper (Quarantined in ai-version/)
Built to compare AI-generated monolithic pipeline against hand-built modular architecture.
"""
import os
import re
import time
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from typing import Optional, List, Dict, Any

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/Haris-Mahmood-21/todo-api)"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class AIPydanticBook(BaseModel):
    title: str = Field(..., min_length=1)
    product_url: str
    price_text: str
    price_gbp: float = Field(..., ge=0.0)
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_https(cls, v: str) -> str:
        if not v.startswith("http"):
            raise ValueError("Must be a valid HTTP URL")
        return v

class AIScraper:
    def __init__(self):
        self.last_fetch_time = 0.0
        self.pages_fetched = 0
        self.cache_hits = 0

    def fetch(self, url: str, cache_name: str) -> str:
        cache_file = CACHE_DIR / cache_name
        if cache_file.exists():
            self.cache_hits += 1
            return cache_file.read_text(encoding="utf-8")

        elapsed = time.time() - self.last_fetch_time
        if elapsed < 0.5 and self.last_fetch_time > 0:
            time.sleep(0.5 - elapsed)

        headers = {"User-Agent": USER_AGENT}
        for attempt in range(2):
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                resp.encoding = "utf-8"
                self.last_fetch_time = time.time()
                if resp.status_code == 200:
                    self.pages_fetched += 1
                    cache_file.write_text(resp.text, encoding="utf-8")
                    return resp.text
                elif resp.status_code in (403, 404):
                    raise ValueError(f"HTTP {resp.status_code}: permanent error, no retry")
                elif 500 <= resp.status_code < 600:
                    if attempt == 0:
                        time.sleep(1.0)
                        continue
                    raise ValueError(f"HTTP {resp.status_code} server error")
            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                raise ValueError(f"Network error: {e}")
        raise ValueError(f"Fetch failed for {url}")

    def run(self):
        start_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        t0 = time.perf_counter()
        
        current_url = "https://books.toscrape.com/catalogue/page-1.html"
        discovered_books = []
        
        for p in range(1, 4):
            if not current_url:
                break
            html = self.fetch(current_url, f"catalogue-page-{p}.html")
            soup = BeautifulSoup(html, "html.parser")
            for pod in soup.select(".product_pod h3 a"):
                discovered_books.append({
                    "url": urljoin(current_url, pod.get("href")),
                    "source": current_url
                })
            next_a = soup.select_one("li.next a")
            current_url = urljoin(current_url, next_a.get("href")) if next_a else None

        valid_records = []
        errors = []
        failed_pages = 0
        seen = set()

        for item in discovered_books:
            url = item["url"]
            if url in seen:
                continue
            seen.add(url)
            
            slug = url.split("/")[-2]
            try:
                html = self.fetch(url, f"book-{slug}.html")
                soup = BeautifulSoup(html, "html.parser")
                main_div = soup.select_one(".product_main")
                title = main_div.select_one("h1").get_text(strip=True)
                p_text = main_div.select_one("p.price_color").get_text(strip=True)
                match = re.search(r"(\d+\.\d+)", p_text)
                price_gbp = float(match.group(1)) if match else 0.0
                avail = " ".join(main_div.select_one("p.availability").get_text().split())
                rating_cls = main_div.select_one("p.star-rating").get("class", [])
                rating = [c for c in rating_cls if c != "star-rating"][0]
                
                desc_el = soup.select_one("#product_description ~ p")
                description = desc_el.get_text(strip=True) if desc_el else None

                rec = AIPydanticBook(
                    title=title,
                    product_url=url,
                    price_text=p_text,
                    price_gbp=price_gbp,
                    availability_text=avail,
                    rating_text=rating,
                    description=description,
                    source_page=item["source"],
                    fetched_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                )
                valid_records.append(rec.model_dump())
            except Exception as e:
                failed_pages += 1
                errors.append({"url": url, "error": str(e)})

        duration = time.perf_counter() - t0
        report = {
            "start_time": start_time,
            "duration_seconds": round(duration, 2),
            "pages_fetched": self.pages_fetched,
            "cache_hits": self.cache_hits,
            "valid_records": len(valid_records),
            "invalid_records": len(errors),
            "failed_pages": failed_pages
        }
        print("AI Scraper Finished. Report:", json.dumps(report, indent=2))
        return report

if __name__ == "__main__":
    scraper = AIScraper()
    scraper.run()
