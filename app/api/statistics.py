"""
Statistics API routes for data visualization
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.document import Document, DocumentChunk, QueryLog, DocumentStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/documents")
async def get_document_statistics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get document processing statistics"""
    try:
        # Build base query
        query = db.query(Document).filter(Document.user_id == current_user.id)
        
        # Apply date filters
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(Document.created_at >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(Document.created_at < end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Get total documents
        total_documents = query.count()
        
        # Get status distribution
        status_counts = db.query(
            Document.status,
            func.count(Document.id).label('count')
        ).filter(
            Document.user_id == current_user.id
        )
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            status_counts = status_counts.filter(Document.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            status_counts = status_counts.filter(Document.created_at < end_dt)
        
        status_counts = status_counts.group_by(Document.status).all()
        
        # Format status distribution
        status_distribution = {
            "uploaded": 0,
            "processing": 0,
            "processed": 0,
            "failed": 0
        }
        
        for status, count in status_counts:
            status_distribution[status] = count
        
        # Get documents over time (daily counts for last 30 days or date range)
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Documents per day
        daily_docs = db.query(
            func.date(Document.created_at).label('date'),
            func.count(Document.id).label('count')
        ).filter(
            Document.user_id == current_user.id,
            Document.created_at >= datetime.strptime(start_date, "%Y-%m-%d"),
            Document.created_at < datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        ).group_by(
            func.date(Document.created_at)
        ).order_by(
            func.date(Document.created_at)
        ).all()
        
        documents_over_time = [
            {"date": str(date), "count": count}
            for date, count in daily_docs
        ]
        
        # Get average file size
        avg_size = db.query(
            func.avg(Document.file_size)
        ).filter(
            Document.user_id == current_user.id
        ).scalar() or 0
        
        # Get total chunks
        total_chunks = db.query(func.count(DocumentChunk.id)).join(
            Document
        ).filter(
            Document.user_id == current_user.id
        ).scalar() or 0
        
        logger.info(f"Document statistics retrieved for user {current_user.id}")
        
        return {
            "total_documents": total_documents,
            "status_distribution": status_distribution,
            "documents_over_time": documents_over_time,
            "average_file_size_bytes": round(avg_size, 2),
            "total_chunks": total_chunks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document statistics"
        )


@router.get("/queries")
async def get_query_statistics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get query response statistics"""
    try:
        # Build base query
        query = db.query(QueryLog).filter(QueryLog.user_id == current_user.id)
        
        # Apply date filters
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(QueryLog.created_at >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(QueryLog.created_at < end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Get total queries
        total_queries = query.count()
        
        if total_queries == 0:
            return {
                "total_queries": 0,
                "average_response_time_ms": 0,
                "min_response_time_ms": 0,
                "max_response_time_ms": 0,
                "queries_over_time": []
            }
        
        # Get response time statistics
        response_time_stats = db.query(
            func.avg(QueryLog.response_time_ms).label('avg'),
            func.min(QueryLog.response_time_ms).label('min'),
            func.max(QueryLog.response_time_ms).label('max')
        ).filter(
            QueryLog.user_id == current_user.id,
            QueryLog.response_time_ms.isnot(None)
        )
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            response_time_stats = response_time_stats.filter(QueryLog.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            response_time_stats = response_time_stats.filter(QueryLog.created_at < end_dt)
        
        stats = response_time_stats.first()
        
        # Get queries over time (daily counts)
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        daily_queries = db.query(
            func.date(QueryLog.created_at).label('date'),
            func.count(QueryLog.id).label('count'),
            func.avg(QueryLog.response_time_ms).label('avg_response_time')
        ).filter(
            QueryLog.user_id == current_user.id,
            QueryLog.created_at >= datetime.strptime(start_date, "%Y-%m-%d"),
            QueryLog.created_at < datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        ).group_by(
            func.date(QueryLog.created_at)
        ).order_by(
            func.date(QueryLog.created_at)
        ).all()
        
        queries_over_time = [
            {
                "date": str(date),
                "count": count,
                "avg_response_time_ms": round(avg_time, 2) if avg_time else 0
            }
            for date, count, avg_time in daily_queries
        ]
        
        logger.info(f"Query statistics retrieved for user {current_user.id}")
        
        return {
            "total_queries": total_queries,
            "average_response_time_ms": round(stats.avg, 2) if stats.avg else 0,
            "min_response_time_ms": round(stats.min, 2) if stats.min else 0,
            "max_response_time_ms": round(stats.max, 2) if stats.max else 0,
            "queries_over_time": queries_over_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve query statistics"
        )


@router.get("/dashboard")
async def get_dashboard_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get overall dashboard statistics"""
    try:
        # Get document stats
        total_documents = db.query(func.count(Document.id)).filter(
            Document.user_id == current_user.id
        ).scalar() or 0
        
        processed_documents = db.query(func.count(Document.id)).filter(
            Document.user_id == current_user.id,
            Document.status == DocumentStatus.PROCESSED
        ).scalar() or 0
        
        failed_documents = db.query(func.count(Document.id)).filter(
            Document.user_id == current_user.id,
            Document.status == DocumentStatus.FAILED
        ).scalar() or 0
        
        # Get query stats
        total_queries = db.query(func.count(QueryLog.id)).filter(
            QueryLog.user_id == current_user.id
        ).scalar() or 0
        
        avg_response_time = db.query(
            func.avg(QueryLog.response_time_ms)
        ).filter(
            QueryLog.user_id == current_user.id,
            QueryLog.response_time_ms.isnot(None)
        ).scalar() or 0
        
        # Get recent activity (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        recent_documents = db.query(func.count(Document.id)).filter(
            Document.user_id == current_user.id,
            Document.created_at >= seven_days_ago
        ).scalar() or 0
        
        recent_queries = db.query(func.count(QueryLog.id)).filter(
            QueryLog.user_id == current_user.id,
            QueryLog.created_at >= seven_days_ago
        ).scalar() or 0
        
        logger.info(f"Dashboard statistics retrieved for user {current_user.id}")
        
        return {
            "total_documents": total_documents,
            "processed_documents": processed_documents,
            "failed_documents": failed_documents,
            "total_queries": total_queries,
            "average_response_time_ms": round(avg_response_time, 2),
            "recent_documents_7d": recent_documents,
            "recent_queries_7d": recent_queries
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )
