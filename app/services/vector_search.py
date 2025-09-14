"""
Vector search service using Vertex AI embeddings
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.services.vertex_ai import vertex_ai_service

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Vector search service using Vertex AI embeddings"""
    
    def __init__(self):
        self.embedding_model = settings.vertex_ai_embedding_model
        self.embedding_dimension = self._get_embedding_dimension()
    
    def _get_embedding_dimension(self) -> int:
        """Get embedding dimension for the model"""
        try:
            # Test embedding to get dimension
            test_embedding = vertex_ai_service.generate_embedding("test")
            return len(test_embedding)
        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {e}")
            return 768  # Default dimension for text-embedding-gecko
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for texts"""
        try:
            embeddings = vertex_ai_service.generate_embeddings(texts)
            logger.info(f"Created embeddings for {len(texts)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to create embeddings: {e}")
            raise
    
    def create_embedding(self, text: str) -> List[float]:
        """Create single embedding"""
        embeddings = self.create_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {e}")
            return 0.0
    
    def search_similar_documents(
        self, 
        query: str, 
        document_embeddings: List[Dict[str, Any]], 
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query)
            
            # Calculate similarities
            similarities = []
            for doc in document_embeddings:
                doc_embedding = doc.get("embedding", [])
                if doc_embedding:
                    similarity = self.cosine_similarity(query_embedding, doc_embedding)
                    if similarity >= threshold:
                        similarities.append({
                            "document_id": doc.get("document_id"),
                            "chunk_id": doc.get("chunk_id"),
                            "content": doc.get("content"),
                            "similarity": similarity,
                            "metadata": doc.get("metadata", {})
                        })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            return []
    
    def batch_search(
        self, 
        queries: List[str], 
        document_embeddings: List[Dict[str, Any]], 
        top_k: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """Batch search for multiple queries"""
        try:
            results = []
            for query in queries:
                similar_docs = self.search_similar_documents(query, document_embeddings, top_k)
                results.append(similar_docs)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform batch search: {e}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension for the model"""
        return self.embedding_dimension
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate if embedding has correct dimension"""
        return len(embedding) == self.embedding_dimension
    
    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding vector"""
        try:
            vec = np.array(embedding)
            norm = np.linalg.norm(vec)
            if norm == 0:
                return embedding
            normalized = vec / norm
            return normalized.tolist()
        except Exception as e:
            logger.error(f"Failed to normalize embedding: {e}")
            return embedding


# Global instance
vector_search_service = VectorSearchService()
