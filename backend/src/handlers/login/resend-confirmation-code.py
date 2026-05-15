import boto3
import os
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cognito_client = boto3.client('cognito-idp')
CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

def resendConfirmationCodeHandler(event, context):
    """
    AWS Lambda Handler to resend a confirmation code for a newly signed-up user
    Expected API Gateway Event Body (JSON):
    {
        "username": "johndoe"
    }
    """
    logger.info(f"Received resend confirmation event: {json.dumps(event)}")

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
        response = cognito_client.resend_confirmation_code(
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
    except cognito_client.exceptions.InvalidParameterException as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }
    except cognito_client.exceptions.CodeDeliveryFailureException:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Failed to deliver the confirmation code. Check contact info.'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': 'Internal server error'})
        }