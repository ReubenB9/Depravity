import json
import logging
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


cognito_client = boto3.client('cognito-idp')
CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')

def addUserPermissionsHandler(event, context):
    logger.info(f"Received confirm forgot password event: {json.dumps(event)}")

    try:
        body = json.loads(event.get('body', '{}'))
        username = body['username']
    
    except (KeyError, ValueError, TypeError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'error', 
                'message': f"Missing or invalid field: {str(e)}"
            })
        }

    try:
        response = cognito_client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=username,
            GroupName='User'
        )
        return {
            'statusCode': 200,
            'body' : json.dumps({
                'status': 'success',
                'message': 'User permissions added successfully'
            })
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'error', 'message': f"Failed to add 'User' permissions: {str(e)}"
            })
        }