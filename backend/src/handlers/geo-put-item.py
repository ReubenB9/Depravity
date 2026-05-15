import os
import json
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

def geoPutItemHandler(event, context):
    """
    AWS Lambda Handler to insert a geospatial point into DynamoDB.
    pk is coords, sk is group-user-timestamp
    Expected API Gateway Event Body (JSON):
    {
        "latitude": 36.879163,
        "longitude": 10.243122,
        "creator": "John Doe",
        "group": "Group1",
        "timestamp": "2026-05-04T13:56:22Z",
        "other_attributes": "etc",
         ...
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

    # CHANGE IF WANT DIFFERENT CLASSES OF POINTS
    point_attributes = {}
    for key, value in body.items():
        if key != "ConditionExpression":
            if isinstance(value, (int, float)):
                point_attributes[key] = {'N': str(value)}
            else:
                point_attributes[key] = {'S': str(value)}

    put_item_input = {
        'Item': point_attributes,
        'ConditionExpression': "attribute_not_exists(hashKey)"
    }

    # unique id to use for each point to ensure uniqueness of hash/range pairs
    point_id = group + "-" + name + "-" + timestamp
    
    # database call, not wrapped exception handling since geo library does it
    result = geoDataManager.put_Point(dynamodbgeo.PutPointInput(
        dynamodbgeo.GeoPoint(lat, lon), 
        point_id,
        put_item_input 
    ))

    # checking 
    if result == "Error":
        logger.error("Insertion failed (check console for library-specific error)")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Condition check failed or database error.'})
        }

    logger.info(f"Successfully inserted point {point_id} at {lat}, {lon}")
    
    # 201 response to return
    return {
        'statusCode': 201,
        'body': json.dumps({
            'message': 'Location saved successfully.',
            'id': point_id
        })
    }
