import os
import boto3
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS

from utils import compress_image_util, compress_video_util

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Add this line to enable CORS for all routes

UPLOAD_FOLDER = "uploads"
COMPRESSED_FOLDER = "compressed"


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["COMPRESSED_FOLDER"] = COMPRESSED_FOLDER

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


@app.route("/compress", methods=["POST"])
def compress():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    quality = int(request.form.get("quality", 1))  # Default to highest quality
    scale = int(request.form.get("scale", 1200))  # Default to 1200 if not provided

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    result = compress_image_util.compress_image_util(
        file, app, quality, scale, s3_client
    )
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 500


@app.route("/compress_video", methods=["POST"])
def compress_video_endpoint():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    quality = int(request.form.get("quality", 23))  # Default to medium quality (CRF 23)
    scale = int(request.form.get("scale", 1280))  # Default to 720p width

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    result = compress_video_util.compress_video_util(
        file, quality, scale, app, s3_client
    )
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 500


if __name__ == "__main__":
    app.run(debug=True)
