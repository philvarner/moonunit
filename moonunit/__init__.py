import io
import os

import boto3
from PIL import Image

region_name = os.environ.get('AWS_REGION')
s3 = boto3.client('s3', region_name=region_name)


def rotate_image(event, _context):
    src_bucket = event['Records'][0]['s3']['bucket']['name']
    src_key = event['Records'][0]['s3']['object']['key']
    print(f"bucket: '{src_bucket}' key: '{src_key}'")

    s3_object = s3.get_object(Bucket=src_bucket, Key=src_key)

    try:
        with Image.open(s3_object['Body']) as image:
            handle_jpeg(src_key, image)
    except OSError:  # thrown by Image for non-images
        print("invalid image")


def handle_jpeg(src_key, src_img):
    assets_key = f"{src_key[:src_key.rindex('.')]}_rot13.jpg"

    bytes_io = io.BytesIO()
    src_img.rotate(13, expand=True).save(bytes_io, "JPEG", quality=95)

    return s3.put_object(
        Bucket=assets_bucket_name(),
        Key=assets_key,
        Body=bytes_io.getvalue(),
        ContentType='image/jpeg'
    )


def assets_bucket_name():
    return os.getenv('ASSETS_BUCKET_NAME')
