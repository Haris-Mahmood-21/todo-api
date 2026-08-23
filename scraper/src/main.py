"""
The Polite Scraper — Main Pipeline Entry Point
FlyRank Internship — Backend Track — Week 5 — Assignment A9
"""
import argparse
import sys
from scraper.src.fetcher import fetch_url
from scraper.src.crawler import crawl_catalogue

CATALOGUE_PAGE_1 = "https://books.toscrape.com/catalogue/page-1.html"

def run_stage_1():
    print("=== Stage 1: Fetch once, cache once ===")
    html, cached = fetch_url(CATALOGUE_PAGE_1, cache_filename="catalogue-page-1.html")
    status_str = "CACHE HIT" if cached else "FETCH"
    print(f"Status: {status_str} | Size: {len(html.encode('utf-8')):,} bytes")
    print("Stage 1 complete: Page downloaded and cached without dumping HTML.")

def run_stage_2():
    print("=== Stage 2: Find all three pages ===")
    catalogue_pages, unique_urls, total_discovered = crawl_catalogue(CATALOGUE_PAGE_1, max_pages=3)
    print(
        f"catalogue_pages={len(catalogue_pages)}, "
        f"discovered={total_discovered}, "
        f"unique_urls={len(unique_urls)}"
    )

def main():
    parser = argparse.ArgumentParser(description="The Polite Scraper Pipeline")
    parser.add_argument("--stage", type=int, default=2, help="Stage to run (1-6)")
    args = parser.parse_args()

    if args.stage == 1:
        run_stage_1()
    elif args.stage == 2:
        run_stage_2()
    else:
        print(f"Stage {args.stage} is not yet implemented.")

if __name__ == "__main__":
    main()
