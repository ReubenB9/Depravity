import boto3
import os
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

cognito_client = boto3.client('cognito-idp')

def confirmForgotPasswordHandler(event, context):
    logger.info(f"Received confirm forgot password event: {json.dumps(event)}")

    try:
        body = json.loads(event.get('body', '{}'))
        username = body['username']
        confirmation_code = body['confirmation_code']
        new_password = body['new_password']
    except (KeyError, ValueError, TypeError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'status': 'error', 
                'message': f"Missing or invalid field: {str(e)}"
            })
        }

    try:
        cognito_client.confirm_forgot_password(
            ClientId=CLIENT_ID,
            Username=username,
            ConfirmationCode=confirmation_code,
            Password=new_password
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'message': 'Password successfully changed'
            })
        }

    except cognito_client.exceptions.CodeMismatchException:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Invalid verification code'})
        }
    except cognito_client.exceptions.ExpiredCodeException:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Verification code has expired'})
        }
    except cognito_client.exceptions.UserNotFoundException:
        return {
            'statusCode': 404,
            'body': json.dumps({'status': 'error', 'message': 'User does not exist'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': 'Internal server error'})
        }