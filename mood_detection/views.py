import cv2
import numpy as np
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
from . import services

# Configure logging
logger = logging.getLogger(__name__)

def face_mood_player(request):
    """
    Render the face mood detection page with integrated music player
    """
    return render(request, 'mood_detection/face_mood_player.html', {
        'soundcloud_player_url': '/soundcloud/player/',
    })

@csrf_exempt
def detect_mood(request):
    """
    Detect mood from webcam image using OpenCV
    """
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Read image file
            image_file = request.FILES['image']
            image_array = cv2.imdecode(
                np.frombuffer(image_file.read(), np.uint8),
                cv2.IMREAD_COLOR
            )
            
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            
            # Load face cascade classifier
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) > 0:
                # Use our service to detect the mood
                result = services.detect_facial_mood(image_array)
                return JsonResponse(result)
            else:
                logger.warning("No face detected in the image")
                return JsonResponse({
                    'success': False,
                    'error': 'No face detected in the image. Please try again.'
                })
            
        except Exception as e:
            logger.error(f"Error in detect_mood: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while processing the image. Please try again.'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    }) 