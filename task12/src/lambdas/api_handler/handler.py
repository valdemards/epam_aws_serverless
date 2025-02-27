from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
from botocore.exceptions import ClientError
import json
import re
import boto3
import os
import uuid
from datetime import datetime

_LOG = get_logger(__name__)

reservations_table = os.environ.get('reservations_table', "Reservations")
user_pool_id = os.environ.get('user_pool_id', "simple-booking-userpool")
client_id = os.environ.get('client_id', "simple-booking-userpool")
response_headers = {
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*',
                    'Accept-Version': '*'
                    }

class ApiHandler(AbstractLambda):


    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        method = event['httpMethod']
        path = event['path']
        client = boto3.client('cognito-idp')
        response = client.list_user_pools(MaxResults=60)

        if method == 'POST' and path == '/signup':
            try:
                data = json.loads(event['body'])
                first_name = data['firstName']
                last_name = data['lastName']
                email = data['email']
                password = data['password']
            
            except KeyError:
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps('Bad Request: Missing required parameters.')
                }
        
            # Validate email
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps('Bad Request: Invalid email format.')
                }
            # Validate password
            password_regex = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[$%^*-_])[A-Za-z\d$%^*-_]{12,}$"
            if not re.match(password_regex, password):
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps('Bad Request: Password does not meet criteria.')
                }
            # Create user in Cognito
            try:
                response = client.admin_create_user(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=[
                    {
                        'Name': 'given_name',
                        'Value': first_name + last_name
                    },
                    {
                        'Name': 'email',
                        'Value': email
                    },
                    {
                        'Name': 'email_verified',
                        'Value': 'true'
                    },
                ],
                TemporaryPassword=password,
                MessageAction='SUPPRESS',
                )

            except ClientError as e:
                print(e)
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps('Bad Request: Unable to sign up user.')
                }
        
            # Return success status
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps('OK: Sign-up process is successful.')
            }

        if method == 'POST' and path == '/signin':
            try :
                data = json.loads(event['body'])
                email = data['email']
                password = data['password']
            except:
                return {
                    'statusCode': 400,
                    'headers': response_headers,
                    'body': json.dumps('Bad Request: Missing or malformed request data.')
                }
            try:
                response = client.initiate_auth(
                    AuthFlow='USER_PASSWORD_AUTH',
                    AuthParameters={'USERNAME': email, 'PASSWORD': password},
                    ClientId=client_id,
                )
                if response.get('ChallengeName'):
                    response = client.respond_to_auth_challenge(
                        Session=response['Session'],
                        ClientId=client_id,
                        ChallengeName='NEW_PASSWORD_REQUIRED',
                        ChallengeResponses={'USERNAME': email, 'NEW_PASSWORD': password}
                    )
                access_token = response['AuthenticationResult']['AccessToken'] 
                id_token = response['AuthenticationResult']['IdToken']
                return {
                    "statusCode": 200,
                    'headers': response_headers, 
                    "body": json.dumps({"accessToken": id_token})
                }
            
            except ClientError as e:
                error_message = e.response['Error']['Message']
                return {
                    'statusCode': 400, 
                    'headers': response_headers,
                    'body': json.dumps(f'Failed to authenticate: {error_message}')
                    }

        if method == 'POST' and path == '/tables':
            dynamodb = boto3.resource("dynamodb", region_name=os.getenv("region", "eu-central-1"))
            tables_table_name = os.environ.get('tables_table', "Tables")
            target_table = dynamodb.Table(tables_table_name)
            body = json.loads(event['body'])
            tables_entry = {
                            'id': int(body['id']),
                            'number': int(body['number']),
                            'places': int(body['places']),
                            'isVip': body['isVip'],
                            'minOrder': int(body['minOrder'])
            }

            target = target_table.put_item(Item=tables_entry)
        
            return {
                "statusCode": 200,
                'headers': response_headers, 
                "body": json.dumps({"id": int(body['id'])})
            }
        
        if method == 'GET' and path.startswith('/tables'):
            dynamodb = boto3.resource("dynamodb", region_name=os.getenv("region", "eu-central-1"))
            target_table_name = os.environ.get('tables_table', "Tables")
            target_table = dynamodb.Table(target_table_name)
            print(event)
            if event['pathParameters']:
                print(event)
                table_id = event['pathParameters']['tableId']
                response = target_table.get_item(Key={'id': int(table_id)})
                item = response['Item']
                return {
                    "statusCode": 200,
                    'headers': response_headers, 
                    "body": json.dumps(item, default=int)
                }
            else:
                response = target_table.scan()
                items = response['Items']
                return {
                    "statusCode": 200,
                    'headers': response_headers, 
                    "body": json.dumps({"tables": items}, default=int)
                }
            
        if method == 'POST' and path == '/reservations':
            dynamodb = boto3.resource("dynamodb", region_name=os.getenv("region", "eu-central-1"))
            tables_table_name = os.environ.get('tables_table', "Tables")
            tables_table = dynamodb.Table(tables_table_name)
            response = tables_table.scan()
            tables = response['Items']

            reservations_table_name = os.environ.get('reservations_table', "Reservations")
            reservations_table= dynamodb.Table(reservations_table_name)
            response = reservations_table.scan()
            reservations = response['Items']

            body = json.loads(event['body'])
            table_numbers = []
            for table in tables:
                table_numbers.append(table['number'])                   
            reservation_entry = {
                            'id': str(uuid.uuid4()),
                            'tableNumber': int(body['tableNumber']),
                            'clientName': body['clientName'],
                            'phoneNumber': body['phoneNumber'],
                            'date': body['date'],
                            'slotTimeStart': body['slotTimeStart'],
                            'slotTimeEnd': body['slotTimeEnd']
            }

            if reservation_entry['tableNumber'] not in table_numbers:
                return {    
                    "statusCode": 400,
                    'headers': response_headers, 
                    "body": json.dumps({"error": "Table number does not exist"})
                }
            
            for reservation in reservations:
                if reservation['tableNumber'] == reservation_entry['tableNumber'] and reservation['date'] == reservation_entry['date']:
                    reservation_start = datetime.strptime(reservation['slotTimeStart'], '%H:%M')
                    reservation_end = datetime.strptime(reservation['slotTimeEnd'], '%H:%M')
                    new_reservation_start = datetime.strptime(reservation_entry['slotTimeStart'], '%H:%M')
                    new_reservation_end = datetime.strptime(reservation_entry['slotTimeEnd'], '%H:%M')
                    if (new_reservation_start >= reservation_start and new_reservation_start <= reservation_end) or (new_reservation_end >= reservation_start and new_reservation_end <= reservation_end):
                        return {    
                            "statusCode": 400,
                            'headers': response_headers, 
                            "body": json.dumps({"error": "Reservation already exists for the same table and date"})
                        }
                    
            target = reservations_table.put_item(Item=reservation_entry)
            return {
                "statusCode": 200,
                'headers': response_headers, 
                "body": json.dumps({"reservationId": reservation_entry['id']})
            }
    
        if method == 'GET' and path == '/reservations':
            dynamodb = boto3.resource("dynamodb", region_name=os.getenv("region", "eu-central-1"))
            reservations_table_name = os.environ.get('reservations_table', "Reservarions")
            reservations_table = dynamodb.Table(reservations_table_name)
            response = reservations_table.scan()
            items = response['Items']
            return {
                "statusCode": 200,
                'headers': response_headers, 
                "body": json.dumps({"reservations": items}, default=int)
            }
   


HANDLER = ApiHandler()

def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
