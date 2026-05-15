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
        group = lambda_client.invoke(
            FunctionName = 'groupsGetItemFunction',
            InvocationType = 'RequestResponse',
            Payload = json.dumps({
                'HTTPMethod': 'GET',
                'body': json.dumps({
                    'groupname': groupname
                })
            })
        )
        
        group_decoded = json.loads(group.get('Payload').read().decode('utf-8'))
        group_body_data = json.loads(group_decoded.get('body', '{}'))
        group_data = group_body_data.get('data', {})

        # logger.info(f"Group response: {group_decoded}")
        # logger.info(f"Entry code: {group_data.get('entryCode')}, provided code: {code}")

        if group_data.get('entryCode') != code:
            return {'statusCode': 403, 'body': json.dumps({'error': 'Invalid entry code'})}
        
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

        # logger.info(f"Attach policy response: {attach}")

        # Adds group name to user dynamodb item
        dynamodb.update_item(
            TableName=DYNAMODB_TABLE_NAME,
            Key={'PK': {'S': f"USER#{username}"}, 'SK': {'S': f"PROFILE#{username}"}},
            UpdateExpression="SET groups = list_append(#g, :group), currentGroup = :groupname",
            ExpressionAttributeNames={"#g" : "groups"},
            ExpressionAttributeValues={":group": {'L': [{'S': groupname}]}, ":groupname": {'S': groupname}},
        )

        return {'statusCode': 200, 
                'body': json.dumps({'message': f'{username} added to {groupname} successfully!'})
            }

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}