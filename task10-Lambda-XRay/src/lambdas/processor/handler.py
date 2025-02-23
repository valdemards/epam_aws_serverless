from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
import requests
import boto3
import os
import uuid
import json
from decimal import Decimal

_LOG = get_logger(__name__)

dynamodb = boto3.resource("dynamodb", region_name=os.getenv("region", "eu-central-1"))
target_table_name = os.environ.get('target_table', "Weather")
target_table = dynamodb.Table(target_table_name)


class Processor(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        base_url="https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
        response = requests.get(base_url)
        # item = json.loads(json.dumps(response.json()), parse_float=Decimal)
        raw_data = response.json()  # Get JSON response

            # Extract only required fields
        forecast_data = {
            "elevation": raw_data["elevation"],
            "generationtime_ms": raw_data["generationtime_ms"],
            "hourly": {
                "temperature_2m": raw_data["hourly"]["temperature_2m"],
                "time": raw_data["hourly"]["time"]
            },
            "hourly_units": {
                "temperature_2m": raw_data["hourly_units"]["temperature_2m"],
                "time": raw_data["hourly_units"]["time"]
            },
            "latitude": raw_data["latitude"],
            "longitude": raw_data["longitude"],
            "timezone": raw_data["timezone"],
            "timezone_abbreviation": raw_data["timezone_abbreviation"],
            "utc_offset_seconds": raw_data["utc_offset_seconds"]
        }

            # Create item with UUID
        event_item = {
            "id": str(uuid.uuid4()),
            "forecast": json.loads(json.dumps(forecast_data), parse_float=Decimal)
        }
        
        target_table.put_item(Item=event_item)
        _LOG.info(f"Event saved successfully: {event_item}")
        return event_item
    
HANDLER = Processor()

def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
