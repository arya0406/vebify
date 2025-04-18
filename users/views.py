from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from .forms import CustomUserCreationForm, CustomUserChangeForm, CustomAuthenticationForm
from .models import CustomUser, UserMoodHistory
from moods.models import Mood
from django.db import models


def home(request):
    """View for the homepage."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'users/home.html')


def register_view(request):
    """View for user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Mood Music!")
            return redirect('dashboard')
        else:
            messages.error(request, "Registration failed. Please check the form for errors.")
    else:
        form = CustomUserCreationForm()
    
    # Add context for social authentication
    return render(request, 'users/register.html', {
        'form': form,
        'enable_social_auth': False  # Temporarily disable social auth until configured
    })


def login_view(request):
    """View for user login."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.username}!")
                    # Redirect to next page if specified, otherwise dashboard
                    next_page = request.GET.get('next')
                    return redirect(next_page if next_page else 'dashboard')
                else:
                    messages.error(request, "Your account is inactive.")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'users/login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })


@login_required
def dashboard_view(request):
    """View for the user dashboard."""
    # Get recent mood history
    mood_history = UserMoodHistory.objects.filter(user=request.user)[:5]
    
    # Define only the 4 specified moods with their icons
    quick_moods = [
        {'id': 'happy', 'name': 'Happy', 'emoji': '😊'},
        {'id': 'love', 'name': 'Love', 'emoji': '❤️'},
        {'id': 'confidence', 'name': 'Confidence', 'emoji': '💪'},
        {'id': 'anger', 'name': 'Anger', 'emoji': '😠'},
    ]
    
    context = {
        'mood_history': mood_history,
        'moods': quick_moods,
        # 'playlists': playlists
    }
    
    return render(request, 'users/dashboard.html', context)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating user profile."""
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)


@login_required
def profile_view(request):
    """View for displaying user profile."""
    user = request.user
    mood_history = UserMoodHistory.objects.filter(user=user)[:10]
    # playlists = user.playlists.all()
    
    context = {
        'user': user,
        'mood_history': mood_history,
        # 'playlists': playlists
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def toggle_dark_mode(request):
    """View for toggling dark mode."""
    user = request.user
    user.dark_mode = not user.dark_mode
    user.save()
    
    # Redirect back to the previous page
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def logout_view(request):
    """View for handling user logout."""
    if request.method == 'POST':
        logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect('home')
    return HttpResponseNotAllowed(['POST'])


# Global Search
def search_view(request):
    """Global search view to search songs, moods, and playlists."""
    query = request.GET.get('q', '')
    return_to = request.GET.get('return_to', '')
    
    songs = []
    moods = []
    playlists = []
    
    if query:
        # Search moods
        from moods.models import Mood
        moods = Mood.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(description__icontains=query)
        )[:10]
        
        # Search playlists (only public playlists or user's own playlists)
        from users.models import Playlist
        if request.user.is_authenticated:
            playlists = Playlist.objects.filter(
                models.Q(is_public=True) | models.Q(user=request.user)
            ).filter(
                models.Q(name__icontains=query) | 
                models.Q(description__icontains=query)
            )[:10]
        else:
            playlists = Playlist.objects.filter(
                is_public=True
            ).filter(
                models.Q(name__icontains=query) | 
                models.Q(description__icontains=query)
            )[:10]
        
        # Search songs from Spotify API
        if request.user.is_authenticated:
            try:
                from spotify.utils import get_spotify_client
                spotify = get_spotify_client(request.user)
                results = spotify.search(q=query, type='track', limit=10)
                if results and 'tracks' in results and 'items' in results['tracks']:
                    songs = results['tracks']['items']
                
                # If no songs found, try searching with more general queries
                if not songs:
                    # Try search by just artist if the query might be an artist name
                    artist_results = spotify.search(q=f"artist:{query}", type='track', limit=5)
                    if artist_results and 'tracks' in artist_results and 'items' in artist_results['tracks']:
                        songs.extend(artist_results['tracks']['items'])
                    
                    # Try search by just album if the query might be an album name
                    album_results = spotify.search(q=f"album:{query}", type='track', limit=5)
                    if album_results and 'tracks' in album_results and 'items' in album_results['tracks']:
                        songs.extend(album_results['tracks']['items'])
                    
                    # If still no songs, get recommended tracks based on popular genres
                    if not songs:
                        # Get some tracks from popular genres as fallback
                        fallback_genres = ["pop", "rock", "hip hop", "bollywood", "indian"]
                        for genre in fallback_genres:
                            if len(songs) >= 10:
                                break
                            genre_results = spotify.search(q=f"genre:{genre}", type='track', limit=3)
                            if genre_results and 'tracks' in genre_results and 'items' in genre_results['tracks']:
                                songs.extend(genre_results['tracks']['items'][:3])
            except Exception as e:
                print(f"Spotify search error: {str(e)}")
                
                # Fallback to hardcoded popular songs if Spotify API fails
                songs = get_fallback_songs()
    else:
        # Show trending/popular songs if no query
        if request.user.is_authenticated:
            try:
                from spotify.utils import get_spotify_client
                spotify = get_spotify_client(request.user)
                
                # Get trending tracks
                results = spotify.search(q="year:2023", type='track', limit=10)
                if results and 'tracks' in results and 'items' in results['tracks']:
                    songs = results['tracks']['items']
            except Exception as e:
                print(f"Spotify trending search error: {str(e)}")
                songs = get_fallback_songs()
    
    return render(request, 'users/search_results.html', {
        'query': query,
        'songs': songs,
        'moods': moods,
        'playlists': playlists,
        'return_to': return_to,
    })


