import json
import boto3
import logging
import traceback
from typing import List
from services.OMDBClient import get_omdb_client
import asyncio
from services.chatgpt import get_movie_recommendations

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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

def get_secret():
    secret_name = "prod/MovieTherapy/apiKeys"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logger.error("Error retrieving secret: %s", str(e))
        raise e
    
    return json.loads(get_secret_value_response["SecretString"])

app_secrets = get_secret()
openai_api_key = app_secrets.get("OPENAI_API_KEY")
omdb_api_key = app_secrets.get("OMDB_API_KEY")

async def enrich_movie_data(movie_list: List[dict]) -> List[dict]:
    # logger.info("Enriching movie data for %d movies", len(movie_list))
    omdb_client = get_omdb_client(omdb_api_key)

    async def enrich_one(movie):
        logger.info("Fetching data for movie: %r", movie)
        data = await omdb_client.fetch_movie_async(movie["imdb_id"])
        data["commentary"] = movie["commentary"]
        return data

    tasks = [enrich_one(movie) for movie in movie_list]

    enriched_movie_list = await asyncio.gather(*tasks)
    return enriched_movie_list

def handle_chat_post(event):
    body = json.loads(event.get("body") or "{}")
    prompt = body.get("prompt")


    recommended = get_movie_recommendations(prompt)

    logger.info("Recommended movies: %s", recommended)

    loop = asyncio.get_event_loop()
    enriched = loop.run_until_complete(enrich_movie_data(recommended["movies"]))

    return {
        "movies": enriched,
        "introduction": recommended["introduction"]
    }

def handle_hello(method):
    if method == "GET":
        logger.info("Received GET request on /hello")
        return make_response(200, {"message": "Hello, World!"})
    else:
        return make_response(405, {"error": "Method Not Allowed"})

def handle_chat(method, event):
    if method == "POST":
        output = handle_chat_post(event)
        logger.info("Response generated successfully")
        return make_response(200, {"response": output})
    else:
        return make_response(405, {"error": "Method Not Allowed"})

def lambda_handler(event, context):
    path = (event.get("path") or "/").rstrip("/") or "/"
    method = (event.get("httpMethod") or "GET").upper()

    try:
        if method == "OPTIONS":
            return make_response(204, "No Content")
        if path == "/hello":
            return handle_hello(method)
        elif path == "/chat":
            return handle_chat(method, event)
        else:
            return make_response(404, {"error": "Not Found"})
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        logger.error("Stack trace:\n%s", traceback.format_exc())
        return make_response(500, {"error": str(e)})