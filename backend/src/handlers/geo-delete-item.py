import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
import dynamodbgeo

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get('GEO_TABLE_NAME', 'GeoTable')

try:
    dynamodb = boto3.client('dynamodb')
    config = dynamodbgeo.GeoDataManagerConfiguration(dynamodb, TABLE_NAME)
    geoDataManager = dynamodbgeo.GeoDataManager(config)
except Exception as e:
    logger.critical(f"Failed to initialize GeoDataManager: {e}")
    raise

def geoDeleteItemHandler(event, context):
    """
    AWS Lambda Handler to delete a geospatial point from DynamoDB.
    Expected API Gateway Event Body (JSON):
    {
        "latitude": 36.879163,
        "longitude": 10.243122,
        "creator": "John Doe",
        "group": "Group1",
        "timestamp": "2026-05-04T13:56:22Z",
        "items": "etc",
    }
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        body = json.loads(event.get('body', '{}'))
        lat = float(body['latitude'])
        lon = float(body['longitude'])
        group = str(body['group'])
        name = str(body['creator'])
        timestamp = str(body['timestamp'])
        
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Invalid input data: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f"Bad Request. Missing or invalid field: {e}"})
        }

    delete_item_dict = {
        "ReturnValues": "ALL_OLD"
    }

    point_id = group + "-" + name + "-" + timestamp

    try:
        response = geoDataManager.delete_Point(
            dynamodbgeo.DeleteItemInput(
                dynamodbgeo.GeoPoint(lat, lon), 
                point_id, 
                delete_item_dict
            )
        )

        if 'Attributes' not in response:
            logger.warning(f"Point {point_id} not found or already deleted.")
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Point not found.'})
            }

        logger.info(f"Successfully deleted point {point_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Location deleted successfully.',
                'deleted_id': point_id
            })
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"DynamoDB ClientError: {error_code} - {e.response['Error']['Message']}")
        
        if error_code == 'ConditionalCheckFailedException':
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Condition failed. You may not have permission to delete this item.'})
            }
            
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal database error.'})
        }
        
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error.'})
        }