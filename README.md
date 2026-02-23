# Dining Concierge Chatbot
### Cloud Computing and Big Data – Spring 2026 | Assignment 1

A serverless, microservice-driven dining concierge chatbot built on AWS. The chatbot collects user preferences through natural conversation and sends personalized restaurant suggestions via email.

## Live Demo
The frontend was hosted on AWS S3 as a static website during 
the assignment period.

Frontend URL (no longer active post-submission):
[Chatbot](http://dining-concierge-yangzheng-2026.s3-website-us-east-1.amazonaws.com)

---

## Architecture

```
User → S3 (Frontend) → API Gateway → Lambda (LF0) → Amazon Lex → Lambda (LF1) → SQS (Q1)
                                                                                      ↓
                                                                              Lambda (LF2)
                                                                            ↙           ↘
                                                                      OpenSearch      DynamoDB
                                                                            ↘           ↙
                                                                              SES (Email)
```

---

## Features

- 💬 Natural language chat interface hosted on AWS S3
- 🤖 Amazon Lex chatbot with 5 intents
- 🍽️ Restaurant suggestions from 1,300+ Manhattan restaurants
- 📧 Email delivery of personalized recommendations
- 🔁 Returning user support — remembers previous searches by email

---

## Tech Stack

| Service | Purpose |
|---|---|
| **AWS S3** | Static frontend hosting |
| **API Gateway** | REST API endpoint |
| **AWS Lambda** | Serverless compute (LF0, LF1, LF2) |
| **Amazon Lex** | NLP chatbot engine |
| **Amazon SQS** | Message queue (Q1) |
| **Amazon DynamoDB** | Restaurant data + user state storage |
| **Amazon OpenSearch** | Restaurant search by cuisine |
| **Amazon SES** | Email delivery |
| **Yelp Places API** | Restaurant data source |

---

## Repository Structure

```
dining-concierge-chatbot/
├── frontend/                   # Static chat UI (S3 hosted)
│   ├── chat.html
│   └── assets/
│       ├── css/
│       └── js/
│           ├── chat.js
│           └── sdk/            # API Gateway generated SDK
├── lambda-functions/
│   ├── LF0/                    # API Gateway → Lex passthrough
│   │   └── lambda_function.py
│   ├── LF1/                    # Lex code hook + business logic
│   │   └── lambda_function.py
│   └── LF2/                    # SQS queue worker + email sender
│       └── lambda_function.py
├── other-scripts/
│   ├── yelp_scraper.py         # Scrapes Yelp data into DynamoDB
│   └── load_opensearch.py      # Loads restaurant data into OpenSearch
├── swagger/
│   └── swagger.yaml            # API specification
└── README.md
```

---

## Chatbot Intents

| Intent | Trigger | Response |
|---|---|---|
| `GreetingIntent` | "Hello", "Hi" | "Welcome! Have you used our service before?" |
| `ThankYouIntent` | "Thank you", "Thanks" | "You're welcome!" |
| `DiningSuggestionsIntent` | "I need restaurant suggestions" | Collects 5 slots and sends email |
| `NewUserIntent` | "No", "Never used before" | Guides to new search |
| `ReturningUserIntent` | "Yes", "I've used before" | Retrieves previous search by email |

---

## DiningSuggestionsIntent Slots

| Slot | Type | Prompt |
|---|---|---|
| Location | AMAZON.AlphaNumeric | "What city or area are you looking to dine in?" |
| Cuisine | CuisineType (custom) | "What cuisine would you like to try?" |
| DiningTime | AMAZON.Time | "What time would you like to dine?" |
| NumberOfPeople | AMAZON.Number | "How many people are in your party?" |
| Email | AMAZON.EmailAddress | "What's your email address?" |

---

## Example Interaction

```
User: Hello
Bot:  Welcome! Have you used our service before?

User: No
Bot:  No problem! Say 'I need restaurant suggestions' to get started!

User: I need restaurant suggestions
Bot:  What city or area are you looking to dine in?

User: Manhattan
Bot:  What cuisine would you like to try?

User: Japanese
Bot:  How many people are in your party?

User: 2
Bot:  What time would you like to dine?

User: 7pm
Bot:  What's your email address?

User: user@email.com
Bot:  You're all set! Expect restaurant suggestions shortly!

--- (Email received) ---

Hello! Here are my Japanese restaurant suggestions for 2 people, for today at 7pm:
1. Sushi Nakazawa, located at 23 Commerce St
2. Jin Ramen, located at 3183 Broadway
3. Nikko, located at 1280 Amsterdam Ave.
Enjoy your meal!
```

---

## Extra Credit — Returning User State

The chatbot remembers previous searches using email as a unique identifier stored in DynamoDB.

```
User: Hello
Bot:  Welcome! Have you used our service before?

User: Yes
Bot:  Please provide your email.

User: user@email.com
Bot:  Welcome back! Last time you searched for Japanese restaurants 
      in Manhattan for 2 people. Want similar suggestions again?

User: Yes
Bot:  Sending suggestions to user@email.com now!
```

---

## Setup

### Prerequisites
- AWS Account with appropriate IAM permissions
- AWS CLI configured
- Python 3.12+
- Yelp Fusion API key

### Environment Variables

**LF1:**
| Key | Value |
|---|---|
| `SQS_QUEUE_URL` | Your SQS Q1 URL |

**LF2:**
| Key | Value |
|---|---|
| `SQS_QUEUE_URL` | Your SQS Q1 URL |
| `OPENSEARCH_ENDPOINT` | Your OpenSearch domain endpoint |
| `OPENSEARCH_USER` | OpenSearch master username |
| `OPENSEARCH_PASS` | OpenSearch master password |
| `SENDER_EMAIL` | SES verified email address |

**LF0:**
| Key | Value |
|---|---|
| `LEX_BOT_ID` | Your Lex bot ID |
| `LEX_BOT_ALIAS_ID` | Your Lex bot alias ID |

### Data Setup
```bash
# Install dependencies
pip install requests boto3

# Scrape Yelp data into DynamoDB
export YELP_API_KEY="your_key"
python other-scripts/yelp_scraper.py

# Load data into OpenSearch
export OPENSEARCH_USER="admin"
export OPENSEARCH_PASS="your_password"
python other-scripts/load_opensearch.py
```

---

## Supported Cuisines

Chinese, Italian, Japanese, Mexican, Indian, Thai, American, Mediterranean

---

## Author
Yang Zheng — NYU Cloud Computing and Big Data (Assignment 1), Spring 2026
