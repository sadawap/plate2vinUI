import json
import boto3
import requests
from decimal import Decimal
from datetime import datetime

def convert_timestamp(epoch_time):
    return datetime.fromtimestamp(epoch_time).strftime('%m/%d/%Y')

def fetch_image_path(s3_bucket, scan_image_id):
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket=s3_bucket)
    for obj in response.get('Contents', []):
        if obj['Key'] == f'images/{scan_image_id}.jpg':  # Adjust the path and extension based on your S3 setup
            return f"s3://{s3_bucket}/{obj['Key']}"
    return None

def lambda_handler(event, context):
    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    json_file_name = event['Records'][0]['s3']['object']['key']
    print(f"S3 Bucket: {s3_bucket}, JSON File Name: {json_file_name}")

    s3_client = boto3.client('s3')
    dynamodb_client = boto3.resource('dynamodb')
    dynamodb_table = dynamodb_client.Table('datachange')

    api_url = 'https://platetovin.com/api/convert'
    headers = {
        'Authorization': 'FBsYCtb1B7L3Qqp',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    try:
        # Get the JSON object from S3
        response = s3_client.get_object(Bucket=s3_bucket, Key=json_file_name)
        json_data = json.loads(response['Body'].read().decode('utf-8'), parse_float=Decimal)

        data = []
        for item in json_data:
            country_split = item['country'].split('/')
            state = country_split[1] if len(country_split) > 1 else None
            plate_number = item.get('plate_number')

            print(f"Processing item with state: {state}, plate_number: {plate_number}")

            if state and plate_number:
                # Request to Plate to VIN API
                payload = {
                    "state": state,
                    "plate": plate_number
                }
                api_response = requests.post(api_url, headers=headers, json=payload)
                api_data = api_response.json()

                plate2vin = api_data.get('vin', {})

                # Convert side_data timestamps
                side_data = json.loads(item.get('side_data', '{}'))
                front_entry_timestamp = None
                if 'timestamps' in side_data and 'front_entry' in side_data['timestamps']:
                    front_entry_timestamp = side_data['timestamps']['front_entry']
                    converted_front_entry = convert_timestamp(front_entry_timestamp) if front_entry_timestamp is not None else None
                if 'timestamps' in side_data:
                    timestamps = side_data['timestamps']
                    converted_timestamps = {key: (convert_timestamp(value) if value is not None else None) for key, value in timestamps.items() if key != 'post_processing_time'}
                    side_data['timestamps'] = converted_timestamps

                # Fetch image path from S3
                image_path = fetch_image_path(s3_bucket, item['scan_image_id'])
                if image_path is None:
                    image_path = 'null'  # Set to 'null' if no image path found

                combined_item = {
                    'dealership_id': str(item['dealership_id']),
                    'scan_image_id': str(item['scan_image_id']),
                    'plate_number': str(item['plate_number']),
                    'country': str(item['country']),
                    'state': str(state),
                    'entry_id': str(item['entry_id']),
                    'entry_time': str(item['entry_time']),
                    'lane_name': str(item['lane_name']),
                    'front_entry': str(converted_front_entry) if converted_front_entry else '',
                    'side_data': json.dumps(side_data),
                    'image_path': image_path  # Add the image_path field
                }

                combined_item.update(plate2vin)
                data.append(combined_item)

        # Batch write items to DynamoDB
        with dynamodb_table.batch_writer() as batch:
            for item in data:
                if item.get('vin') and item.get('front_entry'):  # Ensure vin and front_entry are not empty
                    batch.put_item(Item=item)
                else:
                    print(f"Skipping item with missing vin or front_entry: {item}")

        return {
            'statusCode': 200,
            'body': 'Data successfully loaded into DynamoDB.'
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }
