"""
Amazon S3 Service for KisaanAI.

Handles image uploads for crop disease detection and other media storage.
"""
import boto3
from botocore.exceptions import ClientError
import logging
from datetime import datetime
import uuid
from typing import Optional, Dict
from app.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """
    Amazon S3 service for file storage.
    
    Usage:
        s3 = S3Service()
        result = await s3.upload_image(file_data, "crop.jpg")
        url = await s3.get_image_url(result['key'])
    """
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = None,
        bucket_name: Optional[str] = None
    ):
        self.aws_access_key_id = aws_access_key_id or settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.AWS_SECRET_ACCESS_KEY
        self.aws_region = aws_region or settings.AWS_REGION
        self.bucket = bucket_name or getattr(settings, 'AWS_S3_BUCKET', 'kisaanai-uploads')
        self._client = None
    
    @property
    def client(self):
        """Lazy-initialize S3 client."""
        if self._client is None:
            self._client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
        return self._client
    
    def is_configured(self) -> bool:
        """Check if AWS credentials are available."""
        return bool(self.aws_access_key_id and self.aws_secret_access_key)
    
    async def upload_image(
        self, 
        file_data: bytes, 
        filename: str,
        content_type: str = 'image/jpeg'
    ) -> Dict:
        """
        Upload image to S3.
        
        Args:
            file_data: Image bytes
            filename: Original filename
            content_type: MIME type
            
        Returns:
            Dict with success, key, and url
        """
        if not self.is_configured():
            logger.warning("AWS credentials not configured for S3")
            return {'success': False, 'error': 'S3 not configured'}
        
        try:
            # Generate unique key with date-based folder structure
            date_path = datetime.now().strftime('%Y/%m/%d')
            unique_id = str(uuid.uuid4())
            key = f"crops/{date_path}/{unique_id}_{filename}"
            
            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                Metadata={
                    'uploaded_at': datetime.now().isoformat(),
                    'original_filename': filename
                }
            )
            
            # Generate presigned URL (valid for 1 hour)
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=3600
            )
            
            logger.info(f"Uploaded image to S3: {key}")
            return {
                'success': True,
                'key': key,
                'url': url,
                'bucket': self.bucket
            }
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_image_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get presigned URL for an image.
        
        Args:
            key: S3 object key
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL or None
        """
        if not self.is_configured():
            logger.warning("AWS credentials not configured for S3")
            return None
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"S3 get URL error: {e}")
            return None
    
    async def delete_image(self, key: str) -> bool:
        """
        Delete an image from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.warning("AWS credentials not configured for S3")
            return False
        
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted image from S3: {key}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
    
    async def list_images(self, prefix: str = 'crops/', max_keys: int = 100) -> list:
        """
        List images in S3.
        
        Args:
            prefix: Key prefix to filter
            max_keys: Maximum number of keys to return
            
        Returns:
            List of object keys
        """
        if not self.is_configured():
            logger.warning("AWS credentials not configured for S3")
            return []
        
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
            
        except ClientError as e:
            logger.error(f"S3 list error: {e}")
            return []


# Singleton instance
s3_service = S3Service()
