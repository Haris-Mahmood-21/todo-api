"""
The Polite Scraper — Main Pipeline Entry Point
FlyRank Internship — Backend Track — Week 5 — Assignment A9
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from scraper.src.fetcher import fetch_url, reset_metrics, get_metrics
from scraper.src.crawler import crawl_catalogue
from scraper.src.extractor import extract_raw_book
from scraper.src.models import validate_and_store_records, export_records_to_csv, OUTPUT_DIR
from scraper.src.reporter import generate_run_report

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


def run_stage_5(test_failure: bool = False):
    print("=== Stage 5: One bad page must not kill the run ===")
    start_time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    start_perf = time.perf_counter()
    reset_metrics()

    # 1. Crawl catalogue pages (1, 2, 3)
    _, unique_books, _ = crawl_catalogue(CATALOGUE_PAGE_1, max_pages=3)

    # 2. Inject deliberate failure if requested
    if test_failure:
        fake_url = "https://books.toscrape.com/catalogue/non-existent-broken-book_9999/index.html"
        print(f"\n[TEST INJECTION] Adding deliberate broken URL: {fake_url}\n")
        unique_books.append({"url": fake_url, "source_page": CATALOGUE_PAGE_1})

    raw_records = []
    failed_pages = 0

    # 3. Process each book detail page in isolation
    for item in unique_books:
        book_url = item["url"]
        source_page = item["source_page"]
        cache_name = url_to_cache_name(book_url)

        try:
            html, _ = fetch_url(book_url, cache_filename=cache_name)
            raw_record = extract_raw_book(html, product_url=book_url, source_page=source_page)
            raw_records.append(raw_record)
        except Exception as exc:
            failed_pages += 1
            print(f"[SKIPPED FAILED PAGE] {book_url} -> Reason: {exc}")

    # 4. Normalize & Validate records
    valid_records, invalid_records = validate_and_store_records(raw_records)
    export_records_to_csv(valid_records)

    # 5. Generate Run Report
    duration = time.perf_counter() - start_perf
    metrics = get_metrics()

    report = generate_run_report(
        start_time=start_time_iso,
        duration_seconds=duration,
        pages_fetched=metrics["pages_fetched"],
        cache_hits=metrics["cache_hits"],
        valid_records=len(valid_records),
        invalid_records=len(invalid_records),
        failed_pages=failed_pages,
    )

    print("\n--- Run Report ---")
    print(json.dumps(report, indent=2))
    print("------------------\n")
    print(f"Stage 5 Checkpoint: books.json has {len(valid_records)} valid records; failed_pages={failed_pages}")


def main():
    parser = argparse.ArgumentParser(description="The Polite Scraper Pipeline")
    parser.add_argument("--stage", type=int, default=5, help="Stage to run (1-6)")
    parser.add_argument("--test-failure", action="store_true", help="Inject fake URL to verify failure survival")
    args = parser.parse_args()

    if args.stage == 1:
        run_stage_1()
    elif args.stage == 2:
        run_stage_2()
    elif args.stage == 3:
        run_stage_3()
    elif args.stage == 4:
        run_stage_4()
    elif args.stage in (5, 6):
        run_stage_5(test_failure=args.test_failure)
    else:
        print(f"Stage {args.stage} is not valid.")


if __name__ == "__main__":
    main()
