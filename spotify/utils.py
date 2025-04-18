import requests
import base64
import json
import time
import spotipy
from django.conf import settings

def get_spotify_client(user):
    """
    Get a Spotify API client for the given user.
    """
    try:
        # Get the user's Spotify tokens from social auth
        social = user.social_auth.get(provider='spotify')
        token = social.extra_data.get('access_token')
        expires_at = social.extra_data.get('expires')

        # Check if token is expired or about to expire (buffer of 60 seconds)
        if expires_at <= int(time.time()) + 60:
            # Refresh the token
            refresh_token = social.extra_data.get('refresh_token')
            new_token_info = refresh_spotify_token(refresh_token)
            
            if new_token_info and 'access_token' in new_token_info:
                # Update the social auth record
                social.extra_data['access_token'] = new_token_info['access_token']
                social.extra_data['expires'] = int(time.time()) + new_token_info.get('expires_in', 3600)
                if 'refresh_token' in new_token_info:
                    social.extra_data['refresh_token'] = new_token_info['refresh_token']
                social.save()
                
                token = new_token_info['access_token']
            else:
                raise Exception("Failed to refresh Spotify token")
        
        # Create and return the Spotify client
        return spotipy.Spotify(auth=token)
    except Exception as e:
        print(f"Error getting Spotify client: {str(e)}")
        raise

def refresh_spotify_token(refresh_token):
    """
    Refresh the Spotify access token using the refresh token.
    """
    try:
        client_id = settings.SOCIAL_AUTH_SPOTIFY_KEY
        client_secret = settings.SOCIAL_AUTH_SPOTIFY_SECRET
        
        # Prepare the request
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode('ascii')).decode('ascii')
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        # Make the request to Spotify's token endpoint
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            headers=headers,
            data=data
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error refreshing token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error refreshing Spotify token: {str(e)}")
        return None 