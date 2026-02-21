import json
import boto3
import os
from datetime import datetime

sqs = boto3.client('sqs', region_name='us-east-1')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL', 'YOUR_SQS_QUEUE_URL')

def lambda_handler(event, context):
    print("LF1 Event:", json.dumps(event))
    
    intent_name = event['sessionState']['intent']['name']
    invocation_source = event['invocationSource']  
    
    if intent_name == 'GreetingIntent':
        return close(event, "Hi there, how can I help?")
    
    elif intent_name == 'ThankYouIntent':
        return close(event, "You're welcome!")
    
    elif intent_name == 'DiningSuggestionsIntent':
        return handle_dining_suggestions(event, invocation_source)
    
    else:
        return close(event, "I'm not sure how to help with that.")


def handle_dining_suggestions(event, invocation_source):
    slots = event['sessionState']['intent']['slots']
    
    location = get_slot(slots, 'Location')
    cuisine = get_slot(slots, 'Cuisine')
    dining_time = get_slot(slots, 'DiningTime')
    num_people = get_slot(slots, 'NumberOfPeople')
    email = get_slot(slots, 'Email')
    
    # Validate location — for now only support Manhattan
    if location and location.lower() not in ['manhattan', 'new york', 'nyc', 'ny']:
        return elicit_slot(
            event,
            'Location',
            f"Sorry, I can only fulfill requests for Manhattan. Please enter Manhattan or a NYC neighborhood."
        )
    
    # If all slots filled, push to SQS
    if invocation_source == 'FulfillmentCodeHook':
        if all([location, cuisine, dining_time, num_people, email]):
            push_to_sqs(location, cuisine, dining_time, num_people, email)
            return close(
                event,
                f"You're all set! Expect restaurant suggestions for {cuisine} cuisine at {dining_time} for {num_people} people. "
                f"I'll send them to {email} shortly. Have a great day!"
            )
    
    return delegate(event)


def push_to_sqs(location, cuisine, dining_time, num_people, email):
    message = {
        'location': location,
        'cuisine': cuisine,
        'diningTime': dining_time,
        'numberOfPeople': num_people,
        'email': email,
        'timestamp': datetime.now().isoformat()
    }
    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(message)
    )
    print(f"Pushed to SQS: {message}")


def get_slot(slots, slot_name):
    slot = slots.get(slot_name)
    if slot and slot.get('value') and slot['value'].get('interpretedValue'):
        return slot['value']['interpretedValue']
    return None

# Informs Amazon Lex not to expect a response from the user
def close(event, message):
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {
                'name': event['sessionState']['intent']['name'],
                'state': 'Fulfilled'
            }
        },
        'messages': [{'contentType': 'PlainText', 'content': message}]
    }

# Informs Amazon Lex that the user is expected to provide a slot value in the response.
def elicit_slot(event, slot_to_elicit, message):
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit
            },
            'intent': event['sessionState']['intent']
        },
        'messages': [{'contentType': 'PlainText', 'content': message}]
    }

# Informs Amazon Lex to delegate the request to the next Lambda function
def delegate(event):
    return {
        'sessionState': {
            'dialogAction': {'type': 'Delegate'},
            'intent': event['sessionState']['intent']
        }
    }