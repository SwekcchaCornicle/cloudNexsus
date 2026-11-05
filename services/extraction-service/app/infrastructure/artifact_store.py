import json
from pathlib import Path
from app.domain.schemas import ExtractionArtifact

class LocalArtifactStore:
    def __init__(self, base_dir="data"):
        self.base_dir = Path(base_dir)

    def save(self, artifact: ExtractionArtifact):
        folder = self.base_dir / "extracted" / artifact.document_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "extraction.json"
        path.write_text(json.dumps(artifact.model_dump(mode="json"), indent=2), encoding="utf-8")
        return path.as_posix()
