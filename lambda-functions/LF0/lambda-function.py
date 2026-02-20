import json

def lambda_handler(event, context):
    """
    LF0: Receives API Gateway request, forwards to Lex, returns response.
    For now, returns a boilerplate response.
    """
    print("Event received:", json.dumps(event))
    
    # Extract message from request body
    body = json.loads(event.get('body', '{}'))
    user_message = body.get('messages', [{}])[0].get('unstructured', {}).get('text', '')
    
    # TODO (Part 4): Integrate Lex call here
    bot_response = "I'm still under development. Please come back later."
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({
            'messages': [{
                'type': 'unstructured',
                'unstructured': {
                    'text': bot_response
                }
            }]
        })
    }