from django.urls import path
from . import views

app_name = 'spotify'

urlpatterns = [
    path('login/', views.spotify_login, name='spotify_login'),
    path('callback/', views.spotify_callback, name='callback'),
    path('auth/', views.spotify_auth, name='auth'),
    path('disconnect/', views.spotify_disconnect, name='disconnect'),
    path('get-token/', views.get_token, name='get_token'),
    path('play/', views.play_track, name='play_track'),
    path('search/', views.search_track, name='search_track'),
    path('player/', views.player, name='player'),
    path('recommendations/<int:mood_id>/', views.get_recommendations_by_mood, name='recommendations'),
] 