"""
URL configuration for music_app project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('moods/', include('moods.urls')),
    path('playlists/', include('playlists.urls')),
    path('mood-detection/', include('mood_detection.urls')),
    path('spotify/', include('spotify.urls')),
    path('', RedirectView.as_view(url='/users/login/'), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 