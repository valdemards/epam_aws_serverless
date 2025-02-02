import json
import uuid
import os
from datetime import datetime
import boto3
from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger(__name__)

# Создаем клиент DynamoDB
dynamodb = boto3.resource("dynamodb", region_name=os.getenv("region", "eu-central-1"))
table_name = os.environ.get('target_table', "Events")
table = dynamodb.Table(table_name)


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        """
        Проверяет, что входной запрос содержит необходимые поля
        """
        try:
            body = event
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")

        if "principalId" not in body or "content" not in body:
            raise ValueError("Missing required fields: principalId, content")
        pass

    def handle_request(self, event, context):
        """
        Обрабатывает входящий POST-запрос, сохраняет данные в DynamoDB и возвращает результат
        """
        try:
            event_item = {
                "id": str(uuid.uuid4()), 
                "principalId": event["principalId"],
                "createdAt": datetime.utcnow().isoformat(),
                "body": event["content"]
            }
            # Сохранение в DynamoDB
            table.put_item(Item=event_item)
            _LOG.info(f"Event saved successfully: {event_item}")
            # Возвращаем ответ с кодом 201 (Created)
            return {
                "statusCode": 201,
                "event": event_item
            }

        except ValueError as e:
            _LOG.error(f"Validation error: {str(e)}")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": str(e)})
            }

        except Exception as e:
            _LOG.error(f"Internal server error: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Internal server error"})
            }


# Создаем экземпляр обработчика
HANDLER = ApiHandler()


def lambda_handler(event, context):
    """
    AWS Lambda entry point
    """
    return HANDLER.lambda_handler(event=event, context=context)
