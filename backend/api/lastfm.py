import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_BASE_URL = "http://ws.audioscrobbler.com/2.0/"

def search_movie_soundtrack(movie_title, year=None):
    """
    Search for a movie soundtrack on Last.fm
    
    Args:
        movie_title (str): The title of the movie
        year (str, optional): Release year to help refine the search
    
    Returns:
        dict: Soundtrack information including tracks, artist, and album details
    """
    search_term = f"{movie_title} soundtrack"
    if year:
        search_term += f" {year}"
    
    params = {
        "method": "album.search",
        "album": search_term,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": 5  # Get top 5 results
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params)
        response.raise_for_status()
        results = response.json()
        
        if "results" in results and "albummatches" in results["results"]:
            albums = results["results"]["albummatches"]["album"]
            
            if not albums:
                return {"error": "No soundtrack found", "tracks": []}
            
            # Get more details for the top album
            top_album = albums[0]
            return get_album_tracks(top_album["artist"], top_album["name"])
        
        return {"error": "Failed to parse Last.fm response", "tracks": []}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Last.fm API error: {str(e)}", "tracks": []}

def get_album_tracks(artist, album):
    """
    Get track list for a specific album
    
    Args:
        artist (str): Artist name
        album (str): Album name
    
    Returns:
        dict: Album information with track list
    """
    params = {
        "method": "album.getinfo",
        "artist": artist,
        "album": album,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "album" in data:
            album_info = data["album"]
            
            # Format the response
            result = {
                "album": album_info.get("name", album),
                "artist": album_info.get("artist", artist),
                "url": album_info.get("url", ""),
                "image": album_info.get("image", [{}])[-1].get("#text", ""),  # Get largest image
                "tracks": []
            }
            
            # Extract tracks
            if "tracks" in album_info and "track" in album_info["tracks"]:
                tracks = album_info["tracks"]["track"]
                if isinstance(tracks, list):
                    for track in tracks:
                        result["tracks"].append({
                            "name": track.get("name", ""),
                            "duration": track.get("duration", 0),
                            "url": track.get("url", "")
                        })
                else:  # Single track
                    result["tracks"].append({
                        "name": tracks.get("name", ""),
                        "duration": tracks.get("duration", 0),
                        "url": tracks.get("url", "")
                    })
            
            return result
        
        return {"error": "Album info not found", "tracks": []}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Last.fm API error in get_album_tracks: {str(e)}", "tracks": []}

def get_movie_soundtrack(movie_title, year=None):
    """
    Main function to get movie soundtrack information
    
    Args:
        movie_title (str): The title of the movie
        year (str, optional): Release year
    
    Returns:
        dict: Soundtrack information or error
    """
    soundtrack_data = search_movie_soundtrack(movie_title, year)
    
    # If no tracks found, try a more generic search
    if not soundtrack_data.get("tracks") and soundtrack_data.get("error"):
        soundtrack_data = search_movie_soundtrack(movie_title)
    
    return soundtrack_data