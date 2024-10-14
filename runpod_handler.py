import runpod
from flask import Flask
import os
from dotenv import load_dotenv
import boto3

from utils import compress_image_util, compress_video_util
from utils.save_file_from_url import save_file_from_url

# Create a FileStorage object with the file
from werkzeug.datastructures import FileStorage

from botocore.exceptions import NoCredentialsError

from utils.s3_settings import get_s3_settings
from utils.s3_utils import s3utils

# Load environment variables from .env file
load_dotenv()

is_gpu_available = os.environ.get("GPU_AVAILABLE")

# AWS S3 configuration
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "uploads"
app.config["COMPRESSED_FOLDER"] = "compressed"


def handler(job):
    job_input = job["input"]

    """Handler function that will be used to process jobs."""
    job_type = job_input.get("job_type", None)

    if job_type == None:
        return {"error": "You need to specify job_type"}

    # generate pre-signed URL
    if job_type == "generate-presigned-url":
        file_name = job_input.get("file_name", None)
        file_type = job_input.get("file_type", None)
        bucket_name = get_s3_settings()["aws_bucket_name"]

        s3utils_instance = s3utils(get_s3_settings())

        try:
            presigned_url = s3utils_instance.get_client().generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": bucket_name,
                    "Key": file_name,
                    "ContentType": file_type,
                },
                ExpiresIn=3600,
            )
            return {"url": presigned_url}
        except NoCredentialsError:
            return {"error": "S3 credentials not available"}
    if job_type == "image_compress":
        file_url = job_input.get("file_url", None)
        quality = job_input.get("quality", 1)
        scale = job_input.get("scale", 1200)

        input_image_path = save_file_from_url(file_url, "input_image")

        with open(input_image_path, "rb") as file:
            file_storage = FileStorage(
                file, filename=os.path.basename(input_image_path)
            )

            result = compress_image_util.compress_image_util(
                file_storage, app, quality, scale, s3_client
            )

            os.remove(input_image_path)
            return result

    if job_type == "video_compress":
        file_url = job_input.get("file_url", None)
        quality = job_input.get("quality", 23)
        scale = job_input.get("scale", 1280)

        input_video_path = save_file_from_url(file_url, "input_video")

        with open(input_video_path, "rb") as file:
            file_storage = FileStorage(
                file, filename=os.path.basename(input_video_path)
            )

            result = compress_video_util.compress_video_util(
                file_storage, app, quality, scale, s3_client
            )

            os.remove(input_video_path)
            return result

    else:
        return {
            "error": "job_type should be one of 'generate-presigned-url' , 'image_compress', 'video_compress' "
        }


runpod.serverless.start({"handler": handler})
