from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
import json

_LOG = get_logger(__name__)


class HelloWorld(AbstractLambda):

    def validate_request(self, event) -> dict:
        _LOG.info('No validation needed')
        return
        
    def handle_request(self, event, context):
        http_method = event['requestContext']['http']['method']
        path = event['requestContext']['http']['path']

        if http_method == "GET" and path == "/hello":
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "statusCode": 200,
                    "message": "Hello from Lambda"
                })
            }
        
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "statusCode": 400,
                    "message": f"Bad request syntax or unsupported method. Request path: {path}. HTTP method: {http_method}"
                })
            }

HANDLER = HelloWorld()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
