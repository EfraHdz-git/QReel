import os
import json
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
logger = logging.getLogger(__name__)

from api.tmdb import search_movies, BASE_URL, TMDB_API_KEY

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

# Shared async HTTP client
client = httpx.AsyncClient(timeout=10.0)

# ========== Core OpenAI Request ==========
async def call_openai(messages: List[Dict[str, str]], max_tokens: int = 300, response_format: Optional[Dict] = None) -> Any:
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key is missing")
        return None

    try:
        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": max_tokens
        }
        if response_format:
            payload["response_format"] = response_format

        response = await client.post("https://api.openai.com/v1/chat/completions", headers=HEADERS, json=payload)

        if response.status_code != 200:
            logger.error(f"OpenAI API error: {response.text}")
            return None

        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"OpenAI request failed: {e}")
        return None

# ========== Search Refinement ==========
async def refine_search_query(query: str) -> Dict[str, Any]:
    prompt = f"""
A user submitted the following search query: "{query}"

Your task is to interpret this query and extract useful metadata to help a movie search engine find the best match.

The user might be:
- Searching for a movie by its exact or partial title (even misspelled)
- Naming an actor, director, or character
- Describing the plot, genre, or setting
- Quoting a line of dialogue or catchphrase
- Referring to the vibe, emotion, or visuals

Analyze and return:
1. The most likely intended movie title
2. The primary search intent: title, actor, character, dialogue, plot, or mixed
3. Corrected query if there were any typos or incomplete phrases
4. The most likely release year (if inferable)
5. Additional relevant metadata that could help disambiguate (genre, actor name, quote, etc.)

Respond strictly in this JSON format:
{{
  "refined_query": "corrected and complete query or title",
  "intent_type": "title | actor | character | plot | dialogue | mixed",
  "likely_year": "YYYY or null",
  "additional_info": "summary of key info extracted from the query"
}}
"""
    messages = [
        {"role": "system", "content": "You are a movie expert assistant helping to interpret user search queries."},
        {"role": "user", "content": prompt}
    ]

    logger.info("Refining search query with OpenAI")
    content = await call_openai(messages, max_tokens=300, response_format={"type": "json_object"})
    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse refined query JSON.")
    return {"refined_query": query, "intent_type": "title", "likely_year": None, "additional_info": ""}

# ========== Movie Match Selection ==========
async def select_best_movie_match(movies: List[Dict[str, Any]], original_query: str) -> Optional[int]:
    if not movies:
        return None

    movie_options = "\n\n".join([
        f"Movie {i+1}:\nTitle: {movie.get('title')}\nRelease Date: {movie.get('release_date')}\nOverview: {movie.get('overview')}"
        for i, movie in enumerate(movies[:10])
    ])

    prompt = f"""
User search query: "{original_query}"

You are given a list of movies (title, release year, and overview). Analyze the query and choose the **best matching movie**. Consider spelling variations, character names, famous quotes, and indirect references.

{movie_options}

Return ONLY the number (1-{min(len(movies), 10)}) that corresponds to the best match.
"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant that selects the best movie match from a list."},
        {"role": "user", "content": prompt}
    ]

    result = await call_openai(messages, max_tokens=50)
    if result:
        import re
        match = re.search(r'(\d+)', result)
        if match:
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(movies):
                return movies[idx]["id"]
    return movies[0]["id"]

# ========== Summary Generator ==========
async def generate_summary(movie_data: Dict[str, Any]) -> str:
    movie_info = f"""
Title: {movie_data.get('title')}
Overview: {movie_data.get('overview')}
Genres: {', '.join(movie_data.get('genres', []))}
Release Date: {movie_data.get('release_date')}
Director: {next((crew.get('name') for crew in movie_data.get('crew', []) if crew.get('job') == 'Director'), 'Unknown')}
"""
    prompt = f"""
You are a professional movie critic.

Write a **concise, engaging 2-3 sentence summary** for the following film. Include tone, theme, and hook. Make it readable for casual movie fans.

Movie Info:
{movie_info}
"""
    messages = [
        {"role": "system", "content": "You are a film critic who writes compelling movie summaries."},
        {"role": "user", "content": prompt}
    ]

    return await call_openai(messages, max_tokens=200) or movie_data.get("overview", "")

# ========== Dialogue Generator ==========
async def generate_dialogues(movie_data: Dict[str, Any]) -> List[Dict[str, str]]:
    movie_info = f"""
Title: {movie_data.get('title')}
Overview: {movie_data.get('overview')}
Genres: {', '.join(movie_data.get('genres', []))}
Release Date: {movie_data.get('release_date')}
Main Cast: {', '.join([f"{cast.get('name')} as {cast.get('character')}" for cast in movie_data.get('cast', [])[:5]])}
"""
    prompt = f"""
