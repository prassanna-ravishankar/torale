import json

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self):
        # Initialize the sentence transformer model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    async def generate_embedding(self, text: str) -> str:
        """Generate embedding for the given text and return as JSON string."""
        embedding = self.model.encode(text)
        return json.dumps(embedding.tolist())

    async def compare_embeddings(
        self, embedding1_json: str, embedding2_json: str
    ) -> float:
        """Compare two embeddings and return cosine similarity."""
        embedding1 = json.loads(embedding1_json)
        embedding2 = json.loads(embedding2_json)

        # Convert to numpy arrays for efficient computation
        import numpy as np

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Compute cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity)