def get_fallback_songs():
    """Return a list of fallback songs when Spotify API fails."""
    return [
        {
            'id': '1',
            'name': 'Tum Hi Ho',
            'preview_url': 'https://p.scdn.co/mp3-preview/9177d158a4e3100f577cff51470231a618d1a19a',
            'artists': [{'name': 'Arijit Singh'}],
            'album': {
                'name': 'Aashiqui 2',
                'images': [{'url': 'https://i.scdn.co/image/ab67616d0000b273c75c3adb82cb60037fa3b290'}]
            },
            'external_urls': {'spotify': 'https://open.spotify.com/track/14wyRXMFNEhE1lenQFG2BR'}
        },
        {
            'id': '2',
            'name': 'Despacito',
            'preview_url': 'https://p.scdn.co/mp3-preview/542975c6c572fde5622beac7c699d7799c3f5ed0',
            'artists': [{'name': 'Luis Fonsi'}, {'name': 'Daddy Yankee'}],
            'album': {
                'name': 'Vida',
                'images': [{'url': 'https://i.scdn.co/image/ab67616d0000b273ef0d4234e1a645740f77d59c'}]
            },
            'external_urls': {'spotify': 'https://open.spotify.com/track/6habFhsOp2NvshLv26jqjb'}
        },
        {
            'id': '3',
            'name': 'Shape of You',
            'preview_url': 'https://p.scdn.co/mp3-preview/84462d8e1e4d0f9e5ccd06f0da390f65843774a2',
            'artists': [{'name': 'Ed Sheeran'}],
            'album': {
                'name': '÷ (Divide)',
                'images': [{'url': 'https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96'}]
            },
            'external_urls': {'spotify': 'https://open.spotify.com/track/7qiZfU4dY1lWllzX7mPBI3'}
        },
        {
            'id': '4',
            'name': 'Blinding Lights',
            'preview_url': 'https://p.scdn.co/mp3-preview/8b637da3b5f26b5cc64cca063bc50d6a81166c8b',
            'artists': [{'name': 'The Weeknd'}],
            'album': {
                'name': 'After Hours',
                'images': [{'url': 'https://i.scdn.co/image/ab67616d0000b2738863bc11d2aa12b54f5aeb36'}]
            },
            'external_urls': {'spotify': 'https://open.spotify.com/track/0VjIjW4GlUZAMYd2vXMi3b'}
        },
        {
            'id': '5',
            'name': 'Bhool Bhulaiyaa 2 Title Track',
            'preview_url': 'https://p.scdn.co/mp3-preview/bbdb40da149c144aabdbc74f7dc61d66f34f8e63',
            'artists': [{'name': 'Neeraj Shridhar'}],
            'album': {
                'name': 'Bhool Bhulaiyaa 2',
                'images': [{'url': 'https://i.scdn.co/image/ab67616d0000b27361248b72f4471b1e7a391eb2'}]
            },
            'external_urls': {'spotify': 'https://open.spotify.com/track/4n4g5xYSAZiZ2tkXyVPIfs'}
        }
    ]


@login_required
def delete_account_view(request):
    """View for handling user account deletion."""
    if request.method == 'POST':
        username_confirm = request.POST.get('username_confirm')
        
        # Validate username confirmation
        if username_confirm == request.user.username:
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Your account has been successfully deleted.")
            return redirect('home')
        else:
            messages.error(request, "Username confirmation did not match. Account not deleted.")
            return redirect('delete_account')
    
    return render(request, 'users/delete_account.html') 