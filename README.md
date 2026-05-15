This application is based around two NoSQL databases; one is a DynamoDB table to store user and group information (put into same table for cost) and the other is a DynamoDB geo table using the DynamoDB Geo library which uses a geohash to make the storing/lookup of location based data more efficient. Database Structures provided below:


General Information Table (GSI also shown in table)
PK	            SK	            Other Attributes
USER#ALICE	      PROFILE#ALICE	{"email": "alice@dev.com"}
GROUP#ADMIN	      METADATA	      {“policy”: “policy”}

Query Structures: PK = USER#123 and SK begins_with(GROUP#)
Or GSI (for all users in a group): SK = GROUP#ABC and PK begins_with(USER#)


Geo DynamoDB Structure
PK	      SK	                  Other Point Attributes
GEOHASH	GROUP-USER-TIMESTAMP	{“description”: “example”}

Query Structures: PK = (Coord generated Geohash) and SK = (unique SK within Geohash location)


Features and Structure
User & Authentication
* Secure custom signup/login flow with cognito
* On Duo cognito approval
    * Attach user permissions policy
    * Generate user IoT certificate
Group Management
* Create group with
    * Unique entry code for joining
    * Unique IoT Core policy for groups users permissions
* Join group
    * Verifies entry code
    * Attaches groups policy to users unique identity pool ID
* Invite other users via sharing code or link
Live Data
* Publishing live user locations to group topics
* Subscription to GraphQL in AppSync for receiving user locations
Frontend (React-Native)
* Responsive, modern UI built with react-native
* Dynamic components for live map (react-native-maps)
Backend (Serverless utilizing AWS Lambda for connecting services)
* Custom RESTful API endpoints for DynamoDB and AppSync
* Cognito-based authentication
* DynamoDB for data storage
* IoT Core for receiving live data
* AppSync for pushing live data to users
* Location Services for processing user locations
* CloudWatch for live app statistics
Database (DynamoDB)
* Horizontal scaling for users and groups
* Map pins saved with geohashing for quick area querying
Deployment
* Complete AWS serverless backend using cognito, IoT Core, Lambda, Location Services, Cloudwatch
* Frontend built with react native and hosted through App Store and Google Play Store
Testing and Development
* Local testing with SAM CLI

Commands for Local Deployment
To build and deploy the application for the first time locally, download the git repo and create your own env.json file. Then run the following in your shell:

```bash
sam build
```

The first command will build the source of your application. Then you can either locally invoke commands using docker instances of AWS DBs or you can deploy databases to test the lambda functions locally in a live environment. If a lambda function relies on invoking other lambda functions locally run the command below to start local instances of lambda. Ensure port is correct in your local env.json.

```bash
sam local start-lambda
```

Below are local testing commands for the geo lambda functions. Run functions locally and invoke them with the `sam local invoke` command.

```bash
my-application$ sam local invoke geoGetItemsFunction --event events/geo-event-query-rectangle.json
my-application$ sam local invoke geoGetItemsFunction --event events/geo-event-query-rectangle.json
my-application$ sam local invoke geoPutItemFunction --event events/geo-event-post-item.json
my-application$ sam local invoke geoUpdateItemFunction --event events/geo-event-update-item.json
my-application$ sam local invoke geoDeleteItemFunction --event events/geo-event-delete-item.json
```

To run the local frontend, cd into the frontend file and run 
```bash
npx start run:ios
```
for the functions to work properly you will need two local api's running, a lambda api and a api gateway

README is unfinished, more details coming soon.
