# The Polite Scraper — Books to Scrape Pipeline

A polite, robust, and idempotent web scraping pipeline built in Python with `requests`, `BeautifulSoup4`, and `Pydantic` for **FlyRank Internship — Backend Track, Week 5, Assignment A9**.

---

## Target Classification

- **Target Site**: [Books to Scrape](https://books.toscrape.com) (`https://books.toscrape.com`)
- **Why this target**: Books to Scrape is an official sandbox environment built specifically for learning and practicing web scraping safely without causing harm or violating commercial terms of service.
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

## Politeness Rules Followed

1. **Honest User-Agent**: Every request identifies itself:
   `FlyRankInternship-A9/1.0 (+https://github.com/Haris-Mahmood-21/todo-api)`
2. **Politeness Delay**: A minimum delay of $\ge 500\,\text{ms}$ is enforced between consecutive network requests to avoid overloading the server.
3. **HTTP Caching**: All fetched HTML pages (catalogue and book detail pages) are saved to `scraper/cache/`. Development and repeated runs read from the local cache with zero network overhead.
4. **Request Timeout**: A strict 10-second timeout prevents requests from hanging indefinitely.
5. **Status Code Verification**: Only HTTP 200 responses are treated as valid HTML pages.
6. **Isolated Fault Tolerance**: Each book detail fetch/parse is isolated. A failed page is logged and skipped without crashing the remaining pipeline.

