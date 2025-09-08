"""
Google Document AI service for intelligent document processing
"""
import os
import logging
from typing import List, Dict, Any, Optional
from google.cloud import documentai
from google.cloud.documentai_v1 import DocumentProcessorServiceClient
from google.cloud.documentai_v1.types import ProcessRequest, RawDocument
from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentAIService:
    """Google Document AI service for document processing"""
    
    def __init__(self):
        self.client = DocumentProcessorServiceClient()
        self.project_id = settings.gcp_project_id
        self.location = settings.document_ai_location
        self.processor_id = settings.document_ai_processor_id
        self.processor_name = f"projects/{self.project_id}/locations/{self.location}/processors/{self.processor_id}"
    
    def process_document(self, file_data: bytes, mime_type: str = "application/pdf") -> Dict[str, Any]:
        """Process document using Document AI"""
        try:
            # Create raw document
            raw_document = RawDocument(
                content=file_data,
                mime_type=mime_type
            )
            
            # Create process request
            request = ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            # Process document
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract text and entities
            extracted_data = self._extract_document_data(document)
            
            logger.info(f"Document processed successfully: {len(extracted_data.get('text', ''))} characters")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Failed to process document with Document AI: {e}")
            raise
    
    def _extract_document_data(self, document) -> Dict[str, Any]:
        """Extract data from processed document"""
        try:
            # Extract text
            text = document.text
            
            # Extract entities (if any)
            entities = []
            for entity in document.entities:
                entity_data = {
                    "type": entity.type_,
                    "mention_text": entity.mention_text,
                    "confidence": entity.confidence,
                    "page_anchor": entity.page_anchor.page_refs[0].page if entity.page_anchor.page_refs else None
                }
                entities.append(entity_data)
            
            # Extract pages
            pages = []
            for page in document.pages:
                page_data = {
                    "page_number": page.page_number,
                    "dimension": {
                        "width": page.dimension.width,
                        "height": page.dimension.height
                    },
                    "text": page.text if hasattr(page, 'text') else ""
                }
                pages.append(page_data)
            
            return {
                "text": text,
                "entities": entities,
                "pages": pages,
                "confidence": document.confidence if hasattr(document, 'confidence') else 0.0
            }
            
        except Exception as e:
            logger.error(f"Failed to extract document data: {e}")
            raise
    
    def extract_text_from_pdf(self, file_data: bytes) -> str:
        """Extract text from PDF using Document AI"""
        try:
            result = self.process_document(file_data, "application/pdf")
            return result.get("text", "")
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise
    
    def extract_entities(self, file_data: bytes) -> List[Dict[str, Any]]:
        """Extract entities from document"""
        try:
            result = self.process_document(file_data)
            return result.get("entities", [])
            
        except Exception as e:
            logger.error(f"Failed to extract entities: {e}")
            raise


# Global instance
document_ai_service = DocumentAIService()
