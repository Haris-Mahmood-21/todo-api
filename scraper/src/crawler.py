"""
Catalogue Crawler — Traverses pagination and discovers book URLs with provenance.
"""
from urllib.parse import urljoin
from typing import List, Tuple, Optional, Dict
from bs4 import BeautifulSoup
from scraper.src.fetcher import fetch_url


def extract_book_links_from_catalogue(html: str, page_url: str) -> List[str]:
    """
    Extract all book detail links from a catalogue page and convert to absolute URLs.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for article in soup.select("article.product_pod"):
        a_tag = article.select_one("h3 a")
        if a_tag and a_tag.get("href"):
            rel_href = a_tag.get("href")
            abs_url = urljoin(page_url, rel_href)
            links.append(abs_url)
    return links


def extract_next_page_url(html: str, current_page_url: str) -> Optional[str]:
    """
    Extract the 'next' pagination link from a catalogue page, converted to absolute URL.
    """
    soup = BeautifulSoup(html, "html.parser")
    next_li = soup.select_one("li.next a")
    if next_li and next_li.get("href"):
        return urljoin(current_page_url, next_li.get("href"))
    return None


def crawl_catalogue(
    start_url: str = "https://books.toscrape.com/catalogue/page-1.html",
    max_pages: int = 3,
) -> Tuple[List[str], List[Dict[str, str]], int]:
    """
    Crawl up to max_pages of the catalogue following 'next' links.
    Returns:
        catalogue_pages: list of visited catalogue URLs
        discovered_books: list of dicts with {"url": book_url, "source_page": catalogue_url}
        total_discovered: count of discovered links before deduplication
    """
    current_url = start_url
    catalogue_pages = []
    discovered_items = []
    page_num = 1

    while current_url and page_num <= max_pages:
        cache_name = f"catalogue-page-{page_num}.html"
        html, _ = fetch_url(current_url, cache_filename=cache_name)
        catalogue_pages.append(current_url)

        links = extract_book_links_from_catalogue(html, current_url)
        for link in links:
            discovered_items.append({"url": link, "source_page": current_url})

        if page_num < max_pages:
            next_url = extract_next_page_url(html, current_url)
            current_url = next_url
        else:
            current_url = None

        page_num += 1

    # Remove duplicates while preserving discovery order
    seen = set()
    unique_books = []
    for item in discovered_items:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique_books.append(item)

    return catalogue_pages, unique_books, len(discovered_items)
