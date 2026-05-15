import boto3
import os
import json

MAIN_TABLE_NAME = os.environ.get('MAINTABLE_TABLE_NAME')

dynamodb_client = boto3.client('dynamodb')

def usersUpdateItemHandler(event, context):
    """
    AWS Lambda Handler to update user profile information in DynamoDB.
    Expected API Gateway Event Body (JSON):
    {
        "username": "johndoe",
        'Authentication': {
            'AccessToken': 'string',
            'IdToken': 'string',
            'RefreshToken': 'string',
            'ExpiresIn': 'string'
        },
        etc...
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        username = body.get('username')

    except (KeyError, ValueError, TypeError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f"Bad Request. Missing or invalid field: {e}"})
        }
    
    try:
        update_expr = "SET "
        attr_values = {}
        attr_names = {"#ttl": "TTL"}

        fields = ['email', 'gender', 'birthdate']
        
        updates = []
        for field in fields:
            if field in body:
                updates.append(f"{field} = :{field}")
                attr_values[f":{field}"] = {'S': body[field]}

        if 'Authentication' in body:
            updates.append("Authentication = :auth")
            auth_result = body['Authentication']
            attr_values[':auth'] = {
                'M': {
                    'access_token': {'S': auth_result.get('AccessToken', 'N/A')},
                    'id_token': {'S': auth_result.get('IdToken', 'N/A')},
                    'refresh_token': {'S': auth_result.get('RefreshToken', 'N/A')},
                    'expires_in': {'N': str(auth_result.get('ExpiresIn', 0))},
                }
            }

        update_expr += ", ".join(updates)
        update_expr += " REMOVE #ttl"

        if not attr_values:
            return {'statusCode': 400, 'body': json.dumps({'error': 'must pass update parameters in'})}
        
        dynamodb_client.update_item(
            TableName=MAIN_TABLE_NAME,
            Key={'PK': {'S': f"USER#{username}"}, 'SK': {'S': f"PROFILE#{username}"}},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values
        )

        return {'statusCode': 200, 'body': json.dumps({'message': 'Success'})}

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}