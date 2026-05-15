import boto3
import os
import json
import logging
from boto3.dynamodb.types import TypeDeserializer

dynamodb = boto3.client('dynamodb')
DYNAMODB_TABLE_NAME = os.environ.get('MAIN_TABLE_NAME', 'mainTable')

iot = boto3.client('iot')
lambda_client = boto3.client('lambda', endpoint_url='http://host.docker.internal:3001')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def usersAddUserToGroupHandler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        username = body.get('username')
        groupname = body.get('groupname')
        code = body.get('code')
        
    except (KeyError, ValueError, TypeError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f"Bad Request. Missing or invalid field: {e}"})
        }
    
    try:
        # Getting users cognito certificate to attach policy to it
        user = lambda_client.invoke(
            FunctionName = 'usersGetItemFunction',
            InvocationType = 'RequestResponse',
            Payload = json.dumps({
                'HTTPMethod': 'GET',
                'body': json.dumps({
                    'username': username
                })
            })
        )

        user_decoded = json.loads(user.get('Payload').read().decode('utf-8'))
        user_body_data = json.loads(user_decoded.get('body', '{}'))
        user_data = user_body_data.get('data', {})
        
        iot_data = user_data.get('IoTCertificate', {})
        logger.info(f"User IoT certificateARN: {iot_data.get('certificateArn', '')}")

        attach = iot.attach_policy(
            policyName=f"{groupname}-Policy",
            target=iot_data.get('certificateArn', '')
        )
