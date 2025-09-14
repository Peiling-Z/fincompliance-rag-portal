"""
Question and Answer API routes
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["question-answer"])


class QuestionRequest(BaseModel):
    """Request model for asking a question"""
    question: str
    document_ids: Optional[List[int]] = None
    top_k: Optional[int] = 5
    threshold: Optional[float] = 0.7


class QuestionResponse(BaseModel):
    """Response model for question answers"""
    answer: str
    sources: List[dict]
    confidence: float
    response_time_ms: float
    query_id: Optional[int]


class SearchRequest(BaseModel):
    """Request model for document search"""
    query: str
    document_ids: Optional[List[int]] = None
    limit: Optional[int] = 10


class SearchResponse(BaseModel):
    """Response model for document search"""
    results: List[dict]
    total_results: int


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Ask a question and get an AI-generated answer"""
    try:
        # Validate question
        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        # Validate parameters
        if request.top_k and (request.top_k < 1 or request.top_k > 20):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="top_k must be between 1 and 20"
            )
        
        if request.threshold and (request.threshold < 0 or request.threshold > 1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="threshold must be between 0 and 1"
            )
        
        # Ask question using RAG service
        result = rag_service.ask_question(
            question=request.question,
            user_id=current_user.id,
            db=db,
            document_ids=request.document_ids,
            top_k=request.top_k,
            threshold=request.threshold
        )
        
        logger.info(f"Question answered for user {current_user.id}: {request.question[:50]}...")
        
        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            response_time_ms=result["response_time_ms"],
            query_id=result["query_id"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to answer question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question"
        )


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search documents without generating an answer"""
    try:
        # Validate query
        if not request.query or not request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
        
        # Validate limit
        if request.limit and (request.limit < 1 or request.limit > 50):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit must be between 1 and 50"
            )
        
        # Search documents using RAG service
        results = rag_service.search_documents(
            query=request.query,
            user_id=current_user.id,
            db=db,
            document_ids=request.document_ids,
            limit=request.limit
        )
        
        logger.info(f"Document search performed for user {current_user.id}: {request.query[:50]}...")
        
        return SearchResponse(
            results=results,
            total_results=len(results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search documents"
        )


@router.get("/history", response_model=List[dict])
async def get_query_history(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's query history"""
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit must be between 1 and 100"
            )
        
        # Get query history
        history = rag_service.get_query_history(
            user_id=current_user.id,
            db=db,
            limit=limit
        )
        
        logger.info(f"Query history retrieved for user {current_user.id}")
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve query history"
        )


@router.get("/stats", response_model=dict)
async def get_qa_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get Q&A statistics for the user"""
    try:
        # Get query history
        history = rag_service.get_query_history(
            user_id=current_user.id,
            db=db,
            limit=1000  # Get more data for stats
        )
        
        if not history:
            return {
                "total_queries": 0,
                "average_response_time": 0,
                "average_confidence": 0,
                "recent_queries": []
            }
        
        # Calculate statistics
        total_queries = len(history)
        response_times = [q.get("response_time_ms", 0) for q in history if q.get("response_time_ms")]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Get recent queries (last 5)
        recent_queries = history[:5]
        
        logger.info(f"QA stats retrieved for user {current_user.id}")
        
        return {
            "total_queries": total_queries,
            "average_response_time": round(avg_response_time, 2),
            "recent_queries": recent_queries
        }
        
    except Exception as e:
        logger.error(f"Failed to get QA stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.post("/feedback", response_model=dict)
async def submit_feedback(
    query_id: int,
    rating: int,
    feedback: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for a query"""
    try:
        # Validate rating
        if rating < 1 or rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1 and 5"
            )
        
        # TODO: Implement feedback storage
        # This would involve creating a feedback table and storing the data
        
        logger.info(f"Feedback submitted for query {query_id} by user {current_user.id}: rating={rating}")
        
        return {
            "message": "Feedback submitted successfully",
            "query_id": query_id,
            "rating": rating
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )
