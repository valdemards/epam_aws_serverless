from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
from botocore.exceptions import ClientError
import json
import re
import boto3

_LOG = get_logger(__name__)


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass
        
    def handle_request(self, event, context):
        method = event['requestContext']['http']['method']
        path = event['requestContext']['http']['path']
        client = boto3.client('cognito-idp')
        response = client.list_user_pools(MaxResults=60)
        for pool in response['UserPools']:
            if pool['Name'] == 'cmtr-eeb642ea-simple-booking-userpool':
                user_pool_id = pool['Id']


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
                    ClientId=user_pool_id,
                )
                # Extract token from the response
                access_token = response['AuthenticationResult']['AccessToken']
                id_token = response['AuthenticationResult']['IdToken']
                refresh_token = response['AuthenticationResult']['RefreshToken']

                tokens = {
                    'accessToken': access_token,
                    'idToken': id_token,
                    'refreshToken': refresh_token
                }
                return {'statusCode': 200, 'body': json.dumps({'message': 'Authentication successful', 'tokens': tokens})}
            
            except ClientError as e:
                _LOG.error(f"Error in signing in user: {e}")
                error_message = e.response['Error']['Message']
                return {'statusCode': 400, 'body': json.dumps(f'Failed to authenticate: {error_message}')}

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
