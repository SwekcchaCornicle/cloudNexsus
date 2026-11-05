
"""
CloudNexus reusable extraction artifact importer.

Usage:
    python import_artifact.py "data/extracted/<document_id>/extraction.json"

The same repository handles AWS, Azure and GCP artifacts.
"""

import argparse
import json
from pathlib import Path

from app.infrastructure.neo4j_client import Neo4jClient
from app.infrastructure.graph_repository import GraphRepository


def load_artifact(file_path: Path):
    """Load and parse an extraction JSON artifact."""

    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        artifact = json.load(file)

    print("Loaded artifact:")
    print("Provider:", artifact.get("provider"))
    print("Document:", artifact.get("title"))
    print("Document ID:", artifact.get("document_id"))
    print("Chunks:", artifact.get("chunk_count"))

    return artifact


def main():
    parser = argparse.ArgumentParser(
        description="Import CloudNexus extraction artifact into Neo4j"
    )

    parser.add_argument(
        "artifact_path",
        help="Path to extraction.json",
    )

    args = parser.parse_args()
    artifact_path = Path(args.artifact_path)

    client = Neo4jClient()

    try:
        client.verify_connection()
        print("\nNeo4j connection successful.")

        artifact = load_artifact(artifact_path)

        repository = GraphRepository(client)

        result = repository.persist_artifact(artifact)

        print("\nPERSISTENCE COMPLETED")
        print("Provider:", artifact["provider"])
        print("Result:", result)

    finally:
        client.close()
        print("\nNeo4j connection closed.")


if __name__ == "__main__":
    main()
