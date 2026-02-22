import json
import boto3
import os
import random
import requests
from requests.auth import HTTPBasicAuth

sqs = boto3.client('sqs', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
ses = boto3.client('ses', region_name='us-east-1')

SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL', 'YOUR_SQS_QUEUE_URL')
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT', 'https://YOUR_DOMAIN.es.amazonaws.com')
OPENSEARCH_USER = os.environ.get('OPENSEARCH_USER', 'master')
OPENSEARCH_PASS = os.environ.get('OPENSEARCH_PASS', 'password')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'your-verified@email.com')

table = dynamodb.Table('yelp-restaurants')


def lambda_handler(event, context):
    print("LF2 triggered")
    
    # Pull message from SQS
    response = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )
    
    messages = response.get('Messages', [])
    if not messages:
        print("No messages in queue")
        return {'statusCode': 200, 'body': 'No messages'}
    
    message = messages[0]
    receipt_handle = message['ReceiptHandle']
    body = json.loads(message['Body'])
    
    print(f"Processing: {body}")
    
    cuisine = body.get('cuisine', 'Italian')
    email = body.get('email')
    dining_time = body.get('diningTime', '')
    num_people = body.get('numberOfPeople', '2')
    
    # Search OpenSearch for restaurants by cuisine
    restaurant_ids = search_opensearch(cuisine)
    
    if not restaurant_ids:
        print(f"No restaurants found for cuisine: {cuisine}")
        sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)
        return {'statusCode': 200, 'body': 'No restaurants found'}
    
    # Pick 3 random restaurants
    picked_ids = random.sample(restaurant_ids, min(3, len(restaurant_ids)))
    
    # Fetch details from DynamoDB
    restaurants = []
    for rid in picked_ids:
        resp = table.get_item(Key={'BusinessID': rid})
        if 'Item' in resp:
            restaurants.append(resp['Item'])
    
    # Send email
    if restaurants and email:
        send_email(email, cuisine, dining_time, num_people, restaurants)
    
    # Delete message from queue
    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)
    
    return {'statusCode': 200, 'body': 'Processed successfully'}


def search_opensearch(cuisine):
    url = f"{OPENSEARCH_ENDPOINT}/restaurants/_search"
    query = {
        "query": {
            "match": {"Cuisine": cuisine}
        },
        "size": 50
    }
    
    r = requests.get(
        url, json=query,
        auth=HTTPBasicAuth(OPENSEARCH_USER, OPENSEARCH_PASS)
    )
    
    hits = r.json().get('hits', {}).get('hits', [])
    return [hit['_source']['RestaurantID'] for hit in hits]


def send_email(to_email, cuisine, dining_time, num_people, restaurants):
    restaurant_list = ""
    for i, r in enumerate(restaurants, 1):
        restaurant_list += f"{i}. {r.get('Name', 'Unknown')}, located at {r.get('Address', 'N/A')}\n"
    
    body = (
        f"Hello! Here are my {cuisine} restaurant suggestions for "
        f"{num_people} people, for today at {dining_time}:\n\n"
        f"{restaurant_list}\n"
        "Enjoy your meal!"
    )
    
    ses.send_email(
        Source=SENDER_EMAIL,
        Destination={'ToAddresses': [to_email]},
        Message={
            'Subject': {'Data': f'Your {cuisine} Restaurant Suggestions!'},
            'Body': {'Text': {'Data': body}}
        }
    )
    print(f"Email sent to {to_email}")