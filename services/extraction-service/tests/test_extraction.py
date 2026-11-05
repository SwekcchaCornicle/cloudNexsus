from app.domain.schemas import Provider, IngestionArtifact, DocumentMetadata, InputChunk
from app.infrastructure.providers import LocalEmbeddingProvider, LocalKnowledgeExtractor
from app.infrastructure.artifact_store import LocalArtifactStore
from app.services.extraction_service import ExtractionService

def test_local_extraction_pipeline(tmp_path):
    doc_id = "doc-test"
    artifact = IngestionArtifact(
        metadata=DocumentMetadata(
            document_id=doc_id, provider=Provider.AWS, service_name="Lambda",
            source_url="https://docs.aws.amazon.com/lambda/", title="AWS Lambda",
            filename="lambda.html", checksum_sha256="abc123"
        ),
        chunks=[InputChunk(
            chunk_id="doc-test:00000", document_id=doc_id, provider=Provider.AWS,
            service_name="Lambda", title="AWS Lambda",
            source_url="https://docs.aws.amazon.com/lambda/", chunk_index=0,
            heading_path=["AWS Lambda","Overview"],
            content="AWS Lambda is a serverless compute service.",
            approximate_token_count=9, content_hash="hash"
        )]
    )
    service = ExtractionService(LocalEmbeddingProvider(), LocalKnowledgeExtractor(), LocalArtifactStore(str(tmp_path)))
    result = service.process(artifact)
    assert result["status"] == "COMPLETED"
    assert result["chunk_count"] == 1
    assert result["entity_count"] >= 1
    assert result["mode"] == "local"
