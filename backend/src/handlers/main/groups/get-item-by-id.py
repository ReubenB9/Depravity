import os
import json
import logging
import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer, Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAIN_TABLE_NAME = os.environ.get('MAINTABLE_TABLE_NAME')

dynamodb_client = boto3.client('dynamodb')

def groupsGetHandler(event, context):
    """
    AWS Lambda Handler to query a groups metadata
    Expected API Gateway Event Body (JSON):
    {
        "groupname": "Group1"
    }
    """
    logger.info(f"Received event: {event}")
    
    try:
        body = json.loads(event.get('body', '{}'))
        groupname = body['groupname']
        
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Invalid input data: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f"Bad Request. Missing or invalid field: {e}"})
        }

    try:
        data = dynamodb_client.get_item(
            TableName=MAIN_TABLE_NAME,
            Key={
                'PK': {'S': f"GROUP#{groupname}"},
                'SK': {'S': "METADATA"}
            }
        )
        
        logger.info(f'Dynamo Data: {data}')
        items = data.get('Item')
        deserializer = TypeDeserializer()
        cleaned_items = {k: deserializer.deserialize(v) for k, v in items.items()}

        return {
            'statusCode': 201,
            'body': json.dumps({
                "message": "Group items returned successfully.",
                "data": cleaned_items
            })
        }

    except Exception as e:
        logger.exception("An unexpected error occurred.")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Error querying DynamoDB: {str(e)}"})
        }