# AWS Cloud Image Gallery

A Flask-based image gallery hosted on Amazon EC2. Images are stored privately in Amazon S3 and displayed using temporary pre-signed URLs.

## Architecture
Browser → Flask application on Amazon EC2 → Private Amazon S3 bucket

## Features
- Upload JPG, JPEG, PNG, GIF and WEBP images
- Store images in an S3 `uploads/` folder
- Display images from a private S3 bucket using pre-signed URLs
- Delete uploaded images
- 10 MB upload limit

## Requirements
- Python 3
- An AWS S3 bucket
- An EC2 instance with an IAM role that permits `s3:ListBucket`, `s3:PutObject`, `s3:GetObject` and `s3:DeleteObject` for the project bucket

## Configuration
Set these environment variables on the EC2 instance:

```bash
export S3_BUCKET_NAME=your-s3-bucket-name
export AWS_REGION=ap-southeast-2
export FLASK_SECRET_KEY='replace-with-a-long-random-secret'
```

Use an EC2 IAM role for AWS permissions. Do not put AWS access keys in this project.

## Run
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 app:app
```

Configure the EC2 security group to allow the required web traffic. For a real production deployment, use HTTPS, a production web-server setup, and suitable access controls.

## Security
- Keep the S3 bucket private.
- Never commit AWS credentials, `.env` files, private keys, or the Python virtual environment.
- Change the demo Flask secret key before production use.
