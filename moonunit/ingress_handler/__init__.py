"""
moonunit.ingress_handler
~~~~~~~~~~~~~~~~~~~~~
Moon Unit Ingress API Handler Lambda
"""

import json
import logging
import os
from random import choices
from string import ascii_uppercase

import falcon
from boto3 import client
from falcon import HTTP_201, HTTPInternalServerError
from falcon_multipart.middleware import MultipartMiddleware

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ImageResource:

    def on_post(self, req, resp):
        logger.info('Lambda function invoked')

        region_name = os.environ.get('AWS_REGION')
        bucket_name = os.getenv('SOURCE_BUCKET_NAME')

        try:
            response = client('s3', region_name=region_name).put_object(
                Bucket=bucket_name,
                Key=req.get_param('image').filename,
                Body=req.get_param('image').file,
                ContentType='application/jpeg'
            )
        except BaseException as e:
            logger.exception(e)
            raise HTTPInternalServerError("Error storing response")

        resp.status = HTTP_201
        resp.media = json.dumps({"s3_put_response": response})




app = falcon.API(middleware=[MultipartMiddleware()])
app.add_route('/images', ImageResource())
