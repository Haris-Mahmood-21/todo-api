"""
Run Reporter — Generates honest metrics summary and writes run-report.json.
"""
import json
from pathlib import Path
from typing import Dict, Any

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_run_report(
    start_time: str,
    duration_seconds: float,
    pages_fetched: int,
    cache_hits: int,
    valid_records: int,
    invalid_records: int,
    failed_pages: int,
    output_filename: str = "run-report.json",
) -> Dict[str, Any]:
    """
    Generate and save the run report JSON.
    """
    report = {
        "start_time": start_time,
        "duration_seconds": round(duration_seconds, 2),
        "pages_fetched": pages_fetched,
        "cache_hits": cache_hits,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "failed_pages": failed_pages,
    }

    report_path = OUTPUT_DIR / output_filename
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
