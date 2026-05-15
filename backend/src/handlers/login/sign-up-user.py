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

def signUpUserHandler(event, context):
    """
    AWS Lambda Handler to sign up a new user in Cognito.
    Expected API Gateway Event Body (JSON):
    {
        "username": "johndoe",
        "password": "Password123!",
        "email": "example@gmail.com"
        "gender": "male"
        "birthdate": "YYYY-MM-DD"
        }
        """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        body = json.loads(event.get('body', '{}'))
        username = body['username']
        password = body['password']
        email = body['email']
        gender = body['gender']
        birthdate = body['birthdate']
    except (KeyError, ValueError, TypeError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f"Bad Request. Missing or invalid field: {e}"})
        }
    try:
        cognito_response = cognito_client.sign_up(
            ClientId=CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'gender', 'Value': gender},
                {'Name': 'birthdate', 'Value': birthdate}
            ]
        )

        user_post = lambda_client.invoke(
            FunctionName = 'usersPutItemFunction',
            InvocationType = 'RequestResponse',
            Payload = json.dumps({
                'HTTPMethod': 'POST',
                'body': json.dumps({
                    'username': username,
                    'email': email,
                    'birthdate': birthdate,
                    'gender': gender,
                    'createdAt': str(int(context.aws_request_id[:8], 16)),
                })
            })
        )

        user_posted_response = user_post['Payload'].read().decode()
        logger.info(f"Dynamodb user post: {user_post['Payload'].read().decode()} for user: {username}")

        return {
            'statusCode': 201,
            'body': json.dumps({
                'status': 'success',
                'user_sub': cognito_response['UserSub'],
                'user_confirmed': cognito_response['UserConfirmed']
            })
        }
    except cognito_client.exceptions.UsernameExistsException:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Username already exists'})
        }
    except cognito_client.exceptions.InvalidPasswordException:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Password does not meet complexity requirements'})
        }
    except cognito_client.exceptions.InvalidParameterException as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }