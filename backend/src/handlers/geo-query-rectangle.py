import os
import json
import uuid
import logging
import boto3
from botocore.exceptions import ClientError
import dynamodbgeo

# logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# env variables
TABLE_NAME = os.environ.get('GEO_TABLE_NAME', 'GeoTable')
REGION = os.environ.get('AWS_REGION', 'us-east-1') # Lambda sets this automatically

# reuseable global init
try:
    dynamodb = boto3.client('dynamodb', region_name=REGION)
    config = dynamodbgeo.GeoDataManagerConfiguration(dynamodb, TABLE_NAME)
    # config.hashKeyLength = 5 # Ensure this matches your table creation script!
    geoDataManager = dynamodbgeo.GeoDataManager(config)
except Exception as e:
    logger.critical(f"Failed to initialize GeoDataManager: {e}")
    raise
  
def geoGetQueryHandler(event, context):
    """
    AWS Lambda Handler to query a geospatial rectangle in DynamoDB and filter.
    Expected API Gateway Event Body (JSON):
    {
        "lat1": 36.879163,
        "lon1": 10.243122,
        "lat2": 36.889163,
        "lon2": 10.253122,
        "QueryFilters" : {
            "FilterExpression": "Capital = :val1 AND District = :val2",
            "ExpressionAttributeValues": {
                ":val1": {"S": "Moscow"},
                ":val2": {"S": "Russia"},
            }
        }
    }
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        body = json.loads(event.get('body', '{}'))
        lat1 = float(body['lat1'])
        lon1 = float(body['lon1'])
        lat2 = float(body['lat2'])
        lon2 = float(body['lon2'])
        QueryFilters = body['QueryFilters']
        
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Invalid input data: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f"Bad Request. Missing or invalid field: {e}"})
        }


    
    # database call
    try:
        points = geoDataManager.queryRectangle(
            dynamodbgeo.QueryRectangleRequest(
                dynamodbgeo.GeoPoint(lat1, lon1),
                dynamodbgeo.GeoPoint(lat2, lon2), QueryFilters))
        
        logger.info(f"Successfully returned points in rectangle defined by {lat1}, {lon1} and {lat2}, {lon2} with filters {QueryFilters}")
        
        # 201 response to return
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Locations returned successfully.',
                'data': points
            })
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"DynamoDB ClientError: {error_code} - {e.response['Error']['Message']}")
        
        if error_code == 'ConditionalCheckFailedException':
            return {
                'statusCode': 409,
                'body': json.dumps({'error': 'A point at this exact geo-hash already exists.'})
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