from typing import List, Dict, Any

def classical_search(movies: List[Dict[str, Any]], query: str) -> int:
    """
    Classical search implementation for comparison with quantum search
    """
    if not movies:
        return None
        
    # Simple relevance scoring
    best_match = None
    highest_score = -1
    
    query_words = set(query.lower().split())
    
    for movie in movies:
        title = movie.get('title', '').lower()
        overview = movie.get('overview', '').lower()
        
        title_words = set(title.split())
        overview_words = set(overview.split())
        
        # Title matches worth more than overview matches
        title_matches = len(query_words.intersection(title_words)) * 3
        overview_matches = len(query_words.intersection(overview_words))
        
        # Include popularity from TMDb as a factor
        popularity = movie.get('popularity', 0) / 20
        
        # Combined score
        score = title_matches + overview_matches + popularity
        
        if score > highest_score:
            highest_score = score
            best_match = movie
    
    return best_match['id'] if best_match else movies[0]['id']