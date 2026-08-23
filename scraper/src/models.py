"""
Data Schema and Normalization using Pydantic.
"""
import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field, HttpUrl, field_validator


def parse_price_gbp(price_text: str) -> float:
    """
    Extract numeric price in GBP from raw price string (e.g. '£51.77' -> 51.77).
    """
    if not price_text:
        raise ValueError("price_text cannot be empty")
    match = re.search(r"(\d+(?:\.\d+)?)", price_text)
    if not match:
        raise ValueError(f"Could not parse numeric price from: '{price_text}'")
    return round(float(match.group(1)), 2)


class BookRecord(BaseModel):
    """
    Schema for a validated, normalized book record.
    """
    title: str = Field(..., min_length=1, description="Book title")
    product_url: str = Field(..., description="Canonical absolute URL")
    price_text: str = Field(..., min_length=1, description="Raw price text")
    price_gbp: float = Field(..., ge=0.0, description="Normalized numeric price in GBP")
    availability_text: str = Field(..., description="Availability status text")
    rating_text: str = Field(..., description="Rating string representation")
    description: Optional[str] = Field(default=None, description="Optional book description")
    source_page: str = Field(..., description="Provenance catalogue page URL")
    fetched_at: str = Field(..., min_length=1, description="ISO 8601 UTC timestamp")

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"URL must start with http:// or https://: {v}")
        return v


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def validate_and_store_records(
    raw_records: List[Dict[str, Any]],
    output_filename: str = "books.json",
    error_filename: str = "errors.json",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Normalize and validate raw records against BookRecord schema.
    Write valid records to output/books.json and errors to output/errors.json.
    Deduplicates by product_url (canonical identity).
    Returns (valid_records, invalid_records).
    """
    valid_records: List[Dict[str, Any]] = []
    invalid_records: List[Dict[str, Any]] = []
    seen_canonical_urls = set()

    for raw in raw_records:
        product_url = raw.get("product_url", "")
        if product_url in seen_canonical_urls:
            # Duplicate URL - already processed
            continue

        try:
            # 1. Normalize price
            raw_price = raw.get("price_text", "")
            price_gbp = parse_price_gbp(raw_price)

            # 2. Build record dict
            record_data = dict(raw)
            record_data["price_gbp"] = price_gbp

            # 3. Schema validation
            validated = BookRecord(**record_data)
            valid_dict = validated.model_dump()
            valid_records.append(valid_dict)
            seen_canonical_urls.add(product_url)
        except Exception as err:
            invalid_records.append({"raw_record": raw, "error": str(err)})

    # Write output/books.json idempotently
    books_file = OUTPUT_DIR / output_filename
    books_file.write_text(json.dumps(valid_records, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write output/errors.json
    errors_file = OUTPUT_DIR / error_filename
    errors_file.write_text(json.dumps(invalid_records, indent=2, ensure_ascii=False), encoding="utf-8")

    return valid_records, invalid_records
