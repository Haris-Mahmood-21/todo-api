# The Polite Scraper — Books to Scrape Pipeline

A polite, resilient, and idempotent web scraping pipeline built with **Python 3**, `requests`, `BeautifulSoup4`, and `Pydantic` for **FlyRank Internship — Backend Track, Week 5, Assignment A9**.

---

## 1. Target Classification

- **Target Site**: [Books to Scrape](https://books.toscrape.com) (`https://books.toscrape.com`)
- **Why this target**: Books to Scrape is an official sandbox environment built specifically for developers to learn and practice web scraping safely without causing harm or violating commercial terms of service.
- **Scope & Scale**: Exactly the first **3 catalogue pages** (`page-1.html`, `page-2.html`, `page-3.html`), discovering and extracting all **60 book detail pages**.
- **Data Collected**:
  - `title` (string): Title of the book.
  - `product_url` (string / URL): Canonical absolute URL of the book detail page.
  - `price_text` (string): Raw scraped price string (e.g. `£51.77`).
  - `price_gbp` (float): Clean, normalized numeric price in GBP (e.g. `51.77`).
  - `availability_text` (string): Stock availability status (e.g. `In stock (22 available)`).
  - `rating_text` (string): Rating word representation (e.g. `Three`).
  - `description` (string or null): Book product description (or `null` if missing).
  - `source_page` (string / URL): Catalogue page where the book link was discovered (provenance).
  - `fetched_at` (string): ISO 8601 UTC timestamp of fetch time (provenance).
- **Why this is appropriate**: We collect only public catalog information from an authorized sandbox environment at minimal request volume, respecting site resources.
- **Robots.txt Result**: `https://books.toscrape.com/robots.txt` was requested and returned **HTTP 404 (no robots file found)**. A missing robots file is not permission on its own; our permission is derived from the site's explicit designation as a scraping sandbox.

> **Mandatory Policy Commitment**:  
> *"I will not reuse this code on another site without checking its rules and terms first."*

---

## 2. Quickstart & Installation

Clone the repository and run the full pipeline in under 2 minutes:

```bash
# 1. Clone repo & enter directory
git clone https://github.com/Haris-Mahmood-21/todo-api.git
cd todo-api

# 2. Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the full scraping pipeline (end-to-end)
PYTHONPATH=. python scraper/src/main.py --stage 5
```

Outputs will be generated in `scraper/output/`:
- `scraper/output/books.json` — 60 validated clean book records.
- `scraper/output/books.csv` — Flattened CSV export.
- `scraper/output/run-report.json` — Run statistics & execution audit.
- `scraper/output/errors.json` — Any validation errors or skipped records.

### Running Unit Tests

Run the 5-point parser and schema unit test suite:

```bash
PYTHONPATH=. pytest scraper/tests/test_parser.py -v
```

---

## 3. Tooling & Architecture (Python Lane)

| Component | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.10+ (tested on Python 3.14) | Core language runtime |
| **HTTP Client** | `requests` | Polite HTTP requests with headers, timeouts, and status checks |
| **HTML Parser** | `BeautifulSoup4` | Robust DOM traversal and CSS selector extraction |
| **Schema Validator** | `Pydantic` (v2) | Strict data normalization, type validation, and URL checking |
| **Testing** | `pytest` | Fixture-based unit tests for parser resilience |
| **Data Output** | Built-in `json` & `csv` modules | Idempotent file persistence |

---

## 4. Politeness Rules Followed

1. **Honest User-Agent**: Every request identifies itself:
   `FlyRankInternship-A9/1.0 (+https://github.com/Haris-Mahmood-21/todo-api)`
2. **Politeness Delay**: A minimum delay of $\ge 500\,\text{ms}$ is enforced between consecutive network requests to avoid overloading the server.
3. **HTTP Caching**: All fetched HTML pages (catalogue and book detail pages) are saved to `scraper/cache/`. Development and repeated runs read from the local cache with zero network overhead and zero delay.
4. **Request Timeout**: A strict 10-second timeout prevents requests from hanging indefinitely.
5. **Status Code Verification**: Only HTTP 200 responses are treated as valid HTML pages.
6. **Smart Retries**: Network timeouts and 5xx server errors retry once after a short backoff; 404 (Not Found) and 403 (Forbidden) client errors are **never** retried.
7. **Isolated Fault Tolerance**: Each book detail fetch/parse is isolated in a `try...except` block. A single broken page is logged and skipped without crashing the remaining 59 records.

---

## 5. Record Schema & Data Model

Every scraped book record conforms to the following Pydantic schema:

```python
class BookRecord(BaseModel):
    title: str = Field(..., min_length=1, description="Book title")
    product_url: str = Field(..., description="Canonical absolute URL")
    price_text: str = Field(..., min_length=1, description="Raw price text (e.g. £51.77)")
    price_gbp: float = Field(..., ge=0.0, description="Clean numeric price in GBP (e.g. 51.77)")
    availability_text: str = Field(..., description="Stock availability status")
    rating_text: str = Field(..., description="Rating string representation (One..Five)")
    description: Optional[str] = Field(default=None, description="Optional book description or null")
    source_page: str = Field(..., description="Catalogue page URL where link was found")
    fetched_at: str = Field(..., min_length=1, description="ISO 8601 UTC timestamp")
```

---

## 6. Sample Output Record

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-08-23T16:33:03Z"
}
```

---

## 7. Real Run Report Proof

Verbatim output of `scraper/output/run-report.json`:

```json
{
  "start_time": "2026-08-23T16:34:40Z",
  "duration_seconds": 0.26,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

When run with deliberate failure injection (`--test-failure`):
```json
{
  "start_time": "2026-08-23T16:33:49Z",
  "duration_seconds": 1.20,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
```

---

## 8. Why This Assignment Needed No Browser

The data on Books to Scrape is entirely present in the static HTML rendered by the server. Using plain HTTP requests with `BeautifulSoup4` is significantly faster, uses under 30MB of RAM, and avoids the heavy CPU, memory, and binary overhead of launching a headless Chromium/Firefox instance via Playwright or Puppeteer. A browser would only add unnecessary cost without providing any benefit.

---

## 9. Web Scraping Ethics Statement

1. **Use Official APIs First**: Whenever an official API or data feed is provided by the service, use it instead of scraping HTML.
2. **Never Bypass Access Controls**: Never attempt to bypass authentication walls, login requirements, paywalls, CAPTCHAs, or IP rate-limit blocks.
3. **Respect Server Resources**: Always throttle requests ($\ge 500\,\text{ms}$ delay), identify yourself with an honest User-Agent and contact info, and use local caching to avoid duplicate requests.
4. **Minimalist Data Collection**: Scrape only the specific data fields required for the application, discard unnecessary payloads, and respect robots policies and site terms of service.

---

## 10. Honest Limitations

1. **Static DOM Selector Dependence**: The extractor relies on CSS selectors (`.product_main`, `#product_description ~ p`). If the target site updates its template markup or class names, the extractor selectors will need manual adjustment.
2. **Fixed Page Scope**: The pagination logic terminates after 3 catalogue pages (60 books). Crawling the entire 1,000-book catalog would require adjusting `max_pages` or crawling until `next_page` is null.

---

## 11. Bonus Stage: AI Rematch ("AI vs Me")

An AI-generated scraping pipeline was built from a standalone specification prompt (`scraper/ai-version/prompt.txt`) and quarantined in `scraper/ai-version/ai_scraper.py`.

### Comparison Analysis:
1. **What the AI did well**: The AI effectively combined fetching, parsing, and Pydantic validation into a concise, self-contained single script.
2. **What the AI missed / got wrong**:
   - The AI version coupled all responsibilities (caching, crawling, extracting, validating, reporting) into a single monolithic class, making unit testing individual parts difficult.
   - The AI's price regex (`\d+\.\d+`) failed on integer prices without decimal cents (e.g. `£50`), whereas our hand-built version supports `\d+(?:\.\d+)?`.
   - The AI's description selector `#product_description ~ p` did not guard against missing sibling paragraphs as cleanly as the modular extractor.
3. **What the prompt forgot to specify**: The initial prompt did not specify CSV flattening requirements or isolated test fixture handling, which was easily accommodated by our modular architecture.

---

## 12. Project Structure & Legacy Code Preservation

```
todo-api/
├── scraper/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py              # CLI entry point & orchestrator pipeline
│   │   ├── fetcher.py           # Polite HTTP fetcher with local caching & retry logic
│   │   ├── crawler.py           # Catalogue pagination & book URL discovery
│   │   ├── extractor.py         # BeautifulSoup HTML parsing for raw book details
│   │   ├── models.py            # Pydantic schemas, normalization & CSV export
│   │   └── reporter.py          # Metrics collector & run-report.json generator
│   ├── cache/                   # Cached HTML files (gitignored)
│   ├── output/
│   │   ├── books.json           # 60 validated clean book records
│   │   ├── books.csv            # Flattened CSV export
│   │   ├── errors.json          # Failed/invalid records with reason
│   │   └── run-report.json      # Run statistics & provenance audit
│   ├── tests/
│   │   ├── fixtures/            # Static HTML snippets for deterministic testing
│   │   └── test_parser.py       # 5 parser unit tests (price, URLs, null desc, etc.)
│   ├── ai-version/              # Quarantined AI-generated version
│   │   ├── prompt.txt           # Prompt used to generate rematch version
│   │   └── ai_scraper.py        # Quarantined AI script
│   ├── .gitignore               # Scraper gitignore (ignores cache/, __pycache__, etc.)
│   └── README.md                # This documentation file
├── main.py                      # Preserved from W4 (Supabase Auth API & commented A3 code)
├── requirements.txt             # Updated with requests, beautifulsoup4, pytest
├── compose.yaml                 # Preserved from A3
├── dockerfile                   # Preserved from A3
└── Readme.md                    # Root README preserved & updated with link to scraper/
```
