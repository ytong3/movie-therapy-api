import json
import boto3
from openai import OpenAI


def get_openai_key(secret_name="openai/api-key"):
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    secret_dict = json.loads(response["SecretString"])
    return secret_dict["OPENAI_API_KEY"]

openai_api_key = get_openai_key()

def lambda_handler(event, context):

    path = event.get("path", "/")
    method = event.get("httpMethod", "GET").upper()
    if path == "/hello":
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Hello, World!"})
        }
    elif path == "/chat":
        if method == "GET":
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "This is a chat endpoint. Use POST to send messages."})
            }
        # Handle POST /chat
        elif method == "POST":
            try:
                body = json.loads(event.get("body") or "{}")
                prompt = body.get("prompt", "default fallback prompt")
                
                client = OpenAI(api_key=openai_api_key)

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a helpful film Sommelier. \
                                        You recommend movies based on user's moods and sometimes a commentary of what's going on for them. \
                                        You are also a therapist. So you recommend 5 movies that make them feel they are seen and felt. \
                                        When you recommend movies, you also provide a brief commentary on why you chose each movie. \
                                        Format your response as a JSON object with a 'movies' key containing an array of movie objects. \
                                        Each movie object should have 'title', 'year', and 'commentary' keys."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    max_tokens=300,
                    temperature=0.7
                )

                output = response.choices[0].message.content.strip()

                return {
                    "statusCode": 200,
                    "body": json.dumps({"response": output})
                }
            except Exception as e:
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": str(e)})
                }
        else:
            return {
                "statusCode": 405,
                "body": json.dumps({"error": "Method not allowed"})
            }





