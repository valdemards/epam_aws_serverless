
import os
import uuid
from datetime import datetime
import boto3
from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger(__name__)

dynamodb = boto3.resource("dynamodb", region_name=os.getenv("region", "eu-central-1"))
target_table_name = os.environ.get('target_table', "Audit")
target_table = dynamodb.Table(target_table_name)

class AuditProducer(AbstractLambda):

    def validate_request(self, event) -> dict:
        if 'Records' not in event or not event['Records']:
            raise ValueError("No DynamoDB records found in the event.")
        pass

    def handle_request(self, event, context):
        for record in event['Records']:
            # Only process MODIFY and INSERT events
            if record['eventName'] in ['INSERT', 'MODIFY']:
                new_image = record['dynamodb']['NewImage']
                old_image = record['dynamodb'].get('OldImage')
                item_key = new_image['key']['S']
                modification_time = datetime.utcnow().isoformat() + 'Z'
                if record['eventName'] == 'INSERT':
                    newValue = {
                        'key': item_key,
                        'value': int(new_image['value']['N'])
                    }
                    audit_entry = {
                        'id': str(uuid.uuid4()),
                        'itemKey': item_key,
                        'modificationTime': modification_time,
                        'newValue': newValue
                    }
                elif record['eventName'] == 'MODIFY':
                    updated_attr = 'value'  # Assuming 'value' is the only field that can change
                    oldValue = int(old_image['value']['N'])
                    newValue = int(new_image['value']['N'])
                    audit_entry = {
                        'id': str(uuid.uuid4()),
                        'itemKey': item_key,
                        'modificationTime': modification_time,
                        'updatedAttribute': updated_attr,
                        'oldValue': oldValue,
                        'newValue': newValue
                    }
                # Put the audit entry into the Audit table
                target = target_table.put_item(Item=audit_entry)
        return 200

HANDLER = AuditProducer()

def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)