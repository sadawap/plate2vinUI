# This code retrieve data from DynamoDB and show in UI in tabular format. Key is "plate".

import json
import boto3

def lambda_handler(event, context):
    # Extracting parameters from the event object
    plate = event.get("plate", "")
    
    # Initialize a DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('VehicleInfo')
    
    # Fetch the item from the DynamoDB table
    response = table.get_item(Key={'plate': plate})
    
    # Check if the item exists in the table
    if 'Item' in response:
        vehicle_info = response['Item']
        status_code = 200
    else:
        vehicle_info = {'error': 'Vehicle information not found'}
        status_code = 404

    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(vehicle_info, indent=4)
    }