You're an expert at recalling and simulating famous movie dialogues.

Generate 5 **memorable and realistic dialogues** from the movie below. Mix emotional, humorous, or dramatic tones depending on genre.

Provide this format in your JSON response:
[
  {{
    "character": "Character Name",
    "quote": "The actual dialogue line",
    "context": "Brief description of the scene or situation"
  }}
]

Movie Info:
{movie_info}
"""
    messages = [
        {"role": "system", "content": "You are a movie expert who specializes in memorable film dialogues."},
        {"role": "user", "content": prompt}
    ]

    logger.info("Generating dialogues for: %s", movie_data.get("title"))
    content = await call_openai(messages, max_tokens=800, response_format={"type": "json_object"})
    try:
        parsed = json.loads(content)
        return parsed.get("dialogues", parsed)
    except Exception as e:
        logger.warning("Failed to parse dialogues: %s", str(e))
        return [{"character": "System", "quote": "Dialogues not available."}]

# ========== Similar Movies ==========
async def suggest_similar_movies(movie_data: Dict[str, Any]) -> List[str]:
    title = movie_data.get("title", "").strip().lower()

    movie_info = f"""
Title: {movie_data.get('title')}
Overview: {movie_data.get('overview')}
Genres: {', '.join(movie_data.get('genres', []))}
Release Date: {movie_data.get('release_date')}
"""
    prompt = f"""
You're a film expert recommending movies.

Based on the following movie:
{movie_info}

Suggest 8 movies that fans of this movie would enjoy, in order of relevance.

**Rules:**
1. First include any sequels, remakes, reboots, or movies in the same franchise or cinematic universe.
2. Then include other movies that share similar themes, tone, plot elements, or visual style.

Return ONLY the movie titles as a JSON array:
[
  "Movie Title 1",
  "Movie Title 2",
  ...
]
"""
    messages = [
        {"role": "system", "content": "You are a film recommendation expert with vast knowledge of movies."},
        {"role": "user", "content": prompt}
    ]

    logger.info("Suggesting similar movies for: %s", movie_data.get("title"))
    result = await call_openai(messages, max_tokens=300, response_format={"type": "json_object"})
    try:
        parsed = json.loads(result)
        if isinstance(parsed, dict):
            parsed = next(iter(parsed.values()), [])
        return [m for m in parsed if m.strip().lower() != title]
    except Exception as e:
        logger.warning("Failed to parse similar movie titles: %s", str(e))
        return []

async def find_similar_movies(movie_id: int, movie_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    titles = await suggest_similar_movies(movie_data)
    similar_movies = []

    for title in titles[:8]:
        results = await search_movies(title)
        if results:
            movie = results[0]
            similar_movies.append({
                "id": movie["id"],
                "title": movie["title"],
                "poster_path": movie.get("poster_path"),
                "release_date": movie.get("release_date", ""),
                "similarity_score": 0.85
            })

    if len(similar_movies) < 5:
        try:
            response = await client.get(
                f"{BASE_URL}/movie/{movie_id}/recommendations",
                params={"api_key": TMDB_API_KEY, "language": "en-US", "page": 1}
            )
            for m in response.json().get("results", []):
                if not any(sm["id"] == m["id"] for sm in similar_movies):
                    similar_movies.append({
                        "id": m["id"],
                        "title": m["title"],
                        "poster_path": m.get("poster_path"),
                        "release_date": m.get("release_date", ""),
                        "similarity_score": round(m.get("vote_average", 0) / 10, 2)
                    })
        except Exception as e:
            logger.error("TMDb fallback failed: %s", str(e))

    return similar_movies

# ========== Fallback Soundtrack ==========
async def generate_soundtrack_via_openai(title: str, year: Optional[str] = None) -> Dict[str, Any]:
    prompt = f"""
You are a music expert who specializes in movie and TV soundtracks.

List the most iconic tracks (with artist or composer names) from the official soundtrack of the following movie:

Title: {title}
Year: {year or "unknown"}

Respond in JSON format:
{{
  "source": "openai",
  "album": "Soundtrack of {title}",
  "artist": "Various Artists or Composer",
  "tracks": [
    {{
      "name": "Track Title",
      "artist": "Artist Name",
      "note": "Optional context"
    }}
  ]
}}
"""
    messages = [
        {"role": "system", "content": "You are a soundtrack expert who outputs JSON."},
        {"role": "user", "content": prompt}
    ]

    result = await call_openai(messages, max_tokens=500, response_format={"type": "json_object"})
    try:
        return json.loads(result)
    except Exception as e:
        logger.error("OpenAI soundtrack fallback failed: %s", str(e))
        return {"source": "openai", "tracks": [], "error": "Soundtrack not available"}
