"""
Document processing service that integrates all GCP services
"""
import os
import logging
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.cloud_storage import cloud_storage_service
from app.services.document_ai import document_ai_service
from app.services.vector_search import vector_search_service

logger = logging.getLogger(__name__)


class DocumentProcessorService:
    """Document processing service that orchestrates all GCP services"""
    
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.supported_formats = settings.supported_formats
    
    def process_document(
        self, 
        file_data: bytes, 
        filename: str, 
        user_id: int, 
        db: Session
    ) -> Dict[str, Any]:
        """Process a document through the complete pipeline"""
        try:
            # Step 1: Validate file
            file_extension = self._get_file_extension(filename)
            if not self._is_supported_format(file_extension):
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Step 2: Create document record
            document = self._create_document_record(filename, file_data, user_id, db)
            
            # Step 3: Upload to Cloud Storage
            storage_path = self._upload_to_storage(file_data, filename, document.id)
            
            # Step 4: Process with Document AI
            ai_result = self._process_with_document_ai(file_data, file_extension)
            
            # Step 5: Create document chunks
            chunks = self._create_document_chunks(document.id, ai_result, db)
            
            # Step 6: Generate embeddings
            embeddings = self._generate_embeddings(chunks)
            
            # Step 7: Update document status
            self._update_document_status(document, DocumentStatus.PROCESSED, db)
            
            logger.info(f"Document processed successfully: {filename}")
            return {
                "document_id": document.id,
                "chunks_count": len(chunks),
                "storage_path": storage_path,
                "ai_confidence": ai_result.get("confidence", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Failed to process document {filename}: {e}")
            # Update document status to failed
            if 'document' in locals():
                self._update_document_status(document, DocumentStatus.FAILED, db)
            raise
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        return Path(filename).suffix.lower().lstrip('.')
    
    def _is_supported_format(self, file_extension: str) -> bool:
        """Check if file format is supported"""
        return file_extension in self.supported_formats
    
    def _create_document_record(
        self, 
        filename: str, 
        file_data: bytes, 
        user_id: int, 
        db: Session
    ) -> Document:
        """Create document record in database"""
        try:
            # Generate file hash
            file_hash = hashlib.sha256(file_data).hexdigest()[:16]
            
            # Create document record
            document = Document(
                filename=filename,
                original_filename=filename,
                file_path="",  # Will be updated after storage
                file_size=len(file_data),
                file_type=self._get_file_extension(filename),
                status=DocumentStatus.UPLOADED,
                user_id=user_id,
                metadata={
                    "file_hash": file_hash,
                    "processing_status": "uploaded"
                }
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            logger.info(f"Document record created: {document.id}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to create document record: {e}")
            db.rollback()
            raise
    
    def _upload_to_storage(self, file_data: bytes, filename: str, document_id: int) -> str:
        """Upload file to Cloud Storage"""
        try:
            # Create storage path
            storage_path = f"documents/{document_id}/{filename}"
            
            # Upload to Cloud Storage
            storage_url = cloud_storage_service.upload_file(
                file_data=file_data,
                file_path=storage_path,
                content_type=self._get_mime_type(filename)
            )
            
            logger.info(f"File uploaded to storage: {storage_path}")
            return storage_url
            
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {e}")
            raise
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type for file"""
        file_extension = self._get_file_extension(filename)
        return document_ai_service.get_mime_type(file_extension) or "application/octet-stream"
    
    def _process_with_document_ai(self, file_data: bytes, file_extension: str) -> Dict[str, Any]:
        """Process document with Document AI"""
        try:
            # Get MIME type
            mime_type = document_ai_service.get_mime_type(file_extension)
            
            if not mime_type:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Process based on file type
            if file_extension == "csv":
                result = document_ai_service.process_csv_file(file_data)
            elif file_extension in ["png", "jpg", "jpeg", "gif", "bmp", "tiff"]:
                result = document_ai_service.process_image_file(file_data, file_extension)
            elif file_extension in ["doc", "docx", "xls", "xlsx", "ppt", "pptx"]:
                result = document_ai_service.process_office_document(file_data, file_extension)
            else:
                result = document_ai_service.process_document(file_data, mime_type)
            
            logger.info(f"Document AI processing completed: {file_extension}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process with Document AI: {e}")
            raise
    
    def _create_document_chunks(
        self, 
        document_id: int, 
        ai_result: Dict[str, Any], 
        db: Session
    ) -> List[DocumentChunk]:
        """Create document chunks from AI result"""
        try:
            text = ai_result.get("text", "")
            if not text:
                raise ValueError("No text extracted from document")
            
            # Split text into chunks
            chunks = self._split_text_into_chunks(text)
            
            # Create chunk records
            chunk_records = []
            for i, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk_text,
                    metadata={
                        "chunk_size": len(chunk_text),
                        "ai_confidence": ai_result.get("confidence", 0.0)
                    }
                )
                chunk_records.append(chunk)
                db.add(chunk)
            
            db.commit()
            
            logger.info(f"Created {len(chunk_records)} chunks for document {document_id}")
            return chunk_records
            
        except Exception as e:
            logger.error(f"Failed to create document chunks: {e}")
            db.rollback()
            raise
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        try:
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + self.chunk_size
                chunk = text[start:end]
                
                if chunk.strip():
                    chunks.append(chunk.strip())
                
                # Move start position with overlap
                start = end - self.chunk_overlap
                
                # Prevent infinite loop
                if start >= len(text):
                    break
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to split text into chunks: {e}")
            return [text]  # Return full text as single chunk
    
    def _generate_embeddings(self, chunks: List[DocumentChunk]) -> List[List[float]]:
        """Generate embeddings for document chunks"""
        try:
            # Extract text from chunks
            texts = [chunk.content for chunk in chunks]
            
            # Generate embeddings
            embeddings = vector_search_service.create_embeddings(texts)
            
            # Update chunks with embeddings
            for i, chunk in enumerate(chunks):
                if i < len(embeddings):
                    chunk.embedding_id = f"embedding_{chunk.document_id}_{chunk.chunk_index}"
                    # Store embedding in metadata for now (in production, use vector DB)
                    chunk.metadata = chunk.metadata or {}
                    chunk.metadata["embedding"] = embeddings[i]
            
            logger.info(f"Generated embeddings for {len(chunks)} chunks")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def _update_document_status(
        self, 
        document: Document, 
        status: DocumentStatus, 
        db: Session
    ) -> None:
        """Update document status"""
        try:
            document.status = status
            db.commit()
            logger.info(f"Document {document.id} status updated to {status}")
        except Exception as e:
            logger.error(f"Failed to update document status: {e}")
            db.rollback()
            raise


# Global instance
document_processor_service = DocumentProcessorService()
