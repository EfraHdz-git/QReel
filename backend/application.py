from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import traceback
import os
import json
import asyncio
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Local modules
from api import tmdb, lastfm
from api.tmdb import search_movies, get_movie_details
from api.openai_api import (
    refine_search_query,
    select_best_movie_match,
    generate_summary,
    generate_dialogues,
    find_similar_movies,
    generate_soundtrack_via_openai
)
from quantum_search.grover import quantum_search
from quantum_search.classical import classical_search

# Main FastAPI app
application = FastAPI(title="Quantum Movie Search API")

application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    use_quantum: bool = False

def match_movie_by_title_and_year(movies: List[Dict[str, Any]], title: str, year: str) -> Optional[int]:
    title = title.lower().strip()
    year = year.strip()
    for movie in movies:
        movie_title = movie.get("title", "").lower().strip()
        movie_year = movie.get("release_date", "")[:4]
        if movie_title == title and movie_year == year:
            return movie["id"]
    return None

@application.post("/search")
async def search(request: SearchRequest):
    try:
        logger.info(f"Received search: '{request.query}' | Quantum: {request.use_quantum}")

        refined_data = await refine_search_query(request.query)
        refined_query = refined_data.get("refined_query", request.query)
        intent_type = refined_data.get("intent_type", "title")
        likely_year = refined_data.get("likely_year")

        logger.info(f"Refined: '{refined_query}' | Intent: {intent_type} | Year: {likely_year}")

        movies = await search_movies(refined_query)
        if not movies:
            raise HTTPException(status_code=404, detail="No movies found")

        movie_id = match_movie_by_title_and_year(movies, refined_query, likely_year) if likely_year else None

        if not movie_id:
            if request.use_quantum:
                movie_id = quantum_search(movies, refined_query)
            else:
                movie_id = await select_best_movie_match(movies, request.query) or classical_search(movies, refined_query)

        movie_details = await get_movie_details(movie_id)

        summary_task = generate_summary(movie_details)
        dialogue_task = generate_dialogues(movie_details)
        similar_task = find_similar_movies(movie_id, movie_details)

        summary, dialogues, similar_movies = await asyncio.gather(summary_task, dialogue_task, similar_task)

        return {
            "movie": {
                **movie_details,
                "summary": summary,
                "dialogues": dialogues,
                "search_info": {
                    "original_query": request.query,
                    "refined_query": refined_query,
                    "intent_type": intent_type
                }
            },
            "similar_movies": similar_movies
        }
    except Exception as e:
        logger.error(f"Search failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")

@application.get("/api/movie/soundtrack/{movie_id}")
async def get_movie_soundtrack(movie_id: int):
    movie = await get_movie_details(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    title = movie.get("title")
    year = movie.get("release_date", "")[:4]

    logger.info(f"Fetching soundtrack for '{title}' ({year})")
    soundtrack = lastfm.get_movie_soundtrack(title, year)

    if not soundtrack.get("tracks") or soundtrack.get("error"):
        logger.warning("Last.fm failed. Using OpenAI fallback.")
        soundtrack = await generate_soundtrack_via_openai(title, year)

    return {
        "title": title,
        "year": year,
        "soundtrack": soundtrack
    }

@application.get("/api/movie/{movie_id}")
async def get_movie_by_id(movie_id: int):
    try:
        movie = await get_movie_details(movie_id)
        logger.info(f"Movie ID {movie_id}: {movie.get('title')}")

        summary_task = generate_summary(movie)
        dialogue_task = generate_dialogues(movie)
        similar_task = find_similar_movies(movie_id, movie)

        summary, dialogues, similar = await asyncio.gather(summary_task, dialogue_task, similar_task)

        return {
            "movie": {
                **movie,
                "summary": summary,
                "dialogues": dialogues,
                "search_info": {
                    "source": "direct",
                    "matched_by": "id"
                }
            },
            "similar_movies": similar
        }
    except Exception as e:
        logger.error(f"Error in GET /api/movie/{movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch movie by ID")

@application.get("/status")
async def status():
    return {"status": "ok", "message": "Quantum Movie Search API running"}
