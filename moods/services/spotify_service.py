import requests
import logging
from typing import Dict, List, Optional
from django.conf import settings
from spotify.views import get_valid_spotify_token, refresh_spotify_token

logger = logging.getLogger(__name__)

class SpotifyService:
    """Service for interacting with Spotify API for mood-based recommendations."""
    
    BASE_URL = "https://api.spotify.com/v1"
    
    # Map our moods to Spotify audio features
    MOOD_MAPPING = {
        'Happy': {'valence': 0.8, 'energy': 0.8, 'tempo': 120},
        'Sad': {'valence': 0.2, 'energy': 0.2, 'tempo': 70},
        'Dance': {'valence': 0.7, 'energy': 0.9, 'tempo': 130},
        'Joy': {'valence': 0.9, 'energy': 0.75, 'tempo': 115},
        'Nostalgia': {'valence': 0.5, 'energy': 0.4, 'tempo': 90},
        'Frustration': {'valence': 0.3, 'energy': 0.8, 'tempo': 140},
        'Confidence': {'valence': 0.7, 'energy': 0.7, 'tempo': 110},
        'Sad/Lonely': {'valence': 0.1, 'energy': 0.3, 'tempo': 65},
        'Love': {'valence': 0.6, 'energy': 0.4, 'tempo': 80},
        'Excitement': {'valence': 0.8, 'energy': 0.9, 'tempo': 140},
        'Anger': {'valence': 0.2, 'energy': 0.9, 'tempo': 150},
        'Sunday Mood': {'valence': 0.6, 'energy': 0.3, 'tempo': 85},
        'Easy Rider': {'valence': 0.5, 'energy': 0.6, 'tempo': 100}
    }
    
    # Map moods to genres for better recommendations
    GENRE_MAPPING = {
        'Happy': ['pop', 'happy', 'dance'],
        'Sad': ['sad', 'indie', 'piano', 'blues'],
        'Dance': ['dance', 'electronic', 'house', 'disco'],
        'Joy': ['pop', 'dance', 'happy'],
        'Nostalgia': ['oldies', 'classic rock', 'classic pop'],
        'Frustration': ['rock', 'punk', 'metal', 'grunge'],
        'Confidence': ['hip-hop', 'rap', 'r-n-b', 'dance'],
        'Sad/Lonely': ['blues', 'soul', 'acoustic', 'sad'],
        'Love': ['r-n-b', 'soul', 'romantic', 'indie', 'pop'],
        'Excitement': ['edm', 'dance', 'pop', 'rock'],
        'Anger': ['metal', 'rock', 'punk', 'hardcore'],
        'Sunday Mood': ['chill', 'acoustic', 'ambient', 'jazz'],
        'Easy Rider': ['rock', 'country', 'classic rock', 'folk']
    }
    
    def __init__(self, request=None):
        self.request = request
        self.token = None
        if request:
            self.token = get_valid_spotify_token(request)
    
    def set_token(self, token):
        """Set the token manually if not using request object."""
        self.token = token
    
    def get_recommendations_by_mood(self, mood: str, limit: int = 20) -> List[Dict]:
        """Get music recommendations based on mood using search endpoint."""
        if not self.token:
            logger.error("No Spotify token available")
            return []
        
        # Get genres for the mood
        mood_genres = self.GENRE_MAPPING.get(mood, ['pop', 'rock'])
        
        # Get audio features for the mood
        features = self.MOOD_MAPPING.get(mood, self.MOOD_MAPPING['Happy'])
        
        # Create search query based on mood and genres
        search_terms = []
        search_terms.append(f"genre:{mood_genres[0]}")
        
        # Add mood name to search if it's a common term
        if mood.lower() not in ['confidence', 'excitement', 'frustration']:
            search_terms.append(mood.lower())
        
        # Add a descriptor based on valence/energy
        if features['valence'] > 0.7:
            search_terms.append("happy")
        elif features['valence'] < 0.3:
            search_terms.append("sad")
            
        if features['energy'] > 0.7:
            search_terms.append("upbeat")
        elif features['energy'] < 0.3:
            search_terms.append("chill")
        
        search_query = " ".join(search_terms)
        logger.debug(f"Search query for mood {mood}: {search_query}")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {
            'q': search_query,
            'type': 'track',
            'limit': limit
        }
        
        logger.debug(f"Searching Spotify tracks for mood: {mood}")
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/search", 
                headers=headers, 
                params=params
            )
            
            # Handle authentication errors specifically
            if response.status_code in (401, 403):
                logger.error(f"Spotify authentication error: {response.status_code}")
                # Try to refresh token from the request if available
                if self.request:
                    from spotify.views import refresh_spotify_token, get_valid_spotify_token
                    from spotify.models import UserSpotify
                    try:
                        # Try to refresh the token
                        user_spotify = UserSpotify.objects.get(user=self.request.user)
                        refresh_spotify_token(user_spotify)
                        # Get the new token
                        self.token = get_valid_spotify_token(self.request)
                        if self.token:
                            # Retry with new token
                            logger.info("Retrying Spotify API call with refreshed token")
                            headers = {'Authorization': f'Bearer {self.token}'}
                            response = requests.get(
                                f"{self.BASE_URL}/search", 
                                headers=headers, 
                                params=params
                            )
                    except Exception as token_error:
                        logger.error(f"Error refreshing token: {str(token_error)}")
                        return []
            
            response.raise_for_status()
            data = response.json()
            
            if 'tracks' not in data or 'items' not in data['tracks']:
                logger.warning(f"No tracks in Spotify search response for mood: {mood}")
                return []
            
            # Format the tracks
            tracks = []
            for track in data['tracks']['items']:
                # Get the album image
                album_image = None
                if track.get('album', {}).get('images'):
                    album_image = track['album']['images'][0]['url']
                
                # Get artist names
                artists = ", ".join([artist['name'] for artist in track.get('artists', [])])
                
                tracks.append({
                    'id': track['id'],
                    'title': track['name'],
                    'artist': artists,
                    'album': track.get('album', {}).get('name', ''),
                    'preview_url': track.get('preview_url', ''),
                    'artwork': album_image,
                    'uri': track['uri'],
                    'spotify_url': track['external_urls'].get('spotify', ''),
                })
            
            logger.info(f"Found {len(tracks)} Spotify tracks for mood: {mood}")
            return tracks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Spotify tracks for mood: {str(e)}")
            return []
    
    def search_tracks(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for tracks on Spotify."""
        if not self.token:
            logger.error("No Spotify token available")
            return []
        
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {
            'q': query,
            'type': 'track',
            'limit': limit
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/search", 
                headers=headers, 
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if 'tracks' not in data or 'items' not in data['tracks']:
                return []
            
            # Format the tracks
            tracks = []
            for track in data['tracks']['items']:
                # Skip tracks without a preview URL
                if not track.get('preview_url'):
                    continue
                
                # Get the album image
                album_image = None
                if track.get('album', {}).get('images'):
                    album_image = track['album']['images'][0]['url']
                
                # Get artist names
                artists = ", ".join([artist['name'] for artist in track.get('artists', [])])
                
                tracks.append({
                    'id': track['id'],
                    'title': track['name'],
                    'artist': artists,
                    'album': track.get('album', {}).get('name', ''),
                    'preview_url': track['preview_url'],
                    'artwork': album_image,
                    'uri': track['uri'],
                    'spotify_url': track['external_urls'].get('spotify', ''),
                })
            
            return tracks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Spotify tracks: {str(e)}")
            return []
    
    def get_track_details(self, track_id: str) -> Optional[Dict]:
        """Get detailed information about a specific track."""
        if not self.token:
            logger.error("No Spotify token available")
            return None
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/tracks/{track_id}", 
                headers=headers
            )
            response.raise_for_status()
            track = response.json()
            
            # Get the album image
            album_image = None
            if track.get('album', {}).get('images'):
                album_image = track['album']['images'][0]['url']
            
            # Get artist names
            artists = ", ".join([artist['name'] for artist in track.get('artists', [])])
            
            return {
                'id': track['id'],
                'title': track['name'],
                'artist': artists,
                'album': track.get('album', {}).get('name', ''),
                'preview_url': track.get('preview_url', ''),
                'artwork': album_image,
                'uri': track['uri'],
                'spotify_url': track['external_urls'].get('spotify', ''),
                'duration': track.get('duration_ms', 0),
                'popularity': track.get('popularity', 0),
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting Spotify track details: {str(e)}")
            return None 