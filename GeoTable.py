# Utilizing code given by geo library to create a geospatial tabl
# Creates geo table with dynamodbgeo config
import boto3
import dynamodbgeo
import uuid

dynamodb = boto3.client('dynamodb', region_name='us-east-1')

config = dynamodbgeo.GeoDataManagerConfiguration(dynamodb, 'GeoTable')

geoDataManager = dynamodbgeo.GeoDataManager(config)

# Pick a hashKeyLength appropriate to your usage
config.hashKeyLength = 5

# Use GeoTableUtil to help construct a CreateTableInput.
table_util = dynamodbgeo.GeoTableUtil(config)
create_table_input=table_util.getCreateTableRequest()

#tweaking the base table parameters as a dict
create_table_input["ProvisionedThroughput"]['ReadCapacityUnits']=5

# Use GeoTableUtil to create the table
table_util.create_table(create_table_input)

# #preparing non key attributes for the item to add

# PutItemInput = {
#         'Item': {
#             'Country': {'S': "Tunisia"},
#             'Capital': {'S': "Tunis"},
#             'year': {'S': '2020'}
#         },
#         'ConditionExpression': "attribute_not_exists(hashKey)" # ... Anything else to pass through to `putItem`, eg ConditionExpression

# }

# geoDataManager.put_Point(dynamodbgeo.PutPointInput(
#         dynamodbgeo.GeoPoint(36.879163, 10.243120), # latitude then latitude longitude
#          str( uuid.uuid4()), # Use this to ensure uniqueness of the hash/range pairs.
#          PutItemInput # pass the dict here
#         ))

# #define a dict of the item to update
# UpdateItemDict= { # Dont provide TableName and Key, they are filled in for you
#         "UpdateExpression": "set Capital = :val1",
#         "ConditionExpression": "Capital = :val2",
#         "ExpressionAttributeValues": {
#             ":val1": {"S": "Tunis"},
#             ":val2": {"S": "Ariana"}
#         },
#         "ReturnValues": "ALL_NEW"
# }
# geoDataManager.update_Point(dynamodbgeo.UpdateItemInput(
#         dynamodbgeo.GeoPoint(36.879163,10.24312), # latitude then latitude longitude
#          "1e955491-d8ba-483d-b7ab-98370a8acf82", # Use this to ensure uniqueness of the hash/range pairs.
#          UpdateItemDict # pass the dict that contain the remaining parameters here
#          ))

#         # Preparing dict of the item to delete
# DeleteItemDict= {
#             "ConditionExpression": "attribute_exists(Country)",
#             "ReturnValues": "ALL_OLD"
#             # Don't put keys here, they will be generated for you implecitly
#         }

# geoDataManager.delete_Point(
#     dynamodbgeo.DeleteItemInput(
#     dynamodbgeo.GeoPoint(36.879163,10.24312), # latitude then latitude longitude
#         "0df9742f-619b-49e5-b79e-9fb94279d30c", # Use this to ensure uniqueness of the hash/range pairs.
#         DeleteItemDict # pass the dict that contain the remaining parameters here
#         ))
