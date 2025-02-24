from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
from botocore.exceptions import ClientError
import json
import re
import boto3
import os

_LOG = get_logger(__name__)

tables_table = os.environ.get('tables_table', "Tables")
reservations_table = os.environ.get('reservations_table', "Reservations")
user_pool_id = os.environ.get('user_pool_id', "simple-booking-userpool")
client_id = os.environ.get('client_id', "simple-booking-userpool")


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
                    'body': json.dumps('Bad Request: Missing required parameters.')
                }
        
            # Validate email
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return {
                    'statusCode': 400,
                    'body': json.dumps('Bad Request: Invalid email format.')
                }
            # Validate password
            password_regex = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[$%^*-_])[A-Za-z\d$%^*-_]{12,}$"
            if not re.match(password_regex, password):
                return {
                    'statusCode': 400,
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
                    'body': json.dumps('Bad Request: Unable to sign up user.')
                }
        
            # Return success status
            return {
                'statusCode': 200,
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
                    "body": json.dumps({"accessToken": id_token})
                }
            
            except ClientError as e:
                error_message = e.response['Error']['Message']
                return {'statusCode': 400, 'body': json.dumps(f'Failed to authenticate: {error_message}')}

        if method == 'POST' and path == '/tables':
            dynamodb = boto3.resource("dynamodb", region_name=os.getenv("region", "eu-central-1"))
            target_table = dynamodb.Table(tables_table)
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
                "body": json.dumps({"accessToken": "id_token"})
            }
        
        if method == 'GET' and path == '/tables':
            dynamodb = boto3.resource("dynamodb", region_name=os.getenv("region", "eu-central-1"))
            target_table = dynamodb.Table(tables_table)
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
                "body": json.dumps({"accessToken": "id_token"})
            }



HANDLER = ApiHandler()

def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
