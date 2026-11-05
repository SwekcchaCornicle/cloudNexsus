import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load local .env before settings are instantiated; deployment can inject env vars.
load_dotenv()

@dataclass(frozen=True)
class Settings:
    """Immutable application configuration."""
    extraction_mode: str = os.getenv("EXTRACTION_MODE", "local").strip().lower()
    aws_region: str = os.getenv("AWS_REGION", "ap-south-1")
    aws_profile: str | None = os.getenv("AWS_PROFILE") or None
    embedding_model_id: str = os.getenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
    chat_model_id: str = os.getenv("BEDROCK_CHAT_MODEL_ID", "")
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
    app_data_dir: str = os.getenv("APP_DATA_DIR", "data")
    # Vertex settings are separate; credentials come from ADC, not this file.
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "").strip()
    gcp_region: str = os.getenv("GCP_REGION", "global").strip()
    vertex_chat_model: str = os.getenv("VERTEX_CHAT_MODEL", "gemini-3.8-flash").strip()
    vertex_embedding_model: str = os.getenv("VERTEX_EMBEDDING_MODEL", "gemini-embedding-001").strip()

settings = Settings()
