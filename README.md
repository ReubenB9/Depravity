# Depravity - Social App

This application is based around two NoSQL databases, an authentication pool, live features using MQTT protocol and following security best practices being implemented with an AWS backend and a basic react-native frontend. Repo Structure: 

- `backend` - Code for the application's Lambda functions
- `events` - Invocation events that you can use to invoke the function
- `frontend` - Code for application UI
- `env.json` - A template for env.json file, must be edited with user env variables
- `template.yaml` - A template that defines the application's AWS resources

## Database Structures
The backend is structured into two NoSQL databasesm, one is a DynamoDB table to store user and group information (put into the same table for cost optimization), and the other is a DynamoDB geo table utilizing the DynamoDB Geo library, which uses a geohash to make the storing and lookup of location-based data more efficient. The first table is structured This second table is specifically designed for holding pin locations to be displayed efficiently on the live map interface. 

### General Information Table (Single-Table Design)

| PK | SK | Other Attributes |
| :--- | :--- | :--- |
| `USER#ALICE` | `PROFILE#ALICE` | `{"email": "alice@dev.com"}` |
| `GROUP#ADMIN` | `METADATA` | `{"policy": "policy"}` |

**Query Structures:**
* **Primary:** `PK = USER#123` and `SK begins_with(GROUP#)`
* **GSI (All users in a group):** `SK = GROUP#ABC` and `PK begins_with(USER#)`

### Geo DynamoDB Structure

| PK | SK | Other Pin Attributes |
| :--- | :--- | :--- |
| `GEOHASH` | `GROUP-USER-TIMESTAMP` | `{"description": "example"}` |

**Query Structures:** * `PK = (Coord generated Geohash)` and `SK = (unique SK within Geohash location)`

## Features and Structure

### User & Authentication
* Secure custom signup/login flow with Cognito (custom backend utilizing Python and the Boto3 SDK)
* Login API built using API Gateway, included methods for sign up, confirm sign up, login, forgot password, resend confirmation code and adding user permissions
* On Duo Cognito approval:
  * Attach user permissions policy
  * Generate user IoT permissions (policies attached directly to identity pool with dynamic permissions given based on users current group tag)
  * Permanently add users to dynamodb user base

### Group Management
* Create a group with:
  * Unique entry code for joining
  * Dynamodb for storing group metadata
* Join a group:
  * Verifies entry code
  * Adds group to users list of active 'groups'
* Invite other users via sharing code or link
* Dynamic user ability to switch between groups and securely display only current group information

### Live Map Data
## Pipeline
* User data is published to group topics
* topic/*GroupName*/location data routed through a lambda function and sent to location services for processing
* Users subscribe to AppSync via GraphQL to recieve live user location data

## Frontend
* Map implemented using react open source Leaflet library
* Dynamic tile based interface with pins and other user locations displayed
  
## Testing and Development
Complete AWS serverless backend utilizing AWS services, frontend to be hosted through the App Store and Google Play Store. Instructions included below for local deployment using AWS SAM and react native expo. SAM has built in deployment functions for moving to a live env. For local deployment you will need Node.js, AWS CLI, SAM CLI, Docker and React-Native-Expo.

### Local Deployment
To build and deploy the application for the first time locally, clone the repository and create your own `env.json` file. Example `env.json` file is included in the repo

Build the source of your application:
```bash
sam build
```

You can locally invoke commands using Docker instances of AWS databases, or you can deploy databases to test the Lambda functions locally in a live environment. If a Lambda function relies on invoking other Lambda functions locally, start local instances of Lambda (ensure the port is correct in your local `env.json`):
```bash
sam local start-lambda
```

### Geo Lambda Testing
Run functions locally and invoke them with the `sam local invoke` command. Below are local testing commands for the geo Lambda functions:

```bash
sam local invoke geoGetItemsFunction --event events/geo-event-query-rectangle.json
sam local invoke geoGetItemsFunction --event events/geo-event-query-rectangle.json
sam local invoke geoPutItemFunction --event events/geo-event-post-item.json
sam local invoke geoUpdateItemFunction --event events/geo-event-update-item.json
sam local invoke geoDeleteItemFunction --event events/geo-event-delete-item.json
```

### Frontend Development
To run the local frontend, navigate into the frontend directory and run:
```bash
npx react-native run-ios
```
*Note: For the functions to work properly in local simulation, you will need two local APIs running: a Lambda API (sam local start-lambda) and an API Gateway (sam local start-api*

### Features in progress
* Group trip planning feature orchestrated by an ai model including user surveying, ai generated personalized recommendations and rank choice voting system (include rate limiting and real time usage tracking)
* User location processing for custom geo fences
* Live app data metrics with Cloudwatch
