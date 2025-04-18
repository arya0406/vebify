from django.contrib import admin
from .models import UserSpotify

@admin.register(UserSpotify)
class UserSpotifyAdmin(admin.ModelAdmin):
    list_display = ('user', 'spotify_id', 'token_expires_at')
    search_fields = ('user__username', 'spotify_id') 