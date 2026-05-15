import boto3
import os
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
LOCAL_ENDPOINT = os.environ.get('LOCAL_ENDPOINT')

cognito_client = boto3.client('cognito-idp')
lambda_client = boto3.client('lambda', endpoint_url=LOCAL_ENDPOINT)

def confirmSignUpHandler(event, context):
    """
    AWS Handler to sign up a new user in Cognito
    also adds users to permissions group "User" in cognito user pool
    DOES NOT GENERATE SESSION TOKEN    
    Expected API Gateway Event Body (JSON):
    {
        "username": "johndoe",
        "confirmation": "123456!",
    }
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        body = json.loads(event.get('body', '{}'))
        username = body['username']
        confirmation = body['confirmation']
    except (KeyError, ValueError, TypeError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f"Bad Request. Missing or invalid field: {e}"})
        }
        
    try:
        # response = cognito_client.confirm_sign_up(
        #     ClientId=CLIENT_ID,
        #     Username=username,
        #     ConfirmationCode=confirmation
        # )
        # # logger.info(f"Confirm sign up response: {json.dumps(response)}")

        # add_permissions = lambda_client.invoke(
        #     FunctionName='loginAddUserPermissionsFunction',
        #     InvocationType='RequestResponse',
        #     Payload=json.dumps({
        #         'HTTPMethod': 'POST',
        #         'body': json.dumps({
        #             'username': username,
        #             'group': 'User'
        #         })
        #     }),
        # )

        # logger.info(f"Add permissions response: {add_permissions['Payload'].read().decode()} for user: {username}")

        user = lambda_client.invoke(
            FunctionName='usersGetItemFunction',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'HTTPMethod': 'GET',
                'body': json.dumps({
                    'username': username,
                    'group': 'User'
                })
            }),
        )
        user_password = user['Payload'].read().decode()
        logger.info(f'user info: {user_password}')
        return {
            'statusCode': 201,
            'body': json.dumps({
                'status': 'success',
                'message': f"User {username} confirmed successfully and permissions added",
            })
        }
    except cognito_client.exceptions.CodeMismatchException:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Invalid confirmation code'})
        }
    except cognito_client.exceptions.ExpiredCodeException:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Expired code'})
        }
    except cognito_client.exceptions.UserNotFoundException:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'User not found'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }
