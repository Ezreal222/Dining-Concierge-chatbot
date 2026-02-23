import json
import boto3
import os
from datetime import datetime

sqs = boto3.client('sqs', region_name='us-east-1')
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL', 'YOUR_SQS_QUEUE_URL')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('user-last-search')

def lambda_handler(event, context):
    print("LF1 Event:", json.dumps(event))
    
    intent_name = event['sessionState']['intent']['name']
    invocation_source = event['invocationSource']  
    
    if intent_name == 'GreetingIntent':
        return close(event, "Welcome! Have you used our service before?")
    
    elif intent_name == 'ThankYouIntent':
        return close(event, "You're welcome!")
    
    elif intent_name == 'DiningSuggestionsIntent':
        return handle_dining_suggestions(event, invocation_source)
    
    elif intent_name == 'ReturningUserIntent':
        return handle_returning_user(event, invocation_source)
    
    elif intent_name == 'NewUserIntent':
        return close(event,
            "No problem! How can I help you today?  "
            "Say 'I need restaurant suggestions' to get started!"
        )
    
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
            save_last_search(email, location, cuisine, dining_time, num_people)
            return close(
                event,
                f"You're all set! Expect restaurant suggestions for {cuisine} cuisine at {dining_time} for {num_people} people. "
                f"I'll send them to {email} shortly. Have a great day!"
            )
    
    return delegate(event)

def handle_returning_user(event, invocation_source):
    slots = event['sessionState']['intent']['slots']
    email = get_slot(slots, 'Email')
    confirm = get_slot(slots, 'ConfirmSuggestion')

    # Step 1 — Email not provided yet, wait for it
    if not email:
        return delegate(event)

    # Step 2 — Email provided, check DynamoDB
    if email and not confirm:
        try:
            result = table.get_item(Key={'Email': email})
            
            if 'Item' in result:
                last = result['Item']
                # Store last search in session for later use
                return elicit_slot(
                    event,
                    'ConfirmSuggestion',
                    f"Welcome back! Last time you searched for {last['cuisine']} "
                    f"restaurants in {last['location']} for {last['numberOfPeople']} people. "
                    f"Want similar suggestions again?"
                )
            else:
                return close(event,
                    f"I don't have any previous searches for {email}. "
                    f"Would you like to make a new search? Just say 'I need restaurant suggestions'!"
                )
        except Exception as e:
            print(f"Error looking up previous search: {e}")
            return close(event, "Sorry, I couldn't retrieve your previous search. Please try a new search.")

    # Step 3 — User confirms yes or no
    if confirm:
        if confirm.lower() in ['yes', 'yeah', 'sure', 'yep', 'ok', 'okay']:
            try:
                result = table.get_item(Key={'Email': email})
                if 'Item' in result:
                    last = result['Item']
                    push_to_sqs(
                        last['location'],
                        last['cuisine'],
                        last['diningTime'],
                        last['numberOfPeople'],
                        email
                    )
                    return close(event,
                        f"Sending suggestions to {email} now! Enjoy your meal!"
                    )
            except Exception as e:
                print(f"Error: {e}")
                return close(event, "Sorry something went wrong. Please try again.")
        
        else:  # User says No
            return close(event,
                "No problem! Just say 'I need restaurant suggestions' "
                "and I'll help you find something new!"
            )
    
    return delegate(event)

def save_last_search(email, location, cuisine, dining_time, num_people):
    try:
        table.put_item(Item={
            'Email': email,
            'location': location,
            'cuisine': cuisine,
            'diningTime': dining_time,
            'numberOfPeople': num_people,
            'timestamp': datetime.now().isoformat()
        })
        print(f"Saved last search for {email}")
    except Exception as e:
        print(f"Error saving last search: {e}")


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

'''
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
'''
def elicit_slot(event, slot_to_elicit, message):
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit
            },
            'intent': {
                'name': event['sessionState']['intent']['name'],
                'slots': event['sessionState']['intent']['slots'],
                'state': 'InProgress'
            }
        },
        'messages': [{'contentType': 'PlainText', 'content': message}]
    }

'''
# Informs Amazon Lex to delegate the request to the next Lambda function
def delegate(event):
    return {
        'sessionState': {
            'dialogAction': {'type': 'Delegate'},
            'intent': event['sessionState']['intent']
        }
    }
'''
def delegate(event):
    return {
        'sessionState': {
            'dialogAction': {'type': 'Delegate'},
            'intent': {
                'name': event['sessionState']['intent']['name'],
                'slots': event['sessionState']['intent']['slots'],
                'state': 'InProgress'
            }
        }
    }