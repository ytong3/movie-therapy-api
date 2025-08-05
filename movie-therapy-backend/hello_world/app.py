import json
import boto3
import logging
import instructor
from pydantic import BaseModel
from openai import OpenAI
from typing import List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Movie(BaseModel):
    title: str
    year: int
    imdb_id: str
    commentary: str

class MovieList(BaseModel):
    movies: List[Movie]

def make_response(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    }

def get_openai_key(secret_name="openai/api-key"):
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    secret_dict = json.loads(response["SecretString"])
    return secret_dict["OPENAI_API_KEY"]

openai_api_key = get_openai_key()

def get_movie_recommendations(prompt):
    
    logger.info("Prompt received: %s", prompt)

    client = instructor.from_provider("openai/gpt-4o", api_key=openai_api_key)

    movies = client.chat.completions.create(
        response_model=MovieList,
        messages=[
            {
                "role": "system", 
                "content": "You are a helpful film Sommelier. \
                            You recommend movies based on user's moods and sometimes a commentary of what's going on for them. \
                            You are also a therapist. So you recommend 5 movies that make them feel they are seen and felt. \
                            When you recommend movies, you also provide a brief commentary on why you chose each movie. \
                            Format your response as a JSON object with a 'movies' key containing an array of movie objects. \
                            Each movie object should have 'title', 'year', 'imdb_id' and 'commentary' keys."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        max_tokens=300,
        temperature=0.7
    )

    return movies.model_dump()



def lambda_handler(event, context):
    # logger.info("Received event: %s", json.dumps(event))
    path = event.get("path", "/")
    method = event.get("httpMethod", "GET").upper()
    if path == "/hello":
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Hello, World!"})
        }
    elif path == "/chat":
        if method == "OPTIONS":
            return make_response(204, "No Content")
        if method == "POST":
            try:

                body = json.loads(event.get("body") or "{}")

                prompt = body.get("prompt", "default fallback prompt")

                output = get_movie_recommendations(prompt)
                
                logger.info("Response generated successfully")
                
                return make_response(200, {"response": output})
            
            except Exception as e:
                return make_response(500, {"error": str(e)})
        else:
            return make_response(405, {"error": "Method Not Allowed"})