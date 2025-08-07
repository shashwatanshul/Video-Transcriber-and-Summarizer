import boto3
import os
from botocore.exceptions import NoCredentialsError, ClientError
import config

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        self.bucket_name = config.S3_BUCKET_NAME
    
    def upload_video(self, file_path, filename):
        """Upload video file to S3"""
        try:
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                f"videos/{filename}",
                ExtraArgs={'ContentType': 'video/mp4'}
            )
            s3_url = f"https://{self.bucket_name}.s3.{config.AWS_REGION}.amazonaws.com/videos/{filename}"
            return s3_url
        except NoCredentialsError:
            raise Exception("AWS credentials not found")
        except ClientError as e:
            raise Exception(f"Error uploading to S3: {e}")
    
    def get_video_url(self, filename):
        """Get presigned URL for video streaming"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': f"videos/{filename}"},
                ExpiresIn=3600  # 1 hour
            )
            return url
        except Exception as e:
            raise Exception(f"Error generating presigned URL: {e}")
    
    def delete_video(self, filename):
        """Delete video from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=f"videos/{filename}"
            )
            return True
        except Exception as e:
            raise Exception(f"Error deleting from S3: {e}")
    
    def check_bucket_exists(self):
        """Check if S3 bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False 