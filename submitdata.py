# This code submit the data from UI to dynamoDB

import json
import requests
import boto3
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    # Extracting parameters from the event object
    state = event.get("state", "")
    plate = event.get("plate", "")
    
    # Check if the httpMethod is in the event and handle the OPTIONS preflight request
    if 'httpMethod' in event and event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps({'message': 'CORS preflight check.'})
        }

    # Define the API endpoint and payload
    url = 'https://platetovin.com/api/convert'
    payload = {
        "state": state,
        "plate": plate
    }
    headers = {
        'Authorization': 'iBVnCES3bvlUzGX',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Make the POST request
    response = requests.post(url, json=payload, headers=headers)
    
    # Check the response status and return the appropriate response
    if response.status_code == 200:
        data = response.json()
        
        # Extract vehicle information
        vehicle_info = data.get('vin', {})
        
        # Add state and plate information to vehicle_info
        vehicle_info['state'] = state
        vehicle_info['plate'] = plate
        
        # Initialize a DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('VehicleInfo')
        
        # Put the item into the DynamoDB table
        table.put_item(Item=vehicle_info)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps("Data has been Stored to Database", indent=4)
        }
    else:
        return {
            'statusCode': response.status_code,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps({'ERROR': 'No Vehicle data found'})
        }
