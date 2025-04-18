from django.urls import path
from . import views

app_name = 'moods'

urlpatterns = [
    path('', views.mood_list, name='mood_list'),
    path('select/<str:mood_id>/', views.select_mood, name='select_mood'),
    path('track/<str:track_id>/', views.get_track_details, name='track_details'),
    path('search/', views.search_tracks, name='search_tracks'),
    path('history/', views.mood_history, name='mood_history'),
] 