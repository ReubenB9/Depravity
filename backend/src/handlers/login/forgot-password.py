import boto3
import os
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

cognito_client = boto3.client('cognito-idp')

def forgotPasswordHandler(event, context):
    """
    AWS Handler to initiate password reset.
    Expected API Gateway Event Body (JSON):
    {
        "username": "johndoe"
    }
    """
    logger.info(f"Received forgot password event: {json.dumps(event)}")

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
        response = cognito_client.forgot_password(
            ClientId=CLIENT_ID,
            Username=username
        )

        delivery = response.get('CodeDeliveryDetails', {})
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'delivery_medium': delivery.get('DeliveryMedium'),
                'destination': delivery.get('Destination')
            })
        }

    except cognito_client.exceptions.UserNotFoundException:
        return {
            'statusCode': 404,
            'body': json.dumps({'status': 'error', 'message': 'User does not exist'})
        }
    except cognito_client.exceptions.LimitExceededException:
        return {
            'statusCode': 429,
            'body': json.dumps({'status': 'error', 'message': 'Attempt limit exceeded. Please try again later.'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': 'Internal server error'})
        }