# backend/django_app/core/supabase_client.py
import os
import logging
from supabase import create_client, Client
from django.conf import settings

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
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
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





# # backend/django_app/services/supabase_service.py
# import os
# import uuid
# import logging
# from supabase import create_client, Client
# from django.conf import settings
# from dotenv import load_dotenv

# load_dotenv()  # Load environment variables from .env file

# logger = logging.getLogger(__name__)

# class SupabaseStorageService:
#     """Supabase Storage service for resume uploads"""
    
#     def __init__(self):
#         self.supabase_url = os.getenv('SUPABASE_URL')
#         self.supabase_service_role_key= os.getenv('SUPABASE_SERVICE_ROLE_KEY')
#         self.bucket_name = os.getenv('SUPABASE_STORAGE_BUCKET', 'resumes')
        
#         if not self.supabase_url or not self.supabase_service_role_key:
#             raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")
        
#         # Initialize Supabase client
        
#         self.client: Client = create_client(self.supabase_url, self.supabase_service_role_key)
       
#         logger.info(f"✅ SupabaseStorageService initialized with bucket: {self.bucket_name}")
    
#     def upload_resume(self, user_id: str , file_content: bytes, file_name: str) -> dict:
#         """
#         Upload a resume to Supabase Storage
        
#         Args:
#             user_id: User UUID
#             file_content: Binary file content
#             file_name: Original file name
            
#         Returns:
#             dict: {path, url, size, file_type}
#         """
#         try:
#             # Generate unique file path
#             file_id = str(uuid.uuid4())
#             file_extension = file_name.split('.')[-1].lower()
#             file_path = f"{user_id}/{file_id}.{file_extension}"
           
            
#             logger.info(f"📤 Uploading file to Supabase: {file_path}")
            
#             # Upload to Supabase Storage
#             response = self.client.storage.from_(self.bucket_name).upload(
#                 path=file_path,
#                 file=file_content,
#                 file_options={
#                     "content-type": f"application/{file_extension}" if file_extension in ['pdf', 'docx'] else "application/octet-stream",
#                     "cache-control": "3600"
#                 }
#             )
            
#             if hasattr(response, 'error') and response.error:
#                 raise Exception(f"Upload failed: {response.error}")
            
#             # Get public URL
#             public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            
#             logger.info(f"✅ File uploaded successfully: {public_url}")
            
#             return {
#                 'path': file_path,
#                 'url': public_url,
#                 'size': len(file_content),
#                 'file_type': file_extension,
#                 'name': file_name
#             }
            
#         except Exception as e:
#             logger.error(f"❌ Supabase upload error: {str(e)}")
#             raise
    
#     def delete_resume(self, file_path: str, access_token: str) -> bool:
#         """
#         Delete a resume from Supabase Storage
        
#         Args:
#             file_path: Path to the file in storage
            
#         Returns:
#             bool: True if deleted successfully
#         """
#         try:
#             logger.info(f"🗑️ Deleting file from Supabase: {file_path}")

#             response = self.client.storage.from_(self.bucket_name).remove([file_path])
            
#             if hasattr(response, 'error') and response.error:
#                 raise Exception(f"Delete failed: {response.error}")
            
#             logger.info(f"✅ File deleted successfully: {file_path}")
#             return True
            
#         except Exception as e:
#             logger.error(f"❌ Supabase delete error: {str(e)}")
#             return False
        
#     def update_resume(self,file_path:str,new_file_content:bytes,content_type:str) -> dict:
#         try:
#             response= self.storage.form_(self.bucket_name).upload(
#                 path=file_path,
#                 file=new_file_content,
#                 file_options={
#                     "content-type": content_type,
#                     "cache-control": "3600"
#                 },
#                 upsert=True  # Overwrite existing file
#             )

#             if hasattr(response, 'error') and response.error:
#                 raise Exception(f"Update failed: {response.error}")
#             return True
#         except Exception as e:
#             logger.error(f"❌ Supabase update error: {str(e)}")
#             return False
    
         
            
           
    
#     def get_signed_url(self, file_path: str, expires_in: int = 3600) -> str:
#         """
#         Get a signed URL for a private file
        
#         Args:
#             file_path: Path to the file
#             expires_in: Expiry time in seconds
            
#         Returns:
#             str: Signed URL
#         """
#         try:
#             response = self.client.storage.from_(self.bucket_name).create_signed_url(
#                 file_path, expires_in
#             )
            
#             if hasattr(response, 'error') and response.error:
#                 raise Exception(f"Failed to get signed URL: {response.error}")
            
#             return response.get('signedURL', '') if isinstance(response, dict) else str(response)
            
#         except Exception as e:
#             logger.error(f"❌ Supabase signed URL error: {str(e)}")
#             return ""


# # Singleton instance
# supabase_storage = SupabaseStorageService()