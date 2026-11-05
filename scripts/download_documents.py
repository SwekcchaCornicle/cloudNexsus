
"""Download official cloud documentation listed in document_manifest.json."""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "scripts" / "document_manifest.json"
RAW_DATA_DIR = PROJECT_ROOT / "dataset" / "raw"
REPORT_DIR = PROJECT_ROOT / "dataset" / "reports"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
REQUEST_DELAY_SECONDS = 1.5

ALLOWED_HOST_SUFFIXES = {
    "AWS": ("docs.aws.amazon.com",),
    "AZURE": ("learn.microsoft.com",),
    "GCP": ("cloud.google.com",),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("cloudnexus.downloader")


def load_manifest() -> list[dict]:
    """Load and validate document definitions."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")

    documents = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    if not isinstance(documents, list):
        raise ValueError("Manifest must contain a JSON list.")

    seen_ids = set()

    for document in documents:
        required = {"id", "provider", "service_name", "url"}

        if not required.issubset(document):
            raise ValueError(
                f"Document is missing fields: {required - set(document)}"
            )

        document_id = document["id"]
        provider = document["provider"].upper()
        url = document["url"]

        if document_id in seen_ids:
            raise ValueError(f"Duplicate document ID: {document_id}")

        seen_ids.add(document_id)

        if provider not in ALLOWED_HOST_SUFFIXES:
            raise ValueError(f"Unsupported provider: {provider}")

        parsed = urlparse(url)

        if parsed.scheme != "https":
            raise ValueError(f"Only HTTPS URLs are allowed: {url}")

        hostname = (parsed.hostname or "").lower()

        allowed = any(
            hostname == suffix or hostname.endswith("." + suffix)
            for suffix in ALLOWED_HOST_SUFFIXES[provider]
        )

        if not allowed:
            raise ValueError(
                f"URL host {hostname!r} is not approved for {provider}."
            )

    return documents


def safe_filename(document_id: str) -> str:
    """Convert manifest ID into a safe local filename."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", document_id) + ".html"


def download_document(document: dict) -> dict:
    """Download one HTML page with retry and validation."""
    provider = document["provider"].upper()
    document_id = document["id"]
    url = document["url"]

    output_dir = RAW_DATA_DIR / provider
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / safe_filename(document_id)

    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("Skipping existing file: %s", document_id)

        return {
            "id": document_id,
            "provider": provider,
            "url": url,
            "status": "SKIPPED",
            "file_path": str(output_path.relative_to(PROJECT_ROOT)),
            "bytes": output_path.stat().st_size,
        }

    headers = {
        "User-Agent": "CloudNexusDocumentationResearch/1.0"
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            if "html" not in content_type:
                raise ValueError(
                    f"Expected HTML but received: {content_type}"
                )

            if not response.content.strip():
                raise ValueError("Downloaded document is empty.")

            # Check for an HTML document before saving.
            beginning = response.text[:1000].lower()

            if "<html" not in beginning and "<!doctype html" not in beginning:
                raise ValueError("Response does not appear to be HTML.")

            output_path.write_bytes(response.content)

            logger.info(
                "Downloaded %s | %s | %s bytes",
                provider,
                document_id,
                len(response.content),
            )

            return {
                "id": document_id,
                "provider": provider,
                "url": url,
                "status": "DOWNLOADED",
                "file_path": str(output_path.relative_to(PROJECT_ROOT)),
                "bytes": len(response.content),
            }

        except (requests.RequestException, ValueError) as exc:
            logger.warning(
                "Attempt %s/%s failed for %s: %s",
                attempt,
                MAX_RETRIES,
                document_id,
                exc,
            )

            if attempt == MAX_RETRIES:
                return {
                    "id": document_id,
                    "provider": provider,
                    "url": url,
                    "status": "FAILED",
                    "error": str(exc),
                }

            time.sleep(attempt * 2)

    raise RuntimeError("Unexpected downloader state.")


def main() -> None:
    documents = load_manifest()

    logger.info("Documents in manifest: %s", len(documents))

    results = []

    for index, document in enumerate(documents, start=1):
        logger.info(
            "[%s/%s] Processing %s",
            index,
            len(documents),
            document["id"],
        )

        result = download_document(document)
        results.append(result)

        time.sleep(REQUEST_DELAY_SECONDS)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "total": len(results),
        "downloaded": sum(
            item["status"] == "DOWNLOADED" for item in results
        ),
        "skipped": sum(
            item["status"] == "SKIPPED" for item in results
        ),
        "failed": sum(
            item["status"] == "FAILED" for item in results
        ),
        "results": results,
    }

    report_path = REPORT_DIR / "download_report.json"

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    logger.info("Download report: %s", report_path)
    logger.info(
        "Finished | Downloaded: %s | Skipped: %s | Failed: %s",
        report["downloaded"],
        report["skipped"],
        report["failed"],
    )


if __name__ == "__main__":
    main()
