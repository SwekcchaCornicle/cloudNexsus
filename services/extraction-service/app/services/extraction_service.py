from app.domain.schemas import IngestionArtifact, ExtractedChunk, ExtractionArtifact

class ExtractionService:
    def __init__(self, embedding_provider, knowledge_extractor, artifact_store):
        self.embedding_provider = embedding_provider
        self.knowledge_extractor = knowledge_extractor
        self.artifact_store = artifact_store

    def process(self, artifact: IngestionArtifact):
        results = []
        for chunk in artifact.chunks:
            vector = self.embedding_provider.embed(chunk.content)
            knowledge = self.knowledge_extractor.extract(chunk.content, chunk.provider, chunk.service_name)
            source = " ".join(chunk.content.lower().split())
            for rel in knowledge.relationships:
                evidence = " ".join(rel.evidence.lower().split())
                if evidence not in source:
                    raise ValueError("Relationship evidence was not found in the source chunk.")
            results.append(ExtractedChunk(
                chunk_id=chunk.chunk_id, document_id=chunk.document_id,
                provider=chunk.provider, service_name=chunk.service_name,
                source_url=str(chunk.source_url), heading_path=chunk.heading_path,
                content=chunk.content, embedding=vector,
                embedding_model_id=self.embedding_provider.model_id,
                extraction=knowledge,
            ))
        output = ExtractionArtifact(
            document_id=artifact.metadata.document_id, provider=artifact.metadata.provider,
            title=artifact.metadata.title, source_url=str(artifact.metadata.source_url),
            extraction_mode=self.embedding_provider.mode, chunk_count=len(results), chunks=results,
        )
        path = self.artifact_store.save(output)
        return {
            "document_id": output.document_id, "provider": output.provider.value,
            "status": "COMPLETED", "chunk_count": output.chunk_count,
            "entity_count": sum(len(c.extraction.entities) for c in results),
            "relationship_count": sum(len(c.extraction.relationships) for c in results),
            "mode": output.extraction_mode, "artifact_path": path,
        }
