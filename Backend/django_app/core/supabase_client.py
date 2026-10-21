# backend/django_app/core/supabase_client.py
import os
import logging
from supabase import create_client, Client
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Singleton Supabase client for file storage operations.
    """
    _instance = None
    _client: Client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._client = create_client(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            )
            logger.info("Supabase client initialized successfully")
        return cls._instance

    def get_client(self) -> Client:
        """Get the Supabase client instance"""
        return self._client

    def upload_file(self, bucket_name: str, file_path: str, file_content: bytes, 
                    content_type: str = 'application/pdf') -> dict:
        """
        Upload a file to Supabase storage.
        
        Args:
            bucket_name: Storage bucket name (e.g., 'resumes')
            file_path: Path where file will be stored (e.g., 'user_123/resume.pdf')
            file_content: Binary file content
            content_type: MIME type of the file
        
        Returns:
            dict: {'public_url': str, 'path': str, 'bucket': str}
        """
        try:
            # Upload file to Supabase storage
            response = self._client.storage.from_(bucket_name).upload(
                file_path,
                file_content,
                file_options={"content-type": content_type}
            )
            
            # Get public URL
            public_url = self._client.storage.from_(bucket_name).get_public_url(file_path)
            
            logger.info(f"File uploaded successfully to Supabase: {file_path}")
            
            return {
                'public_url': public_url,
                'path': file_path,
                'bucket': bucket_name,
                'response': response
            }
        except Exception as e:
            logger.error(f"Failed to upload file to Supabase: {str(e)}")
            raise

    def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """
        Delete a file from Supabase storage.
        
        Args:
            bucket_name: Storage bucket name
            file_path: Path of the file to delete
        
        Returns:
            bool: True if deleted successfully
        """
        try:
            self._client.storage.from_(bucket_name).remove([file_path])
            logger.info(f"File deleted from Supabase: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Supabase: {str(e)}")
            return False

    def download_file(self, bucket_name: str, file_path: str) -> bytes:
        """
        Download a file from Supabase storage.
        
        Args:
            bucket_name: Storage bucket name
            file_path: Path of the file to download
        
        Returns:
            bytes: File content
        """
        try:
            response = self._client.storage.from_(bucket_name).download(file_path)
            logger.info(f"File downloaded from Supabase: {file_path}")
            return response
        except Exception as e:
            logger.error(f"Failed to download file from Supabase: {str(e)}")
            raise

    def get_file_url(self, bucket_name: str, file_path: str) -> str:
        """
        Get the public URL of a file in Supabase storage.
        
        Args:
            bucket_name: Storage bucket name
            file_path: Path of the file
        
        Returns:
            str: Public URL
        """
        return self._client.storage.from_(bucket_name).get_public_url(file_path)

    def list_files(self, bucket_name: str, folder_path: str = "") -> list:
        """
        List files in a Supabase storage bucket.
        
        Args:
            bucket_name: Storage bucket name
            folder_path: Folder path to list (optional)
        
        Returns:
            list: List of file objects
        """
        try:
            response = self._client.storage.from_(bucket_name).list(folder_path)
            return response
        except Exception as e:
            logger.error(f"Failed to list files from Supabase: {str(e)}")
            return []

    def create_bucket(self, bucket_name: str, public: bool = True) -> bool:
        """
        Create a storage bucket in Supabase.
        
        Args:
            bucket_name: Name of the bucket to create
            public: Whether the bucket should be public
        
        Returns:
            bool: True if created successfully
        """
        try:
            self._client.storage.create_bucket(
                bucket_name,
                {"public": public}
            )
            logger.info(f"Bucket created: {bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create bucket: {str(e)}")
            return False


# Singleton instance
supabase_client = SupabaseClient()




