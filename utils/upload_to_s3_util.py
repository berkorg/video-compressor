import os

from dotenv import load_dotenv
from datetime import datetime, timedelta


# Load environment variables from .env file
load_dotenv()

# AWS S3 configuration
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")


def upload_to_s3(file_path, object_name, s3_client):
    print("uploading to s3", BUCKET_NAME, AWS_REGION, object_name)
    try:
        # Define expiration time (1 hour from now)
        expiration_time = datetime.now() + timedelta(minutes=1)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=object_name,
            Body=open(file_path, "rb"),
            Expires=expiration_time,
        )
        return f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{object_name}"
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return None
