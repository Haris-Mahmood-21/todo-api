"""
Unit Tests for The Polite Scraper Pipeline.
Tests:
1. Price normalization (raw currency string -> float)
2. Relative -> absolute URL conversion
3. Missing description handled as None/null
4. Duplicate URLs deduplication
5. Malformed fixture handling
"""
import pytest
from pathlib import Path
from bs4 import BeautifulSoup
from scraper.src.models import parse_price_gbp, BookRecord, validate_and_store_records
from scraper.src.crawler import extract_book_links_from_catalogue
from scraper.src.extractor import extract_raw_book

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_1_price_normalization():
    """Test 1: Price normalization correctly parses floats from currency strings."""
    assert parse_price_gbp("£51.77") == 51.77
    assert parse_price_gbp("£0.99") == 0.99
    assert parse_price_gbp("£100.00") == 100.0
    assert parse_price_gbp("£12.345") == 12.35

    with pytest.raises(ValueError):
        parse_price_gbp("Free")


def test_2_relative_to_absolute_urls():
    """Test 2: Relative catalogue URLs correctly resolve to absolute URLs."""
    html_catalog = """
    <article class="product_pod">
        <h3><a href="../a-light-in-the-attic_1000/index.html" title="A Light">A Light</a></h3>
    </article>
    """
    base_url = "https://books.toscrape.com/catalogue/category/books_1/page-1.html"
    links = extract_book_links_from_catalogue(html_catalog, base_url)
    assert len(links) == 1
    assert links[0] == "https://books.toscrape.com/catalogue/category/a-light-in-the-attic_1000/index.html"


def test_3_missing_description_handles_none():
    """Test 3: Books without description store None/null, never inventing fake text."""
    fixture_path = FIXTURES_DIR / "sample_book_no_desc.html"
    html = fixture_path.read_text(encoding="utf-8")
    record = extract_raw_book(
        html=html,
        product_url="https://books.toscrape.com/catalogue/test-book_1/index.html",
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-08-23T12:00:00Z",
    )
    assert record["description"] is None
    assert record["title"] == "Test Book Without Description"
    assert record["rating_text"] == "Four"
    assert record["price_text"] == "£19.99"


def test_4_duplicate_urls_deduplication():
    """Test 4: Duplicate book records are deduplicated by canonical product_url."""
    raw_records = [
        {
            "title": "Book 1",
            "product_url": "https://books.toscrape.com/catalogue/book-1/index.html",
            "price_text": "£10.00",
            "availability_text": "In stock",
            "rating_text": "Five",
            "description": "Desc 1",
            "source_page": "https://books.toscrape.com/catalogue/page-1.html",
            "fetched_at": "2026-08-23T12:00:00Z",
        },
        {
            "title": "Book 1 Duplicate",
            "product_url": "https://books.toscrape.com/catalogue/book-1/index.html",
            "price_text": "£10.00",
            "availability_text": "In stock",
            "rating_text": "Five",
            "description": "Desc 1",
            "source_page": "https://books.toscrape.com/catalogue/page-2.html",
            "fetched_at": "2026-08-23T12:00:00Z",
        },
    ]
    valid, invalid = validate_and_store_records(raw_records, output_filename="test_books.json")
    assert len(valid) == 1
    assert valid[0]["title"] == "Book 1"
    assert len(invalid) == 0


def test_5_malformed_fixture_handling():
    """Test 5: Parser handles malformed HTML fixtures gracefully without crashing."""
    fixture_path = FIXTURES_DIR / "sample_book_malformed.html"
    html = fixture_path.read_text(encoding="utf-8")
    record = extract_raw_book(
        html=html,
        product_url="https://books.toscrape.com/catalogue/broken-book_2/index.html",
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-08-23T12:00:00Z",
    )
    assert record["title"] == "Broken Book"
    assert record["price_text"] == "£0.99"
    assert record["availability_text"] == ""
    assert record["rating_text"] == ""
    assert record["description"] is None
