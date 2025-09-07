"""
Google Cloud Storage service for file management
"""
import os
import logging
from typing import Optional, BinaryIO
from google.cloud import storage
from google.cloud.exceptions import NotFound
from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudStorageService:
    """Google Cloud Storage service for file operations"""
    
    def __init__(self):
        self.client = storage.Client(project=settings.gcp_project_id)
        self.bucket_name = settings.cloud_storage_bucket
        self.bucket = self.client.bucket(self.bucket_name) if self.bucket_name else None
    
    def upload_file(self, file_data: bytes, file_path: str, content_type: str = None) -> str:
        """Upload file to Cloud Storage"""
        try:
            if not self.bucket:
                raise ValueError("Cloud Storage bucket not configured")
            
            blob = self.bucket.blob(file_path)
            blob.upload_from_string(file_data, content_type=content_type)
            
            logger.info(f"File uploaded to Cloud Storage: {file_path}")
            return f"gs://{self.bucket_name}/{file_path}"
            
        except Exception as e:
            logger.error(f"Failed to upload file to Cloud Storage: {e}")
            raise
    
    def download_file(self, file_path: str) -> bytes:
        """Download file from Cloud Storage"""
        try:
            if not self.bucket:
                raise ValueError("Cloud Storage bucket not configured")
            
            blob = self.bucket.blob(file_path)
            return blob.download_as_bytes()
            
        except NotFound:
            logger.error(f"File not found in Cloud Storage: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to download file from Cloud Storage: {e}")
            raise
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from Cloud Storage"""
        try:
            if not self.bucket:
                raise ValueError("Cloud Storage bucket not configured")
            
            blob = self.bucket.blob(file_path)
            blob.delete()
            
            logger.info(f"File deleted from Cloud Storage: {file_path}")
            return True
            
        except NotFound:
            logger.warning(f"File not found in Cloud Storage: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file from Cloud Storage: {e}")
            raise
    
    def get_file_url(self, file_path: str, expiration_minutes: int = 60) -> str:
        """Get signed URL for file access"""
        try:
            if not self.bucket:
                raise ValueError("Cloud Storage bucket not configured")
            
            blob = self.bucket.blob(file_path)
            url = blob.generate_signed_url(
                expiration=expiration_minutes * 60,
                method="GET"
            )
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise
    
    def list_files(self, prefix: str = "") -> list:
        """List files in bucket with optional prefix"""
        try:
            if not self.bucket:
                raise ValueError("Cloud Storage bucket not configured")
            
            blobs = self.bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise


# Global instance
cloud_storage_service = CloudStorageService()
