import boto3
import os
import json
import time

MAIN_TABLE_NAME = os.environ.get('MAINTABLE_TABLE_NAME')

dynamodb = boto3.client('dynamodb')

def mainPostUserItemHandler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        username = body.get('username')
        email = body.get('email')
        gender = body.get('gender')
        birthdate = body.get('birthdate')
        
    except (KeyError, ValueError, TypeError) as e:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': "Bad Request. Missing or invalid fields."})
            }

    try:
        dynamodb.put_item(
            TableName=MAIN_TABLE_NAME,
            Item={
                'PK': {'S': f"USER#{username}"},
                'SK': {'S': f"PROFILE#{username}"},
                'email': {'S': email},
                'gender': {'S': gender},
                'birthdate': {'S': birthdate},
                'createdAt': {'S': str(int(context.aws_request_id[:8], 16))},
                'TTL' : {'S': str(int(time.time() + 1800))}, # Set TTL to 30 minutes
                'groups': {'L': []},
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User profile temporarifly saved!'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Error saving to DynamoDB: {str(e)}"})
        }