"""
S3/MinIO storage service for file management.
"""

import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
from config import settings
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """Service for S3/MinIO file storage operations."""

    def __init__(self):
        """Initialize S3 client."""
        self.client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
            else:
                logger.error(f"Error checking bucket: {e}")

    def upload_file(
        self,
        file_obj: BinaryIO,
        object_key: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to S3.

        Args:
            file_obj: File object to upload
            object_key: S3 object key (path in bucket)
            content_type: Optional content type

        Returns:
            str: S3 object key

        Raises:
            ClientError: If upload fails
        """
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        try:
            self.client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_key,
                ExtraArgs=extra_args
            )
            logger.info(f"Uploaded file to {object_key}")
            return object_key
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    def download_file(self, object_key: str) -> bytes:
        """
        Download file from S3.

        Args:
            object_key: S3 object key

        Returns:
            bytes: File content

        Raises:
            ClientError: If download fails
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            raise

    def delete_file(self, object_key: str) -> bool:
        """
        Delete file from S3.

        Args:
            object_key: S3 object key

        Returns:
            bool: True if successful
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"Deleted file {object_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    def file_exists(self, object_key: str) -> bool:
        """
        Check if file exists in S3.

        Args:
            object_key: S3 object key

        Returns:
            bool: True if file exists
        """
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except ClientError:
            return False

    def generate_presigned_url(
        self,
        object_key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for file access.

        Args:
            object_key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            str: Presigned URL or None if failed
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

    @staticmethod
    def build_object_key(tenant_id: str, analysis_id: str, filename: str) -> str:
        """
        Build S3 object key with organized path structure.

        Args:
            tenant_id: Tenant UUID
            analysis_id: Analysis UUID
            filename: Original filename

        Returns:
            str: S3 object key (e.g., tenant_id/analysis_id/filename)
        """
        return f"{tenant_id}/{analysis_id}/{filename}"


# Create global instance
s3_service = S3Service()
