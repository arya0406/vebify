from django.urls import path
from . import views

app_name = 'mood_detection'

urlpatterns = [
    path('face/', views.face_mood_player, name='face_mood_player'),
    path('detect/', views.detect_mood, name='detect_mood'),
] 