import boto3
import json

lambda_client = boto3.client('lambda', endpoint_url='http://127.0.0.1:3001')

user = lambda_client.invoke(
    FunctionName = 'usersGetItemFunction',
    InvocationType = 'RequestResponse',
    Payload = json.dumps({
        'HTTPMethod': 'GET',
        'body': json.dumps({
            'username': 'johndoe'
        })
    })
)

user_decoded = json.loads(user.get('Payload').read().decode('utf-8'))
user_body_data = json.loads(user_decoded.get('body', '{}'))
current_group = user_body_data['data']['groups'][0]

def test_publish_to_iot_topic():
    iot = boto3.client('iot-data')
    response = iot.publish(
        topic='topic/{current_group}/location'.format(current_group=current_group),
        qos=0,
        payload='{"message": "Hello, IoT!"}'
    )
    print("Publish response:", response)

test_publish_to_iot_topic()

