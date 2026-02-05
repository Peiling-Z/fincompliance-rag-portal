"""
Document models and schemas
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Document(Base):
    """Document model"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(String(20), default=DocumentStatus.UPLOADED)
    doc_metadata = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Document chunk model"""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column(JSON, nullable=True)
    embedding_id = Column(String(100), nullable=True)  # Vector DB ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class QueryLog(Base):
    """Query log model"""
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    document_ids = Column(JSON, nullable=True)  # List of document IDs used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")


# Pydantic schemas
class DocumentUpload(BaseModel):
    """Document upload schema"""
    filename: str
    file_type: str
    file_size: int
    doc_metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Document response schema"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    status: DocumentStatus
    doc_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    processed_at: Optional[datetime]
    chunk_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    """Document chunk response schema"""
    id: int
    chunk_index: int
    content: str
    chunk_metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    """Query request schema"""
    question: str
    document_ids: Optional[List[int]] = None
    max_results: int = 5


class QueryResponse(BaseModel):
    """Query response schema"""
    answer: str
    sources: List[DocumentChunkResponse]
    confidence: float
    response_time_ms: float
    query_id: int


class DocumentSearchRequest(BaseModel):
    """Document search request schema"""
    query: str
    document_ids: Optional[List[int]] = None
    limit: int = 10