
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

import requests


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "document_manifest.json"
RAW_DIR = ROOT / "dataset" / "raw"
REPORT_DIR = ROOT / "dataset" / "reports"
STATE_FILE = REPORT_DIR / "ingestion_extraction_state.json"

INGESTION_URL = "http://127.0.0.1:8000/api/v1/ingestion/jobs"
EXTRACTION_URL = "http://127.0.0.1:8001/api/v1/extractions"

INGESTION_DIR = ROOT / "services" / "ingestion-service"
EXTRACTION_DIR = ROOT / "services" / "extraction-service"


def save_state(state):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8"
    )


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))

    return {"completed": [], "failed": []}


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


def find_raw_file(document):
    provider = document["provider"].upper()
    doc_id = safe_name(document["id"])

    expected = RAW_DIR / provider / f"{doc_id}.html"

    if expected.exists():
        return expected

    matches = list((RAW_DIR / provider).glob(f"{doc_id}*.html"))

    if matches:
        return matches[0]

    raise FileNotFoundError(
        f"Downloaded HTML not found for {document['id']}: {expected}"
    )


def resolve_artifact(base_dir, artifact_path):
    path = Path(artifact_path)

    if path.is_absolute():
        return path

    return base_dir / path


def process_document(document):
    doc_id = document["id"]
    print(f"\n{'=' * 65}")
    print(f"PROCESSING: {doc_id}")
    print(f"Provider: {document['provider']} | Service: {document['service_name']}")

    raw_file = find_raw_file(document)
    print(f"[1/2] Ingestion: {raw_file}")

    with raw_file.open("rb") as file_handle:
        response = requests.post(
            INGESTION_URL,
            files={
                "file": (
                    raw_file.name,
                    file_handle,
                    "text/html"
                )
            },
            data={
                "provider": document["provider"],
                "service_name": document["service_name"],
                "source_url": document["url"]
            },
            timeout=300
        )

    if not response.ok:
        raise RuntimeError(
            f"Ingestion failed ({response.status_code}): {response.text[:2000]}"
        )

    ingestion_result = response.json()

    processed_path = resolve_artifact(
        INGESTION_DIR,
        ingestion_result["processed_artifact"]
    )

    if not processed_path.exists():
        raise FileNotFoundError(
            f"Ingestion artifact not found: {processed_path}"
        )

    ingestion_artifact = json.loads(
        processed_path.read_text(encoding="utf-8")
    )

    print(
        f"Ingestion complete: "
        f"{ingestion_result.get('chunk_count', len(ingestion_artifact.get('chunks', [])))} chunks"
    )

    print("[2/2] Extraction: sending chunks to Vertex AI...")

    extraction_response = requests.post(
        EXTRACTION_URL,
        json=ingestion_artifact,
        timeout=1800
    )

    if not extraction_response.ok:
        raise RuntimeError(
            f"Extraction failed ({extraction_response.status_code}): "
            f"{extraction_response.text[:3000]}"
        )

    extraction_result = extraction_response.json()

    artifact_value = extraction_result.get("artifact_path")

    if artifact_value:
        extraction_path = resolve_artifact(
            EXTRACTION_DIR,
            artifact_value
        )
    else:
        extraction_path = (
            EXTRACTION_DIR
            / "data"
            / "extracted"
            / ingestion_result["document_id"]
            / "extraction.json"
        )

    if not extraction_path.exists():
        raise FileNotFoundError(
            f"Extraction API returned success, but artifact was not found: "
            f"{extraction_path}\nResponse: {extraction_result}"
        )

    print("Extraction complete.")
    print(f"Artifact: {extraction_path}")

    return {
        "manifest_id": doc_id,
        "document_id": ingestion_result.get("document_id"),
        "provider": document["provider"],
        "service_name": document["service_name"],
        "source_url": document["url"],
        "chunks": ingestion_result.get("chunk_count"),
        "extraction_artifact": str(extraction_path),
        "status": "completed"
    }


def main():
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST}")

    documents = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # The first manifest entry is the document already tested.
    documents = documents[1:]

    state = load_state()
    completed_ids = set(state.get("completed", []))

    print(f"Documents in batch: {len(documents)}")
    print(f"Already completed in this batch: {len(completed_ids)}")
    print(f"Remaining: {len([d for d in documents if d['id'] not in completed_ids])}")

    # Confirm both services are responding before processing.
    for name, url in [
        ("Ingestion", "http://127.0.0.1:8000/health"),
        ("Extraction", "http://127.0.0.1:8001/health")
    ]:
        try:
            health = requests.get(url, timeout=5)
            health.raise_for_status()
            print(f"{name} service: available")
        except requests.RequestException as exc:
            raise RuntimeError(
                f"{name} service is not responding at {url}. "
                f"Start it before running this script. Details: {exc}"
            )

    for document in documents:
        doc_id = document["id"]

        if doc_id in completed_ids:
            print(f"\nSKIPPING already completed: {doc_id}")
            continue

        try:
            result = process_document(document)

            state["completed"].append(doc_id)
            state.setdefault("results", []).append(result)

        except Exception as exc:
            print(f"\nFAILED: {doc_id}")
            print(str(exc))

            state.setdefault("failed", [])
            state["failed"] = [
                item for item in state["failed"]
                if item["id"] != doc_id
            ]
            state["failed"].append({
                "id": doc_id,
                "error": str(exc),
                "time": datetime.now(timezone.utc).isoformat()
            })

        save_state(state)

    print("\n" + "=" * 65)
    print("BATCH FINISHED")
    print(f"Completed: {len(state.get('completed', []))}")
    print(f"Failed: {len(state.get('failed', []))}")
    print(f"Report: {STATE_FILE}")


if __name__ == "__main__":
    main()
