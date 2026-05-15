import boto3
import os
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

LOCAL_ENDPOINT = os.environ.get('LOCAL_ENDPOINT')
CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

cognito_client = boto3.client('cognito-idp')
lambda_client = boto3.client('lambda', endpoint_url=LOCAL_ENDPOINT)

def loginHandler(event, context):
    """
    AWS Lambda Handler to authenticate a user.
    Expected API Gateway Event Body (JSON):
    {
        "username": "johndoe",
        "password": "Password123!"
    }
    """
    logger.info(f"Received login event: {json.dumps(event)}")

    try:
        body = json.loads(event.get('body', '{}'))
        username = body['username']
        password = body['password']
    except (KeyError, ValueError, TypeError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'error', 
                'message': f"Missing or invalid field: {str(e)}"
            })
        }

    try:
        response = cognito_client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )

        auth_result = response.get('AuthenticationResult', {})
        
        update = lambda_client.invoke(
            FunctionName='usersUpdateItemFunction',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'HTTPMethod': 'PATCH',
                'body': json.dumps({
                    'username': username,
                    'Authentication': {
                        'AccessToken': auth_result.get('AccessToken'),
                        'IdToken': auth_result.get('IdToken'),
                        'RefreshToken': auth_result.get('RefreshToken'),
                        'ExpiresIn': str(auth_result.get('ExpiresIn'))
                    }
                })
            }),
        )

        # logger.info(f"Updated user auth data response: {update['Payload'].read().decode()} for user: {username}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'access_token': auth_result.get('AccessToken'),
                'id_token': auth_result.get('IdToken'),
                'refresh_token': auth_result.get('RefreshToken'),
                'expires_in': auth_result.get('ExpiresIn')
            })
        }

    except cognito_client.exceptions.NotAuthorizedException:
        return {
            'statusCode': 401,
            'body': json.dumps({'status': 'error', 'message': 'Incorrect username or password'})
        }
    except cognito_client.exceptions.UserNotConfirmedException:
        return {
            'statusCode': 403,
            'body': json.dumps({'status': 'error', 'message': 'User is not confirmed yet'})
        }
    except cognito_client.exceptions.UserNotFoundException:
        return {
            'statusCode': 404,
            'body': json.dumps({'status': 'error', 'message': 'User does not exist'})
        }
    except cognito_client.exceptions.PasswordResetRequiredException:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Password reset required'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': 'Internal server error'})
        }