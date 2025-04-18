from django.urls import path
from . import views

app_name = 'playlists'

urlpatterns = [
    path('', views.playlist_list, name='playlist_list'),
    path('create/', views.playlist_create, name='playlist_create'),
    path('<int:playlist_id>/', views.playlist_detail, name='playlist_detail'),
    path('<int:playlist_id>/edit/', views.playlist_edit, name='playlist_edit'),
    path('<int:playlist_id>/delete/', views.playlist_delete, name='playlist_delete'),
    
    # Song management endpoints
    path('<int:playlist_id>/add-song/', views.add_song_to_playlist, name='add_song'),
    path('<int:playlist_id>/remove-song/<int:song_id>/', views.remove_song_from_playlist, name='remove_song'),
    path('<int:playlist_id>/reorder-songs/', views.reorder_songs, name='reorder_songs'),
    path('api/user-playlists/', views.user_playlists_api, name='user_playlists_api'),
] 