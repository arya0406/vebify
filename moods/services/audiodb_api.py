import os
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AudioDBAPI:
    """Service class for interacting with oDB API."""
    
    BASE_URL = "https://theaudiodb.com/api/v1/json/2"  # Using the free API key (2)
    
    # Mapping moods to genres and keywords for better search results
    MOOD_MAPPING = {
        'Happy': ['Pop', 'Dance', 'Disco', 'Funk', 'Happy'],
        'Sad': ['Blues', 'Soul', 'Ballad', 'Emotional'],
        'Dance': ['Dance', 'Electronic', 'House', 'Disco', 'Club'],
        'Joy': ['Pop', 'Dance', 'Funk', 'Happy', 'Upbeat'],
        'Nostalgia': ['Classic Rock', 'Oldies', 'Retro', 'Vintage'],
        'Frustration': ['Rock', 'Metal', 'Punk', 'Grunge'],
        'Confidence': ['Hip-Hop', 'Rap', 'Pop', 'Rock'],
        'Sad/Lonely': ['Blues', 'Soul', 'Acoustic', 'Melancholic'],
        'Love': ['R&B', 'Soul', 'Pop', 'Love Songs'],
        'Excitement': ['Rock', 'Electronic', 'Pop', 'Upbeat'],
        'Anger': ['Metal', 'Rock', 'Punk', 'Hardcore'],
        'Sunday Mood': ['Acoustic', 'Jazz', 'Chill', 'Relaxing'],
        'Easy Rider': ['Rock', 'Country', 'Road Trip', 'Classic Rock']
    }

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to TheAudioDB API with error handling."""
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None

    def _get_preview_url(self, track: Dict) -> Optional[str]:
        """Get a preview URL for a track using various fallback options."""
        preview_sources = [
            track.get('strMusicVid'),  # Official music video
            track.get('strMusicBrainzID'),  # MusicBrainz recording ID
            f"https://www.youtube.com/results?search_query={track.get('strArtist')}+{track.get('strTrack')}+official"  # YouTube search fallback
        ]
        
        for url in preview_sources:
            if url and self._is_valid_url(url):
                return url
        return None

    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid."""
        try:
            return bool(requests.head(url, timeout=5).ok)
        except:
            return False

    def search_tracks_by_mood(self, mood: str, limit: int = 20) -> List[Dict]:
        """
        Search for tracks based on mood by using genre and keyword mapping.
        Returns a list of tracks with their details.
        """
        tracks = []
        seen_track_ids = set()
        
        # Get genres for the mood
        genres = self.MOOD_MAPPING.get(mood, [mood])
        
        for genre in genres:
            data = self._make_request('search.php', {'s': '', 'g': genre})
            
            if not data or 'track' not in data or not data['track']:
                continue
            
            # Process each track
            for track in data['track']:
                track_id = track.get('idTrack')
                if track_id and track_id not in seen_track_ids:
                    seen_track_ids.add(track_id)
                    
                    # Get track details including preview URL
                    track_details = self.get_track_details(track_id)
                    if track_details and track_details.get('preview_url'):
                        tracks.append(track_details)
                        
                        if len(tracks) >= limit:
                            return tracks
        
        return tracks

    def get_track_details(self, track_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific track.
        Returns track details including preview URL if available.
        """
        data = self._make_request('track.php', {'h': track_id})
        
        if not data or 'track' not in data or not data['track']:
            return None
        
        track = data['track'][0]
        preview_url = self._get_preview_url(track)
        
        if not preview_url:
            return None
            
        return {
            'id': track.get('idTrack'),
            'title': track.get('strTrack'),
            'artist': track.get('strArtist'),
            'album': track.get('strAlbum'),
            'genre': track.get('strGenre'),
            'preview_url': preview_url,
            'artwork': track.get('strTrackThumb') or track.get('strArtistThumb'),
            'year': track.get('intYear'),
            'duration': track.get('intDuration'),
            'description': track.get('strDescriptionEN'),
        }

    def get_trending_tracks(self, limit: int = 20) -> List[Dict]:
        """
        Get trending tracks from TheAudioDB.
        Returns a list of trending tracks.
        """
        data = self._make_request('trending.php', {
            'country': 'us',
            'type': 'itunes',
            'format': 'singles'
        })
        
        if not data or 'trending' not in data or not data['trending']:
            return []
        
        tracks = []
        seen_track_ids = set()
        
        for track in data['trending']:
            track_id = track.get('idTrack')
            if track_id and track_id not in seen_track_ids:
                seen_track_ids.add(track_id)
                
                track_details = self.get_track_details(track_id)
                if track_details:
                    tracks.append(track_details)
                    
                    if len(tracks) >= limit:
                        break
        
        return tracks