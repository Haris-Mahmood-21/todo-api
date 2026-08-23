"""
HTML Extractor — Extracts 8 raw fields from a book detail page.
"""
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup


def extract_raw_book(
    html: str,
    product_url: str,
    source_page: str,
    fetched_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract 8 raw receipt fields from a book detail HTML page.
    """
    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    soup = BeautifulSoup(html, "html.parser")
    product_main = soup.select_one(".product_main")

    if not product_main:
        raise ValueError(f"Could not locate .product_main container on {product_url}")

    # 1. Title
    title_el = product_main.select_one("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    # 2. Product URL (passed in as canonical absolute URL)
    canonical_product_url = product_url

    # 3. Price text (e.g. '£51.77')
    price_el = product_main.select_one("p.price_color")
    price_text = price_el.get_text(strip=True) if price_el else ""

    # 4. Availability text (e.g. 'In stock (22 available)')
    avail_el = product_main.select_one("p.availability")
    # Clean internal excess whitespace while preserving full text
    availability_text = (
        " ".join(avail_el.get_text().split()) if avail_el else ""
    )

    # 5. Rating text (e.g. 'Three')
    rating_el = product_main.select_one("p.star-rating")
    rating_text = ""
    if rating_el:
        classes = rating_el.get("class", [])
        for c in classes:
            if c != "star-rating":
                rating_text = c
                break

    # 6. Description (Store None/null if not present)
    description = None
    desc_header = soup.select_one("#product_description")
    if desc_header:
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            text = desc_p.get_text(strip=True)
            if text:
                description = text

    # 7. Source page (provenance)
    # 8. Fetched at timestamp (provenance)

    return {
        "title": title,
        "product_url": canonical_product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }
