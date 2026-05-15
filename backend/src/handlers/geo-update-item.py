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

def geoUpdateItemHandler(event, context):
    """
    AWS Lambda Handler to update/replace a geospatial point into DynamoDB.
    pk is coords, sk is group-user-timestamp
    Expected API Gateway Event Body (JSON):
    {
        "latitude": 36.879163,
        "longitude": 10.243122,
        "creator": "John Doe",
        "group": "Group1",
        "timestamp": "2026-05-04T13:56:22Z",
        "Item": "etc",
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
        update_attributes = str(body['Item'])
        
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"Invalid input data: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f"Bad Request. Missing or invalid field: {e}"})
        }

    # COULD CHANGE IF WANT TO AVOID CHANGING ALL ATTRIBUTES ON UPDATE
    point_attributes = {}
    for key, value in body.items():
        if key != "ConditionExpression":
            if isinstance(value, (int, float)):
                point_attributes[key] = {'N': str(value)}
            else:
                point_attributes[key] = {'S': str(value)}

    expression_attribute_names = {f"#{key}": key for key in point_attributes.keys()}

    expression_attribute_values = {f":new_{key}": value for key, value in point_attributes.items()}

    UpdateItemDict = {
        "UpdateExpression": "set " + ", ".join([f"#{key} = :new_{key}" for key in point_attributes.keys()]),
        "ExpressionAttributeNames": expression_attribute_names,
        "ExpressionAttributeValues": expression_attribute_values,
        "ConditionExpression": "attribute_exists(hashKey)",
        "ReturnValues": "ALL_NEW"
    }

    # unique id to use for each point to ensure uniqueness of hash/range pairs
    point_id = group + "-" + name + "-" + timestamp
    
    # database call
    result=geoDataManager.update_Point(dynamodbgeo.UpdateItemInput(
        dynamodbgeo.GeoPoint(lat, lon), 
        point_id,
        UpdateItemDict 
    ))

    # checking 
    if result == "Error":
        logger.error("Insertion failed (check console for library-specific error)")
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Condition check failed or database error.'})
        }
    
    logger.info(f"Successfully updated point {point_id} with attributes: {UpdateItemDict}")
    
    # 201 response to return
    return {
        'statusCode': 201,
        'body': json.dumps({
            'message': 'Attributes changed successfully.',
            'id': point_id
        })
    }
