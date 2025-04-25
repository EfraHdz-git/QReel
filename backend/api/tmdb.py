import os
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

async def search_movies(query: str) -> List[Dict[str, Any]]:
    """Search for movies using TMDb API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": query,
                "language": "en-US",
                "include_adult": "false"
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

async def search_by_actor(actor_name: str) -> List[Dict[str, Any]]:
    """Search for movies by actor name"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/search/person",
            params={
                "api_key": TMDB_API_KEY,
                "query": actor_name,
                "language": "en-US"
            }
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])

        if not results:
            return []

        actor_id = results[0]["id"]

        response = await client.get(
            f"{BASE_URL}/person/{actor_id}/movie_credits",
            params={
                "api_key": TMDB_API_KEY,
                "language": "en-US"
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("cast", [])

def extract_official_trailer(videos: List[Dict[str, Any]]) -> Optional[str]:
    """Return the YouTube URL of the official trailer (if available)"""
    for video in videos:
        if (
            video.get("type") == "Trailer"
            and video.get("site") == "YouTube"
            and video.get("official", False)
        ):
            return f"https://www.youtube.com/watch?v={video.get('key')}"
    return None

async def get_movie_details(movie_id: int) -> Dict[str, Any]:
    """Get detailed information about a movie"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/movie/{movie_id}",
            params={
                "api_key": TMDB_API_KEY,
                "language": "en-US",
                "append_to_response": "credits,images,keywords,videos,release_dates"
            }
        )
        response.raise_for_status()
        movie_data = response.json()

        # Get keywords
        keyword_response = await client.get(
            f"{BASE_URL}/movie/{movie_id}/keywords",
            params={"api_key": TMDB_API_KEY}
        )
        keywords = keyword_response.json().get("keywords", [])

        # Extract trailer
        trailer_url = extract_official_trailer(movie_data.get("videos", {}).get("results", []))

        return {
            "id": movie_data["id"],
            "title": movie_data["title"],
            "poster_path": movie_data.get("poster_path"),
            "backdrop_path": movie_data.get("backdrop_path"),
            "overview": movie_data["overview"],
            "release_date": movie_data.get("release_date"),
            "runtime": movie_data.get("runtime"),
            "genres": [genre["name"] for genre in movie_data.get("genres", [])],
            "vote_average": movie_data.get("vote_average"),
            "cast": [
                {
                    "name": cast["name"],
                    "character": cast["character"],
                    "profile_path": cast["profile_path"]
                }
                for cast in movie_data.get("credits", {}).get("cast", [])[:10]
            ],
            "crew": [
                {
                    "name": crew["name"],
                    "job": crew["job"],
                    "profile_path": crew["profile_path"]
                }
                for crew in movie_data.get("credits", {}).get("crew", [])
                if crew["job"] in ["Director", "Producer", "Screenplay", "Writer"]
            ],
            "budget": movie_data.get("budget"),
            "revenue": movie_data.get("revenue"),
            "keywords": keywords,
            "trailer_url": trailer_url  # ✅ Include trailer here
        }

async def get_movie_quotes(movie_id: int) -> List[Dict[str, str]]:
    """Placeholder for movie quotes (not available in TMDb)"""
    return [{"quote": "Sample quote", "character": "Character name", "context": "Scene description"}]
