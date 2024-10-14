import boto3
import os
from botocore.exceptions import ClientError

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")


def remove_file_from_s3(file_key):
    """
    Remove a file from an S3 bucket.

    :param bucket_name: String name of the S3 bucket
    :param file_key: String key (path) of the file in the S3 bucket
    :return: True if file was removed successfully, False otherwise
    """

    s3_client = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=file_key)
        print(f"File {file_key} was removed from bucket {BUCKET_NAME}")
        return True
    except ClientError as e:
        print(f"Error removing file {file_key} from bucket {BUCKET_NAME}: {e}")
        return False
