import requests
import boto3
import json
import time
from datetime import datetime
from decimal import Decimal
import os

YELP_API_KEY = os.getenv('YELP_API_KEY')
YELP_HEADERS = {"Authorization": f"Bearer {YELP_API_KEY}"}
YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')

CUISINES = ['Chinese', 'Italian', 'Japanese', 'Mexican', 'Indian', 'Thai', 'American']
# Tracks business IDs to avoid duplicates across cuisines.
seen_ids = set()

def search_restaurants(cuisine, location='Manhattan, NY', limit=50, offset=0):
    params = {
        'term': f'{cuisine} restaurants',
        'location': location,
        'limit': limit,
        'offset': offset,
        'categories': 'restaurants'
    }
    response = requests.get(YELP_SEARCH_URL, headers=YELP_HEADERS, params=params)
    return response.json().get('businesses', [])

def save_restaurant(business, cuisine):
    if business['id'] in seen_ids:
        return False
    seen_ids.add(business['id'])
    
    address_parts = business.get('location', {}).get('display_address', [])
    zip_code = business.get('location', {}).get('zip_code', '')
    coordinates = business.get('coordinates', {})
    
    item = {
        'BusinessID': business['id'],
        'Name': business.get('name', ''),
        'Address': ', '.join(address_parts),
        'Coordinates': {
            'Latitude': Decimal(str(coordinates.get('latitude', 0))),
            'Longitude': Decimal(str(coordinates.get('longitude', 0)))
        },
        'NumberOfReviews': business.get('review_count', 0),
        'Rating': Decimal(str(business.get('rating', 0))),
        'ZipCode': zip_code,
        'Cuisine': cuisine,
        'insertedAtTimestamp': datetime.now().isoformat()
    }
    
    table.put_item(Item=item)
    return True

def scrape_all():
    for cuisine in CUISINES:
        print(f"\nScraping {cuisine} restaurants...")
        count = 0
        for offset in range(0, 200, 50):
            businesses = search_restaurants(cuisine, offset=offset)
            if not businesses:
                break
            for b in businesses:
                if save_restaurant(b, cuisine):
                    count += 1
            time.sleep(0.5)  # Rate limiting
        print(f"  Saved {count} {cuisine} restaurants")
    
    print(f"\nTotal unique restaurants: {len(seen_ids)}")

if __name__ == '__main__':
    scrape_all()