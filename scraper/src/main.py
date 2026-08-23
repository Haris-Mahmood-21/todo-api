"""
The Polite Scraper — Main Pipeline Entry Point
FlyRank Internship — Backend Track — Week 5 — Assignment A9
"""
import argparse
import json
import re
import sys
from pathlib import Path
from scraper.src.fetcher import fetch_url
from scraper.src.crawler import crawl_catalogue
from scraper.src.extractor import extract_raw_book
from scraper.src.models import validate_and_store_records, OUTPUT_DIR

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


def run_stage_4():
    print("=== Stage 4: Clean it, check it, store it ===")
    raw_records = run_stage_3()
    valid_records, invalid_records = validate_and_store_records(raw_records)

    books_path = OUTPUT_DIR / "books.json"
    with open(books_path, "r", encoding="utf-8") as f:
        stored = json.load(f)

    # Verification checks
    count = len(stored)
    all_prices_numeric = all(isinstance(r["price_gbp"], (int, float)) for r in stored)
    all_urls_valid = all(r["product_url"].startswith("https://") for r in stored)

    print("\n--- Stage 4 Validation Summary ---")
    print(f"books.json count: {count}")
    print(f"All price_gbp numeric: {all_prices_numeric}")
    print(f"All product_url start with https://: {all_urls_valid}")
    print(f"Invalid records: {len(invalid_records)}")
    print(f"Saved to: {books_path}")
    print("----------------------------------\n")


def main():
    parser = argparse.ArgumentParser(description="The Polite Scraper Pipeline")
    parser.add_argument("--stage", type=int, default=4, help="Stage to run (1-6)")
    args = parser.parse_args()

    if args.stage == 1:
        run_stage_1()
    elif args.stage == 2:
        run_stage_2()
    elif args.stage == 3:
        run_stage_3()
    elif args.stage == 4:
        run_stage_4()
    else:
        print(f"Stage {args.stage} is not yet implemented.")


if __name__ == "__main__":
    main()
