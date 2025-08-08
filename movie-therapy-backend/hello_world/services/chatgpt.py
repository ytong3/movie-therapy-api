import logging
from pydantic import BaseModel
from typing import List
import instructor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Movie(BaseModel):
    imdb_id: str
    commentary: str

class MovieList(BaseModel):
    movies: List[Movie]
    introduction: str

def get_openai_client():
    from app import openai_api_key  # local import to avoid circular dependency
    return instructor.from_provider("openai/gpt-4o", api_key=openai_api_key)

def get_movie_recommendations(prompt) -> dict:
    logger.info("Prompt received: %s", prompt)

    gpt_client = get_openai_client()

    movie_list = gpt_client.chat.completions.create(
        response_model=MovieList,
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are a helpful film Sommelier. "
                    "You recommend movies based on user's moods and sometimes a commentary of what's going on for them. "
                    "You are also a therapist. So you recommend 5 movies that make them feel they are seen and felt. "
                    "When you recommend movies, first provide a intro to validate the users and feeling and introduce the movies, "
                    "you then provide a brief commentary on why you chose each movie. "
                    "Format your response as a JSON object with a 'introduction' key containing the introduction, "
                    "and 'movies' key containing an array of movie objects. "
                    "Each movie object should have 'imdb_id' and 'commentary' keys."
                    "Make sure the imdb_id is correct and the commentary is insightful."
                )
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        max_tokens=500,
        temperature=0.8,
    )
    return movie_list.model_dump()