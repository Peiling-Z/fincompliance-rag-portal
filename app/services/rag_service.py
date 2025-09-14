"""
RAG (Retrieval-Augmented Generation) service for intelligent Q&A
"""
import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentChunk, QueryLog
from app.services.vector_search import vector_search_service
from app.services.vertex_ai import vertex_ai_service

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service that combines retrieval and generation"""
    
    def __init__(self):
        self.default_top_k = 5
        self.default_threshold = 0.7
        self.max_context_length = 4000  # Maximum context length for LLM
    
    def ask_question(
        self, 
        question: str, 
        user_id: int, 
        db: Session,
        document_ids: Optional[List[int]] = None,
        top_k: int = None,
        threshold: float = None
    ) -> Dict[str, Any]:
        """Ask a question and get an AI-generated answer"""
        try:
            start_time = time.time()
            
            # Set default parameters
            top_k = top_k or self.default_top_k
            threshold = threshold or self.default_threshold
            
            # Step 1: Retrieve relevant documents
            relevant_chunks = self._retrieve_relevant_documents(
                question, user_id, db, document_ids, top_k, threshold
            )
            
            if not relevant_chunks:
                return {
                    "answer": "I couldn't find any relevant information to answer your question. Please try rephrasing your question or upload more documents.",
                    "sources": [],
                    "confidence": 0.0,
                    "response_time_ms": (time.time() - start_time) * 1000,
                    "query_id": None
                }
            
            # Step 2: Prepare context
            context = self._prepare_context(relevant_chunks)
            
            # Step 3: Generate answer using Vertex AI
            answer = self._generate_answer(question, context)
            
            # Step 4: Calculate confidence score
            confidence = self._calculate_confidence(relevant_chunks, answer)
            
            # Step 5: Log the query
            query_id = self._log_query(
                user_id, question, answer, relevant_chunks, 
                (time.time() - start_time) * 1000, db
            )
            
            response_time = (time.time() - start_time) * 1000
            
            logger.info(f"Question answered successfully: {question[:50]}...")
            
            return {
                "answer": answer,
                "sources": self._format_sources(relevant_chunks),
                "confidence": confidence,
                "response_time_ms": response_time,
                "query_id": query_id
            }
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            raise
    
    def _retrieve_relevant_documents(
        self, 
        question: str, 
        user_id: int, 
        db: Session,
        document_ids: Optional[List[int]] = None,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant document chunks"""
        try:
            # Get document chunks from database
            query = db.query(DocumentChunk).join(Document).filter(Document.user_id == user_id)
            
            if document_ids:
                query = query.filter(Document.id.in_(document_ids))
            
            chunks = query.all()
            
            if not chunks:
                return []
            
            # Prepare chunks for vector search
            document_embeddings = []
            for chunk in chunks:
                if chunk.metadata and "embedding" in chunk.metadata:
                    document_embeddings.append({
                        "document_id": chunk.document_id,
                        "chunk_id": chunk.id,
                        "content": chunk.content,
                        "embedding": chunk.metadata["embedding"],
                        "metadata": chunk.metadata
                    })
            
            # Search for similar documents
            similar_docs = vector_search_service.search_similar_documents(
                question, document_embeddings, top_k, threshold
            )
            
            logger.info(f"Retrieved {len(similar_docs)} relevant chunks")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Failed to retrieve relevant documents: {e}")
            return []
    
    def _prepare_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Prepare context from retrieved chunks"""
        try:
            context_parts = []
            current_length = 0
            
            for chunk in chunks:
                chunk_text = f"Document {chunk['document_id']}, Chunk {chunk['chunk_id']}:\n{chunk['content']}\n\n"
                
                # Check if adding this chunk would exceed max context length
                if current_length + len(chunk_text) > self.max_context_length:
                    break
                
                context_parts.append(chunk_text)
                current_length += len(chunk_text)
            
            context = "".join(context_parts)
            logger.info(f"Prepared context with {len(context)} characters")
            return context
            
        except Exception as e:
            logger.error(f"Failed to prepare context: {e}")
            return ""
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using Vertex AI"""
        try:
            answer = vertex_ai_service.generate_rag_response(question, context)
            logger.info(f"Generated answer with {len(answer)} characters")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return "I apologize, but I encountered an error while generating the answer. Please try again."
    
    def _calculate_confidence(
        self, 
        chunks: List[Dict[str, Any]], 
        answer: str
    ) -> float:
        """Calculate confidence score for the answer"""
        try:
            if not chunks:
                return 0.0
            
            # Calculate average similarity score
            similarities = [chunk.get("similarity", 0.0) for chunk in chunks]
            avg_similarity = sum(similarities) / len(similarities)
            
            # Factor in answer length (longer answers might be more comprehensive)
            length_factor = min(len(answer) / 500, 1.0)  # Normalize to 0-1
            
            # Combine similarity and length factors
            confidence = (avg_similarity * 0.8) + (length_factor * 0.2)
            
            return min(confidence, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence: {e}")
            return 0.5  # Default confidence
    
    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for response"""
        try:
            sources = []
            for chunk in chunks:
                source = {
                    "document_id": chunk.get("document_id"),
                    "chunk_id": chunk.get("chunk_id"),
                    "content": chunk.get("content", "")[:200] + "...",  # Truncate for display
                    "similarity": chunk.get("similarity", 0.0),
                    "metadata": chunk.get("metadata", {})
                }
                sources.append(source)
            
            return sources
            
        except Exception as e:
            logger.error(f"Failed to format sources: {e}")
            return []
    
    def _log_query(
        self, 
        user_id: int, 
        question: str, 
        answer: str, 
        chunks: List[Dict[str, Any]], 
        response_time: float, 
        db: Session
    ) -> int:
        """Log the query for analytics and debugging"""
        try:
            query_log = QueryLog(
                user_id=user_id,
                query=question,
                response=answer,
                response_time_ms=response_time,
                document_ids=[chunk.get("document_id") for chunk in chunks]
            )
            
            db.add(query_log)
            db.commit()
            db.refresh(query_log)
            
            logger.info(f"Query logged with ID: {query_log.id}")
            return query_log.id
            
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
            db.rollback()
            return None
    
    def get_query_history(self, user_id: int, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's query history"""
        try:
            queries = db.query(QueryLog).filter(
                QueryLog.user_id == user_id
            ).order_by(QueryLog.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": query.id,
                    "query": query.query,
                    "response": query.response,
                    "response_time_ms": query.response_time_ms,
                    "created_at": query.created_at,
                    "document_ids": query.document_ids
                }
                for query in queries
            ]
            
        except Exception as e:
            logger.error(f"Failed to get query history: {e}")
            return []
    
    def search_documents(
        self, 
        query: str, 
        user_id: int, 
        db: Session,
        document_ids: Optional[List[int]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents without generating an answer"""
        try:
            chunks = self._retrieve_relevant_documents(
                query, user_id, db, document_ids, limit
            )
            
            return self._format_sources(chunks)
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []


# Global instance
rag_service = RAGService()
