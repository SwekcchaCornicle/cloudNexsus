"""Typed settings: one place for environment configuration and startup validation."""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    embedding_mode: str = Field("vertex", alias="EMBEDDING_MODE")
    gcp_project_id: str = Field("", alias="GCP_PROJECT_ID")
    gcp_region: str = Field("global", alias="GCP_REGION")
    vertex_embedding_model: str = Field("gemini-embedding-001", alias="VERTEX_EMBEDDING_MODEL")
    embedding_dimensions: int = Field(1024, alias="EMBEDDING_DIMENSIONS")
    neo4j_uri: str = Field("", alias="NEO4J_URI")
    neo4j_username: str = Field("", alias="NEO4J_USERNAME")
    neo4j_password: str = Field("", alias="NEO4J_PASSWORD")
    neo4j_database: str = Field("neo4j", alias="NEO4J_DATABASE")
    vector_index_name: str = Field("chunk_embedding_index", alias="VECTOR_INDEX_NAME")
    default_top_k: int = Field(5, alias="DEFAULT_TOP_K")
    max_top_k: int = Field(20, alias="MAX_TOP_K")

    def validate_runtime(self):
        """Fail early instead of starting a service with incomplete credentials."""
        if self.embedding_mode.lower() != "vertex":
            raise ValueError("Only EMBEDDING_MODE=vertex is supported.")
        missing = [key for key, value in {
            "GCP_PROJECT_ID": self.gcp_project_id, "NEO4J_URI": self.neo4j_uri,
            "NEO4J_USERNAME": self.neo4j_username, "NEO4J_PASSWORD": self.neo4j_password
        }.items() if not value]
        if missing:
            raise ValueError("Missing environment variables: " + ", ".join(missing))
        if self.embedding_dimensions != 1024:
            raise ValueError("Expected 1024 dimensions to match Extraction Service.")

@lru_cache
def get_settings():
    """Cache one settings object for the application process."""
    return Settings()
