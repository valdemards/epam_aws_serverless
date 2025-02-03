from tests.test_hello_world import HelloWorldLambdaTestCase
import json

class TestSuccess(HelloWorldLambdaTestCase):

    def setUp(self):
            super().setUp()
            self.success_event = {
                'requestContext': {
                    'http': {
                        'method': 'GET',
                        'path': '/hello'
                    }
                }
            }
            self.error_event = {
                'requestContext': {
                    'http': {
                        'method': 'POST', 
                        'path': '/student_id'
                    }
                }
            }

    def test_success_hello(self):
        """
        Test successful GET request to /hello
        """
        response = self.HANDLER.lambda_handler(self.success_event, {})
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response_body['message'], "Hello from Lambda")

    def test_failure_method_not_allowed(self):
        """
        Test failure due to unsupported HTTP method on /hello
        """
        self.error_event['requestContext']['http']['method'] = 'POST'
        response = self.HANDLER.lambda_handler(self.error_event, {})
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('unsupported method', response_body['message'])

    def test_failure_wrong_endpoint(self):
        """
        Test failure due to request to an unsupported endpoint
        """
        self.error_event['requestContext']['http']['path'] = '/some_random_path'
        response = self.HANDLER.lambda_handler(self.error_event, {})
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Bad request syntax or unsupported method', response_body['message'])

