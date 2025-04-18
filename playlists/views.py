from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import models
import json
from users.models import Playlist, PlaylistSong
from moods.models import Mood

@login_required
def playlist_list(request):
    """View for listing user's playlists."""
    playlists = request.user.playlists.all()
    return render(request, 'playlists/playlist_list.html', {'playlists': playlists})

@login_required
def playlist_detail(request, pk):
    """View for displaying playlist details."""
    playlist = get_object_or_404(Playlist, pk=pk)
    # Check if user has permission to view the playlist
    if not playlist.is_public and playlist.user != request.user:
        messages.error(request, "You don't have permission to view this playlist.")
        return redirect('playlists:playlist_list')
    
    songs = playlist.playlist_songs.all().order_by('position')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        songs = songs.filter(song_name__icontains=search_query) | songs.filter(artist_name__icontains=search_query)
    
    # Pagination
    paginator = Paginator(songs, 20)  # 20 songs per page
    page_number = request.GET.get('page', 1)
    songs_page = paginator.get_page(page_number)
    
    return render(request, 'playlists/playlist_detail.html', {
        'playlist': playlist,
        'songs': songs_page,
        'search_query': search_query,
        'can_edit': request.user == playlist.user,
    })

@login_required
def playlist_create(request):
    """View for creating a new playlist."""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        mood_id = request.POST.get('mood')
        is_public = request.POST.get('is_public') == 'on'
        
        if name:
            mood = None
            if mood_id:
                mood = get_object_or_404(Mood, pk=mood_id)
            
            playlist = Playlist.objects.create(
                name=name,
                description=description,
                mood=mood,
                is_public=is_public,
                user=request.user
            )
            messages.success(request, "Playlist created successfully!")
            return redirect('playlists:playlist_detail', pk=playlist.pk)
        else:
            messages.error(request, "Please provide a name for the playlist.")
    
    moods = Mood.objects.all()
    return render(request, 'playlists/playlist_form.html', {'moods': moods})

@login_required
def playlist_edit(request, pk):
    """View for editing a playlist."""
    playlist = get_object_or_404(Playlist, pk=pk)
    
    # Check if user has permission to edit the playlist
    if playlist.user != request.user:
        messages.error(request, "You don't have permission to edit this playlist.")
        return redirect('playlists:playlist_list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        mood_id = request.POST.get('mood')
        is_public = request.POST.get('is_public') == 'on'
        
        if name:
            playlist.name = name
            playlist.description = description
            if mood_id:
                playlist.mood = get_object_or_404(Mood, pk=mood_id)
            else:
                playlist.mood = None
            playlist.is_public = is_public
            playlist.save()
            
            messages.success(request, "Playlist updated successfully!")
            return redirect('playlists:playlist_detail', pk=playlist.pk)
        else:
            messages.error(request, "Please provide a name for the playlist.")
    
    moods = Mood.objects.all()
    return render(request, 'playlists/playlist_form.html', {
        'playlist': playlist,
        'moods': moods
    })

@login_required
def playlist_delete(request, pk):
    """View for deleting a playlist."""
    playlist = get_object_or_404(Playlist, pk=pk)
    
    # Check if user has permission to delete the playlist
    if playlist.user != request.user:
        messages.error(request, "You don't have permission to delete this playlist.")
        return redirect('playlists:playlist_list')
    
    if request.method == 'POST':
        playlist.delete()
        messages.success(request, "Playlist deleted successfully!")
        return redirect('playlists:playlist_list')
    
    return render(request, 'playlists/playlist_confirm_delete.html', {'playlist': playlist})

# Song management views
@login_required
@require_POST
def add_song_to_playlist(request, playlist_id):
    """Add a song to a playlist with AJAX support."""
    playlist = get_object_or_404(Playlist, pk=playlist_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        song_id = data.get('song_id')
        song_name = data.get('song_name')
        artist_name = data.get('artist_name')
        album_name = data.get('album_name', '')
        album_cover_url = data.get('album_cover_url', '')
        duration_ms = data.get('duration_ms', 0)
        
        # Check if song already exists in playlist
        if PlaylistSong.objects.filter(playlist=playlist, song_id=song_id).exists():
            return JsonResponse({
                'success': False,
                'message': 'This song is already in the playlist.'
            }, status=400)
        
        # Get the last position in playlist
        last_position = PlaylistSong.objects.filter(playlist=playlist).order_by('-position').first()
        position = 0 if not last_position else last_position.position + 1
        
        # Create playlist song
        playlist_song = PlaylistSong.objects.create(
            playlist=playlist,
            song_id=song_id,
            song_name=song_name,
            artist_name=artist_name,
            album_name=album_name,
            album_cover_url=album_cover_url,
            duration_ms=duration_ms,
            position=position
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Song added to playlist.',
            'song': {
                'id': playlist_song.id,
                'song_id': playlist_song.song_id,
                'song_name': playlist_song.song_name,
                'artist_name': playlist_song.artist_name,
                'album_cover_url': playlist_song.album_cover_url,
                'position': playlist_song.position
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def remove_song_from_playlist(request, playlist_id, song_id):
    """Remove a song from a playlist."""
    playlist = get_object_or_404(Playlist, pk=playlist_id, user=request.user)
    playlist_song = get_object_or_404(PlaylistSong, pk=song_id, playlist=playlist)
    
    # Get the song's position for reordering
    position = playlist_song.position
    
    # Delete the song
    playlist_song.delete()
    
    # Reorder remaining songs
    PlaylistSong.objects.filter(playlist=playlist, position__gt=position).update(position=models.F('position') - 1)
    
    return JsonResponse({
        'success': True,
        'message': 'Song removed from playlist.'
    })

@login_required
@require_POST
def reorder_playlist_songs(request, playlist_id):
    """Reorder songs in a playlist with drag-and-drop."""
    playlist = get_object_or_404(Playlist, pk=playlist_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        new_order = data.get('song_order', [])
        
        if not new_order:
            return JsonResponse({
                'success': False,
                'message': 'No song order provided'
            }, status=400)
        
        # Update positions for all songs in the new order
        for index, song_id in enumerate(new_order):
            PlaylistSong.objects.filter(pk=song_id, playlist=playlist).update(position=index)
        
        return JsonResponse({
            'success': True,
            'message': 'Playlist songs reordered successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def reorder_songs(request, playlist_id):
    """Alias for reorder_playlist_songs to match URL pattern."""
    return reorder_playlist_songs(request, playlist_id)

# API endpoints
@login_required
def user_playlists_api(request):
    """API endpoint to get user playlists."""
    playlists = Playlist.objects.filter(user=request.user)
    playlists_data = []
    
    for playlist in playlists:
        playlists_data.append({
            'id': playlist.id,
            'name': playlist.name,
            'song_count': playlist.playlist_songs.count(),
            'is_public': playlist.is_public,
        })
    
    return JsonResponse({
        'success': True,
        'playlists': playlists_data
    })
