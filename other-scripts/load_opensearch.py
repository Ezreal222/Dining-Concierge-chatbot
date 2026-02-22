'''
This script loads the data from the DynamoDB table into the OpenSearch index.
so LF2 can query restaurants by cuisine. It creates the index and bulk-loads documents.
'''

import boto3
import json
import requests
from requests.auth import HTTPBasicAuth
from decimal import Decimal
import os

OPENSEARCH_ENDPOINT = "https://search-restaurants-rvohhm6ykvzhc3quzibevfmc4m.us-east-1.es.amazonaws.com"
MASTER_USER = os.getenv('MASTER_USER')
MASTER_PASS = os.getenv('MASTER_PASS')
INDEX = "restaurants"

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')

def create_index():
    url = f"{OPENSEARCH_ENDPOINT}/{INDEX}"
    body = {
        "mappings": {
            "properties": {
                "RestaurantID": {"type": "keyword"},
                "Cuisine": {"type": "keyword"}
            }
        }
    }
    r = requests.put(url, json=body, auth=HTTPBasicAuth(MASTER_USER, MASTER_PASS))
    print("Create index:", r.status_code, r.text)

def load_data():
    # Scan all items from DynamoDB
    response = table.scan()
    items = response['Items']
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response['Items'])
    
    print(f"Loading {len(items)} items into OpenSearch...")
    
    for item in items:
        doc = {
            "RestaurantID": item['BusinessID'],
            "Cuisine": item.get('Cuisine', '')
        }
        url = f"{OPENSEARCH_ENDPOINT}/{INDEX}/_doc/{item['BusinessID']}"
        r = requests.put(url, json=doc, auth=HTTPBasicAuth(MASTER_USER, MASTER_PASS))
        if r.status_code not in [200, 201]:
            print(f"Error: {r.text}")
    
    print("Done loading data!")

if __name__ == '__main__':
    create_index()
    load_data()