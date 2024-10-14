from werkzeug.utils import secure_filename
import os
import subprocess
import uuid

from utils.upload_to_s3_util import upload_to_s3

ALLOWED_EXTENSIONS = {
    "gif",
    "mp4",
    "mov",
    "avi",
}  # Add video extensions


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_video(input_path, output_path, quality, scale):
    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        input_path,
        "-vf",
        f"scale={scale}:-2",
        "-c:v",
        "libx264",
        "-crf",
        str(quality),
        "-preset",
        "medium",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        output_path,
    ]
    subprocess.run(ffmpeg_cmd, check=True)


def compress_video_util(file, quality, scale, app, s3_client):
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        random_filename = f"{uuid.uuid4()}{file_extension}"
        input_path = os.path.join(app.config["UPLOAD_FOLDER"], random_filename)
        output_filename = f"compressed_{uuid.uuid4()}.mp4"
        output_path = os.path.join(app.config["COMPRESSED_FOLDER"], output_filename)

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        os.makedirs(app.config["COMPRESSED_FOLDER"], exist_ok=True)

        file.save(input_path)

        try:
            compress_video(input_path, output_path, quality, scale)

            # Upload the compressed file to S3
            s3_url = upload_to_s3(output_path, output_filename, s3_client)

            if s3_url:
                return {"success": True, "s3_url": s3_url}
            else:
                return {"error": "Failed to upload to S3"}
        except subprocess.CalledProcessError:
            return {"error": "Compression failed"}
        finally:
            # Clean up local files
            os.remove(input_path)
            os.remove(output_path)
