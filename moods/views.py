from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.spotify_service import SpotifyService
from users.models import UserMoodHistory
import logging
from django.conf import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def mood_list(request):
    """View for displaying the list of moods."""
    search_query = request.GET.get('mood_search', '').strip()
    
    # Define all available moods
    all_moods = [
        {'id': 'happy', 'name': 'Happy', 'icon': '😊'},
        {'id': 'sad', 'name': 'Sad', 'icon': '😔'},
        {'id': 'dance', 'name': 'Dance', 'icon': '💃'},
        {'id': 'joy', 'name': 'Joy', 'icon': '🎉'},
        {'id': 'nostalgia', 'name': 'Nostalgia', 'icon': '📷'},
        {'id': 'frustration', 'name': 'Frustration', 'icon': '😤'},
        {'id': 'sad-lonely', 'name': 'Sad/Lonely', 'icon': '💔'},
        {'id': 'love', 'name': 'Love', 'icon': '❤️'},
        {'id': 'excitement', 'name': 'Excitement', 'icon': '🌟'},
        {'id': 'confidence', 'name': 'Confidence', 'icon': '💪'},
        {'id': 'anger', 'name': 'Anger', 'icon': '😠'},
        {'id': 'sunday-mood', 'name': 'Sunday Mood', 'icon': '☀️'},
        {'id': 'easy-rider', 'name': 'Easy Rider', 'icon': '🎸'},
    ]
    
    # Filter moods if search query exists
    if search_query:
        filtered_moods = [
            mood for mood in all_moods
            if search_query.lower() in mood['name'].lower()
        ]
        all_moods = filtered_moods
    
    context = {
        'all_moods': all_moods,
        'search_query': search_query,
    }
    
    logger.debug(f"Displaying mood list with {len(all_moods)} moods")
    return render(request, 'moods/mood_list.html', context)

