import base64
import json
import logging
import os
import requests
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .models import UserSpotify
from .utils import get_spotify_client, refresh_spotify_token

logger = logging.getLogger(__name__)

# Spotify API endpoints
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1/'

# Get Spotify credentials from environment variables
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://127.0.0.1:8000/spotify/callback')

# Required Spotify scopes for the application
SPOTIFY_SCOPES = [
    'user-read-private',
    'user-read-email',
    'streaming',
    'user-read-playback-state',
    'user-modify-playback-state',
    'user-read-currently-playing',
    'user-read-recently-played'
]

def get_spotify_auth_url():
    """Generate the Spotify authorization URL with proper scopes"""
    if not SPOTIFY_CLIENT_ID:
        logger.error("Spotify client ID not configured")
        return None
        
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': ' '.join(SPOTIFY_SCOPES),
        'show_dialog': 'true'  # Always show the auth dialog for better UX
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"

@login_required
def spotify_login(request):
    """
    Redirect the user to Spotify's authorization page.
    This allows any Spotify user to connect their account to our app.
    """
    auth_url = get_spotify_auth_url()
    if not auth_url:
        messages.error(request, "Spotify integration is not properly configured. Please try again later.")
        return redirect('moods:mood_list')
    
    # Store the current timestamp for token expiry calculation
    request.session['spotify_auth_start'] = timezone.now().timestamp()
    return redirect(auth_url)

@login_required
def spotify_callback(request):
    """Handle the callback from Spotify OAuth"""
    error = request.GET.get('error')
    code = request.GET.get('code')
    
    if error:
        logger.error(f"Spotify authentication error: {error}")
        messages.error(request, "Failed to connect to Spotify. Please try again.")
        return redirect('moods:mood_list')
        
    if not code:
        logger.error("No authorization code received from Spotify")
        messages.error(request, "No authorization code received from Spotify. Please try again.")
        return redirect('moods:mood_list')
    
    try:
        # Exchange the authorization code for access and refresh tokens
        token_data = exchange_code_for_tokens(code)
        
        if not token_data:
            messages.error(request, "Failed to get access token from Spotify. Please try again.")
            return redirect('moods:mood_list')
        
        # Get user profile from Spotify
        profile_data = get_spotify_profile(token_data['access_token'])
        
        if not profile_data:
            messages.error(request, "Failed to get Spotify profile. Please try again.")
            return redirect('moods:mood_list')
        
        # Save or update user's Spotify information
        expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour if not specified
        user_spotify, created = UserSpotify.objects.update_or_create(
            user=request.user,
            defaults={
                'spotify_id': profile_data['id'],
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),  # Might not always be present
                'token_expires_at': timezone.now() + timedelta(seconds=expires_in)
            }
        )
        
        messages.success(request, "Successfully connected to Spotify!")
        return redirect('spotify:player')
        
    except Exception as e:
        logger.error(f"Error in Spotify callback: {str(e)}")
        messages.error(request, "An error occurred while connecting to Spotify. Please try again.")
        return redirect('moods:mood_list')

def exchange_code_for_tokens(code):
    """Exchange the authorization code for access and refresh tokens"""
    if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET]):
        logger.error("Spotify client credentials not configured")
        return None
        
    try:
        # Prepare the token request
        auth_header = base64.b64encode(
            f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
        ).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SPOTIFY_REDIRECT_URI
        }
        
        logger.info(f"Attempting to exchange code for tokens with redirect URI: {SPOTIFY_REDIRECT_URI}")
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed with status {response.status_code}: {response.text}")
            return None
            
        token_data = response.json()
        logger.info("Successfully obtained token data from Spotify")
        return token_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error exchanging code for tokens: {str(e)}")
        return None

def get_spotify_profile(access_token):
    """Get the user's Spotify profile information"""
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        logger.info("Attempting to fetch Spotify profile")
        response = requests.get(f"{SPOTIFY_API_BASE_URL}me", headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Profile fetch failed with status {response.status_code}: {response.text}")
            return None
            
        profile_data = response.json()
        logger.info(f"Successfully fetched Spotify profile for user: {profile_data.get('id')}")
        return profile_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting Spotify profile: {str(e)}")
        return None

def get_valid_spotify_token(request):
    """
    Get a valid Spotify access token.
    If the current token is expired, refresh it.
    Attach the token to the request object for future use.
    """
    try:
        if hasattr(request, 'spotify_token'):
            return request.spotify_token
            
        user_spotify = UserSpotify.objects.get(user=request.user)
        
        # Check if token is expired or expires soon
        if user_spotify.token_expires_at <= timezone.now() + timedelta(minutes=5):
            # Token expired or expires soon, refresh it
            refreshed = refresh_spotify_token(user_spotify)
            if not refreshed:
                return None
        
        # Store token on request object for reuse
        request.spotify_token = user_spotify.access_token
        return user_spotify.access_token
    
    except UserSpotify.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error getting valid Spotify token: {str(e)}")
        return None
        
def refresh_spotify_token(user_spotify):
    """Refresh the Spotify access token using the refresh token"""
    try:
        auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode('ascii')
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': user_spotify.refresh_token
        }
        
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        # Update the tokens
        user_spotify.access_token = token_data['access_token']
        expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour
        user_spotify.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        # Update refresh token if present
        if 'refresh_token' in token_data:
            user_spotify.refresh_token = token_data['refresh_token']
            
        user_spotify.save()
        logger.info(f"Successfully refreshed Spotify token for user {user_spotify.user.username}")
        return True
        
    except Exception as e:
        logger.error(f"Error refreshing Spotify token: {str(e)}")
        return False

