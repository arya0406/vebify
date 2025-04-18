from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _



class CustomUser(AbstractUser):
    """Custom user model with additional fields."""
    email = models.EmailField(_('email address'), unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    dark_mode = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email


class Playlist(models.Model):
    """Model for user playlists."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='playlists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    mood = models.ForeignKey('moods.Mood', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']


class PlaylistSong(models.Model):
    """Model for songs in a playlist with position/ordering."""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='playlist_songs')
    song_id = models.CharField(max_length=100)  # External ID (e.g., Spotify track ID)
    song_name = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    album_name = models.CharField(max_length=255, blank=True, null=True)
    album_cover_url = models.URLField(blank=True, null=True)
    duration_ms = models.IntegerField(default=0)
    position = models.IntegerField(default=0)  # Order in the playlist
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['position']
        unique_together = ['playlist', 'song_id']
        
    def __str__(self):
        return f"{self.song_name} - {self.artist_name} ({self.playlist.name})"


class UserMoodHistory(models.Model):
    """Model to track user's mood history."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mood_history')
    mood = models.ForeignKey('moods.Mood', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    track_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.mood.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
