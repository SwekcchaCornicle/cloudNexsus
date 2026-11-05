from __future__ import annotations

import json
import os
import re
from pathlib import Path


class LocalArtifactStore:
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or os.getenv("APP_DATA_DIR", "data"))

    @staticmethod
    def _safe_filename(filename: str) -> str:
        name = Path(filename).name
        name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
        return name or "document.html"

    def save(self, document_id, job_id, filename, raw_bytes, artifact) -> dict[str, str]:
        raw_dir = self.base_dir / "raw" / document_id
        processed_dir = self.base_dir / "processed" / document_id
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)

        raw_path = raw_dir / self._safe_filename(filename)
        processed_path = processed_dir / "chunks.json"

        raw_path.write_bytes(raw_bytes)
        processed_path.write_text(
            json.dumps(artifact, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return {
            "raw": str(raw_path.as_posix()),
            "processed": str(processed_path.as_posix()),
        }

    def save_job(self, job_id: str, result: dict) -> None:
        jobs_dir = self.base_dir / "jobs"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        (jobs_dir / f"{job_id}.json").write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )

    def get_job(self, job_id: str) -> dict | None:
        path = self.base_dir / "jobs" / f"{job_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