@login_required
def player(request):
    """Render the Spotify Web Playback SDK player page"""
    access_token = get_valid_spotify_token(request)
    
    if not access_token:
        messages.warning(request, "Please connect to Spotify first")
        return redirect('spotify:spotify_login')
    
    return render(request, 'spotify/player.html', {
        'spotify_token': access_token
    })

@login_required
def get_recommendations_by_mood(request, mood_id):
    """Get song recommendations based on mood"""
    access_token = get_valid_spotify_token(request)
    
    if not access_token:
        return JsonResponse({'error': 'Not connected to Spotify'}, status=401)
    
    # Map mood_id to Spotify audio features
    # These values are approximations and can be adjusted
    mood_features = {
        1: {'valence': 0.8, 'energy': 0.8, 'tempo': 120},  # Happy
        2: {'valence': 0.2, 'energy': 0.2, 'tempo': 70},   # Sad
        3: {'valence': 0.5, 'energy': 0.9, 'tempo': 140},  # Energetic
        4: {'valence': 0.3, 'energy': 0.4, 'tempo': 90},   # Relaxed
        5: {'valence': 0.6, 'energy': 0.7, 'tempo': 110},  # Excited
    }
    
    # Default to happy if mood_id not found
    features = mood_features.get(mood_id, mood_features[1])
    
    # Get recommendations from Spotify API
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'limit': 10,
        'seed_genres': 'pop,rock,hip-hop,electronic,r-n-b',
        'target_valence': features['valence'],
        'target_energy': features['energy'],
        'target_tempo': features['tempo']
    }
    
    try:
        response = requests.get(
            f"{SPOTIFY_API_BASE_URL}recommendations", 
            headers=headers, 
            params=params
        )
        response.raise_for_status()
        
        return JsonResponse(response.json())
    except requests.exceptions.RequestException as e:
        logger.error(f"Spotify recommendations error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_tracks_by_search(request):
    """Legacy search endpoint, redirects to the new search_track function."""
    return search_track(request)

@login_required
def search_track(request):
    """Search for tracks on Spotify."""
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'success': False, 'error': 'Missing search query'})
    
    try:
        # Get Spotify client
        spotify = get_spotify_client(request.user)
        
        # Search for tracks
        results = spotify.search(q=query, type='track', limit=20)
        
        # Extract track information
        tracks = []
        if 'tracks' in results and 'items' in results['tracks']:
            for track in results['tracks']['items']:
                tracks.append({
                    'id': track['id'],
                    'uri': track['uri'],
                    'name': track['name'],
                    'artists': [{'name': artist['name'], 'id': artist['id']} for artist in track['artists']],
                    'album': {
                        'name': track['album']['name'],
                        'images': track['album']['images'] if 'images' in track['album'] else []
                    },
                    'duration_ms': track['duration_ms'],
                    'popularity': track['popularity'],
                    'preview_url': track.get('preview_url', None),
                    'external_urls': track['external_urls']
                })
        
        return JsonResponse({'success': True, 'tracks': tracks})
    except Exception as e:
        print(f"Error searching tracks: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_token(request):
    """Get a valid Spotify access token for the user."""
    try:
        # Get Spotify client (this will refresh the token if needed)
        spotify = get_spotify_client(request.user)
        
        # Get the user's social auth entry to access the token
        social_auth = request.user.social_auth.get(provider='spotify')
        
        token_info = {
            'access_token': social_auth.extra_data['access_token'],
            'expires_at': social_auth.extra_data['expires'],
        }
        
        return JsonResponse({
            'success': True, 
            'token': token_info['access_token'],
            'expires_at': token_info['expires_at']
        })
    except Exception as e:
        logger.error(f"Error getting token: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
@csrf_protect
def play_track(request):
    """Play a track on the user's active Spotify device."""
    try:
        data = json.loads(request.body)
        track_uri = data.get('uri')
        device_id = data.get('device_id')
        
        if not track_uri:
            return JsonResponse({'success': False, 'error': 'Missing track URI'})
            
        # Get Spotify client
        spotify = get_spotify_client(request.user)
        
        play_params = {}
        if device_id:
            play_params['device_id'] = device_id
            
        # Start playback with the specified track
        spotify.start_playback(
            **play_params,
            uris=[track_uri]
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error playing track: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def spotify_auth(request):
    """Alias for spotify_login to maintain URL compatibility."""
    return spotify_login(request)

@login_required
def spotify_disconnect(request):
    """Disconnect the user's Spotify account."""
    try:
        # Find and delete the user's Spotify connection
        spotify_connection = UserSpotify.objects.filter(user=request.user)
        if spotify_connection.exists():
            spotify_connection.delete()
            messages.success(request, "Successfully disconnected from Spotify.")
        else:
            messages.info(request, "You are not connected to Spotify.")
    except Exception as e:
        logger.error(f"Error disconnecting Spotify: {str(e)}")
        messages.error(request, "An error occurred while disconnecting from Spotify.")
    
    return redirect('profile') 