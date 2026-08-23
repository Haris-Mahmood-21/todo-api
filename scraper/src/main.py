"""
The Polite Scraper — Main Pipeline Entry Point
FlyRank Internship — Backend Track — Week 5 — Assignment A9
"""
import argparse
import json
import re
import sys
from scraper.src.fetcher import fetch_url
from scraper.src.crawler import crawl_catalogue
from scraper.src.extractor import extract_raw_book

CATALOGUE_PAGE_1 = "https://books.toscrape.com/catalogue/page-1.html"


def url_to_cache_name(book_url: str) -> str:
    """Generate a safe cache filename from a book URL slug."""
    match = re.search(r"/catalogue/([^/]+)/index\.html", book_url)
    if match:
        return f"book-{match.group(1)}.html"
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", book_url)
    return f"book-{safe[:50]}.html"


def run_stage_1():
    print("=== Stage 1: Fetch once, cache once ===")
    html, cached = fetch_url(CATALOGUE_PAGE_1, cache_filename="catalogue-page-1.html")
    status_str = "CACHE HIT" if cached else "FETCH"
    print(f"Status: {status_str} | Size: {len(html.encode('utf-8')):,} bytes")
    print("Stage 1 complete: Page downloaded and cached without dumping HTML.")


def run_stage_2():
    print("=== Stage 2: Find all three pages ===")
    catalogue_pages, unique_books, total_discovered = crawl_catalogue(CATALOGUE_PAGE_1, max_pages=3)
    print(
        f"catalogue_pages={len(catalogue_pages)}, "
        f"discovered={total_discovered}, "
        f"unique_urls={len(unique_books)}"
    )
    return unique_books


def run_stage_3():
    print("=== Stage 3: Extract the raw records ===")
    _, unique_books, _ = crawl_catalogue(CATALOGUE_PAGE_1, max_pages=3)
    raw_records = []

    for item in unique_books:
        book_url = item["url"]
        source_page = item["source_page"]
        cache_name = url_to_cache_name(book_url)
        html, _ = fetch_url(book_url, cache_filename=cache_name)
        raw_record = extract_raw_book(html, product_url=book_url, source_page=source_page)
        raw_records.append(raw_record)

    print("\n--- Sample Raw Record ---")
    print(json.dumps(raw_records[0], indent=2))
    print("-------------------------\n")
    print(f"detail_pages={len(raw_records)}")
    return raw_records


def main():
    parser = argparse.ArgumentParser(description="The Polite Scraper Pipeline")
    parser.add_argument("--stage", type=int, default=3, help="Stage to run (1-6)")
    args = parser.parse_args()

    if args.stage == 1:
        run_stage_1()
    elif args.stage == 2:
        run_stage_2()
    elif args.stage == 3:
        run_stage_3()
    else:
        print(f"Stage {args.stage} is not yet implemented.")


if __name__ == "__main__":
    main()
