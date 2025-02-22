from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
import json
from weather_client.client import OpenMeteoClient

_LOG = get_logger(__name__)


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        method = event['requestContext']['http']['method']
        path = event['requestContext']['http']['path']
        if method != "GET" or path != "/weather":
            bad_response = {
                "statusCode": 400,
                "message": f"Bad request syntax or unsupported method. Request path: {path}. HTTP method: {method}"
            }
            return json.dumps(bad_response)
        else:
            client = OpenMeteoClient()
            weather_data = client.get_weather_forecast()
            return weather_data    
    
HANDLER = ApiHandler()

def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
