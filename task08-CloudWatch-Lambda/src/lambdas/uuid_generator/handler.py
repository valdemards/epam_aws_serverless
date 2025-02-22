from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
import json
import uuid
import os
from datetime import datetime
import boto3

_LOG = get_logger(__name__)


class UuidGenerator(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        s3 = boto3.client('s3')
        ids = [str(uuid.uuid4()) for _ in range(10)]
        file_name = datetime.utcnow().isoformat()
        s3.put_object(Bucket=os.environ.get('target_bucket'), Key=file_name, Body=json.dumps({'ids': ids}))
        return {
            "statusCode": 200,
            "file_name": file_name
        }    

HANDLER = UuidGenerator()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
