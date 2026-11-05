"""Vertex AI adapter: embed the question in the same vector space as extracted chunks."""
from google import genai
from google.genai import types

class VertexEmbeddingClient:
    def __init__(self, project_id, region, model, dimensions):
        if not project_id:
            raise ValueError("GCP_PROJECT_ID is required.")
        self.model, self.dimensions = model, dimensions
        # Uses Application Default Credentials; no API key is embedded in code.
        self.client = genai.Client(vertexai=True, project=project_id, location=region)

    def embed_query(self, question: str) -> list[float]:
        """Call the same embedding model/dimensionality used during document extraction."""
        response = self.client.models.embed_content(
            model=self.model,
            contents=question,
            config=types.EmbedContentConfig(output_dimensionality=self.dimensions),
        )
        if not response.embeddings or not response.embeddings[0].values:
            raise RuntimeError("Vertex AI returned an empty embedding.")
        vector = [float(value) for value in response.embeddings[0].values]
        if len(vector) != self.dimensions:
            raise RuntimeError(f"Expected {self.dimensions} values, received {len(vector)}.")
        return vector
