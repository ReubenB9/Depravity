import random
import boto3
import os
import json

ACCOUNT_ID = os.environ.get('ACCOUNT_ID')
MAIN_TABLE_NAME = os.environ.get('MAINTABLE_TABLE_NAME')

dynamodb_client = boto3.client('dynamodb')
iot_client = boto3.client('iot')

def groupsPostItemHandler(event, context):
    """
    Generates an iot policy and an entry code for the group and saves
    in dynamodb with the groupname as the topic name.

    body: {
    "groupname": "Group1"
    }
    """

    try:
        body = json.loads(event.get('body', '{}'))
        groupname = body.get('groupname')

    except (KeyError, ValueError, TypeError) as e:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': "Bad Request. Missing or invalid fields."})
            }

    try:
        # policy = iot_client.create_policy(
        #     policyName=f"{groupname}-Policy",
        #     policyDocument=json.dumps({
        #         "Version": "2012-10-17",
        #         "Statement": [
        #             {
        #                 "Effect": "Allow",
        #                 "Action": [
        #                     "iot:Connect",
        #                     "iot:Publish",
        #                     "iot:Subscribe",
        #                     "iot:Receive"
        #                 ],
        #                 "Resource": "arn:aws:iot:us-east-1:{AccountId}:topic/{groupname}/location".format(AccountId=ACCOUNT_ID, groupname=groupname)
        #             }
        #         ]
        #     })
        # )

        # Code to use for users to join group
        code = random.randint(100000, 999999)

        dynamodb_client.put_item(
            TableName=MAIN_TABLE_NAME,
            Item={
                'PK': {'S': f"GROUP#{groupname}"},
                'SK': {'S': "METADATA"},
                'entryCode': {'S': str(code)},
                'topic': {'S': groupname},
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Group saved successfully!'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Error saving to DynamoDB: {str(e)}"})
        }