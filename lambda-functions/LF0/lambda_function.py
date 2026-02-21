import json
import boto3
import os
import uuid

lex = boto3.client('lexv2-runtime', region_name='us-east-1')

BOT_ID = os.environ.get('LEX_BOT_ID', 'YOUR_BOT_ID')
BOT_ALIAS_ID = os.environ.get('LEX_BOT_ALIAS_ID', 'TSTALIASID')  
LOCALE_ID = 'en_US'

def lambda_handler(event, context):
    print("LF0 Event:", json.dumps(event))
    
    body = json.loads(event.get('body', '{}'))
    messages = body.get('messages', [])
    
    if not messages:
        return build_response(400, {'error': 'No messages provided'})
    # text sent to Lex
    user_message = messages[0].get('unstructured', {}).get('text', '')
    
    '''
    # Use session ID from query params or generate one
    session_id = event.get('queryStringParameters', {}) or {}
    session_id = session_id.get('sessionId', str(uuid.uuid4()))
    '''
    session_id = event.get('queryStringParameters') or {}
    session_id = session_id.get('sessionId', 'default-session')
    
    # Call Lex to process the user's message
    try:
        lex_response = lex.recognize_text(
            botId=BOT_ID,
            botAliasId=BOT_ALIAS_ID,
            localeId=LOCALE_ID,
            sessionId=session_id,
            text=user_message
        )
        
        bot_messages = lex_response.get('messages', [])
        bot_text = bot_messages[0]['content'] if bot_messages else "I didn't understand that."
        
        return build_response(200, {
            'messages': [{
                'type': 'unstructured',
                'unstructured': {'text': bot_text}
            }]
        })
    
    except Exception as e:
        print(f"Error calling Lex: {e}")
        return build_response(500, {'error': str(e)})


def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(body)
    }