@login_required
@require_http_methods(["GET"])
def select_mood(request, mood_id):
    """View for displaying tracks based on selected mood."""
    try:
        # Convert mood_id to proper name format
        mood_name = mood_id.replace('-', ' ').title()
        if mood_name == "Sad Lonely":
            mood_name = "Sad/Lonely"
            
        logger.info(f"Searching tracks for mood: {mood_name}")
        
        # Check if user is connected to Spotify
        from spotify.models import UserSpotify
        spotify_token = None
        spotify_connected = False
        
        try:
            # Get Spotify connection and token
            user_spotify = UserSpotify.objects.get(user=request.user)
            spotify_connected = True
            
            # Get a valid token
            from spotify.views import get_valid_spotify_token
            spotify_token = get_valid_spotify_token(request)
            
            if not spotify_token:
                logger.warning(f"No valid Spotify token for user {request.user.username}")
                messages.warning(request, "Your Spotify connection needs to be refreshed. Please reconnect.")
                return redirect('spotify:spotify_login')
                
        except UserSpotify.DoesNotExist:
            # Redirect to Spotify login if not connected
            messages.info(request, "Please connect to Spotify to get personalized recommendations for your mood")
            return redirect('spotify:spotify_login')
        
        # Get tracks for the selected mood
        spotify_service = SpotifyService(request)
        tracks = spotify_service.get_recommendations_by_mood(mood_name)
        
        # Save mood to user history - find or create the Mood object
        if request.user.is_authenticated:
            try:
                # Try to get the mood from database
                from moods.models import Mood
                mood, created = Mood.objects.get_or_create(
                    name=mood_name,
                    defaults={
                        'description': f'Mood for {mood_name}',
                        'icon': '😊'  # Default icon
                    }
                )
                
                # Add track count to UserMoodHistory
                from users.models import UserMoodHistory
                UserMoodHistory.objects.create(
                    user=request.user,
                    mood=mood,
                    track_count=len(tracks)
                )
            except Exception as e:
                logger.error(f"Error recording mood history: {str(e)}")
        
        context = {
            'tracks': tracks,
            'selected_mood': mood_name,
            'track_count': len(tracks),
            'spotify_connected': spotify_connected,
            'spotify_token': spotify_token
        }
        
        if not tracks:
            context['warning'] = "No tracks found for this mood. Try a different mood or check your Spotify connection."
            logger.warning(f"No tracks found for mood: {mood_name}")
        else:
            logger.info(f"Found {len(tracks)} tracks for mood: {mood_name}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(context)
        
        return render(request, 'moods/mood_tracks.html', context)
        
    except Exception as e:
        error_message = f"An error occurred while fetching tracks: {str(e)}"
        logger.error(f"Error in select_mood view for mood_id {mood_id}: {str(e)}")
        
        context = {
            'error': error_message,
            'selected_mood': mood_id.replace('-', ' ').title(),
            'tracks': [],
            'track_count': 0,
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(context, status=500)
            
        return render(request, 'moods/mood_tracks.html', context)

@login_required
@require_http_methods(["GET"])
def get_track_details(request, track_id):
    """View for getting detailed track information."""
    try:
        logger.info(f"Fetching details for Spotify track: {track_id}")
        spotify_service = SpotifyService(request)
        track_details = spotify_service.get_track_details(track_id)
        
        if track_details:
            logger.debug(f"Successfully retrieved details for track: {track_id}")
            return JsonResponse(track_details)
            
        logger.warning(f"Track not found: {track_id}")
        return JsonResponse({
            'error': 'Track not found',
            'message': 'The requested track could not be found. It may have been removed or is temporarily unavailable.'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error getting track details for track_id {track_id}: {str(e)}")
        return JsonResponse({
            'error': 'An error occurred while getting track details',
            'message': 'Please try again later. If the problem persists, try searching for a different track.'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def search_tracks(request):
    """View for searching tracks."""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'error': 'No search query provided'}, status=400)
    
    try:
        spotify_service = SpotifyService(request)
        tracks = spotify_service.search_tracks(query)
        
        return JsonResponse({
            'tracks': tracks,
            'count': len(tracks)
        })
    except Exception as e:
        logger.error(f"Error searching tracks: {str(e)}")
        return JsonResponse({
            'error': 'An error occurred while searching tracks',
            'message': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def mood_history(request):
    """View for displaying user's mood history."""
    try:
        # Get user's mood history, ordered by timestamp
        history = UserMoodHistory.objects.filter(user=request.user).order_by('-timestamp')
        
        context = {
            'mood_history': history,
        }
        
        logger.info(f"Displaying mood history for user {request.user.username}")
        return render(request, 'moods/mood_history.html', context)
        
    except Exception as e:
        logger.error(f"Error in mood_history view: {str(e)}")
        return render(request, 'moods/mood_history.html', {
            'error': 'An error occurred while fetching your mood history.',
            'mood_history': []
        })

def get_tracks_for_mood(sp, mood, limit=50):
    """Get tracks based on mood with improved search for Bollywood and better mood matching"""
    
    # Define mood-specific search parameters
    mood_params = {
        'dance': {
            'seed_genres': 'bollywood,dance,edm',
            'target_danceability': 0.8,
            'target_energy': 0.8,
            'min_popularity': 50
        },
        'happy': {
            'seed_genres': 'bollywood,pop,happy',
            'target_valence': 0.8,
            'target_energy': 0.7,
            'min_popularity': 50
        },
        'sad': {
            'seed_genres': 'bollywood,sad,acoustic',
            'target_valence': 0.2,
            'target_energy': 0.3,
            'min_popularity': 50
        },
        'romantic': {
            'seed_genres': 'bollywood,romance,love_song',
            'target_valence': 0.6,
            'target_energy': 0.4,
            'min_popularity': 50
        },
        'energetic': {
            'seed_genres': 'bollywood,party,edm',
            'target_energy': 0.9,
            'target_danceability': 0.7,
            'min_popularity': 50
        },
        'calm': {
            'seed_genres': 'bollywood,chill,acoustic',
            'target_energy': 0.3,
            'target_acousticness': 0.8,
            'min_popularity': 50
        }
    }

    try:
        # Get mood parameters or use defaults
        params = mood_params.get(mood.lower(), {
            'seed_genres': 'bollywood,pop',
            'target_energy': 0.5,
            'min_popularity': 50
        })

        # Search for Bollywood tracks first
        bollywood_query = f"genre:bollywood {mood}"
        bollywood_results = sp.search(q=bollywood_query, type='track', limit=limit//2)
        tracks = bollywood_results['tracks']['items']

        # Get recommended tracks based on mood parameters
        recommendations = sp.recommendations(limit=limit//2, **params)
        tracks.extend(recommendations['tracks'])

        # Process and format track data
        formatted_tracks = []
        seen_uris = set()  # To avoid duplicates

        for track in tracks:
            if track['uri'] not in seen_uris:
                seen_uris.add(track['uri'])
                formatted_tracks.append({
                    'uri': track['uri'],
                    'title': track['name'],
                    'artist': ', '.join(artist['name'] for artist in track['artists']),
                    'album': track['album']['name'],
                    'artwork': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    'preview_url': track['preview_url']
                })

        return formatted_tracks, None

    except Exception as e:
        return [], str(e)

def mood_tracks(request, mood):
    """View for displaying tracks based on mood"""
    try:
        sp = spotipy.Spotify(auth=request.session.get('spotify_token'))
        tracks, error = get_tracks_for_mood(sp, mood)
        
        return render(request, 'moods/mood_tracks.html', {
            'tracks': tracks,
            'selected_mood': mood.title(),
            'track_count': len(tracks),
            'error': error,
            'spotify_token': request.session.get('spotify_token', '')
        })
    except Exception as e:
        return render(request, 'moods/mood_tracks.html', {
            'error': str(e),
            'selected_mood': mood.title(),
            'spotify_token': request.session.get('spotify_token', '')
        }) 