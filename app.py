import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-demo-secret")

BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024

s3 = boto3.client("s3", region_name=AWS_REGION)

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_images():
    if not BUCKET_NAME:
        return []
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="uploads/")
        images = []
        for item in response.get("Contents", []):
            key = item["Key"]
            if key.endswith("/"):
                continue
            image_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": key},
                ExpiresIn=3600,
            )
            images.append({"key": key, "url": image_url})
        return sorted(images, key=lambda image: image["key"], reverse=True)
    except ClientError:
        app.logger.exception("Could not list images from S3")
        return []

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", images=get_images())

@app.route("/upload", methods=["POST"])
def upload():
    if not BUCKET_NAME:
        flash("S3 bucket is not configured.", "error")
        return redirect(url_for("index"))

    file = request.files.get("image")
    if not file or not file.filename:
        flash("Please choose an image first.", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Allowed formats: JPG, JPEG, PNG, GIF, WEBP.", "error")
        return redirect(url_for("index"))

    safe_name = secure_filename(file.filename)
    key = f"uploads/{uuid.uuid4().hex}_{safe_name}"

    try:
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": file.mimetype or "application/octet-stream"},
        )
        flash("Image uploaded successfully!", "success")
    except ClientError:
        app.logger.exception("S3 image upload failed")
        flash("Upload failed. Check the EC2 IAM role and S3 permissions.", "error")

    return redirect(url_for("index"))

@app.route("/delete", methods=["POST"])
def delete():
    key = request.form.get("key", "")
    if not BUCKET_NAME or not key.startswith("uploads/"):
        flash("Invalid image selection.", "error")
        return redirect(url_for("index"))
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=key)
        flash("Image deleted successfully.", "success")
    except ClientError:
        app.logger.exception("S3 image delete failed")
        flash("Could not delete the image.", "error")
    return redirect(url_for("index"))

@app.errorhandler(413)
def too_large(_error):
    flash("Image is too large. Maximum size is 10 MB.", "error")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
