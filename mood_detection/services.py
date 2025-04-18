"""Services for mood detection."""

import logging
import cv2
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

def detect_facial_mood(image_data):
    """
    Detect mood from facial expression using OpenCV's face and feature detection.
    
    Args:
        image_data: Image data for processing
        
    Returns:
        dict: A dictionary containing mood detection results
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        
        # Load face cascade classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) == 0:
            logger.warning("No face detected in the image")
            return {
                'success': False,
                'error': 'No face detected in the image. Please try again.'
            }
        
        # Get the largest face
        face = max(faces, key=lambda x: x[2] * x[3])
        x, y, w, h = face
        
        # Extract face region
        face_roi = gray[y:y+h, x:x+w]
        face_color = image_data[y:y+h, x:x+w]
        
        # Detect eyes in the face region
        eyes = eye_cascade.detectMultiScale(face_roi)
        
        # Detect smile in the lower part of the face
        smile_roi = face_roi[int(h/2):, :]
        smiles = smile_cascade.detectMultiScale(smile_roi, scaleFactor=1.7, minNeighbors=20)
        
        # Calculate metrics
        eye_detected = len(eyes) >= 2
        smile_detected = len(smiles) > 0
        
        # Calculate face orientation (rough approximation)
        face_center_x = x + w/2
        frame_center_x = image_data.shape[1]/2
        looking_straight = abs(face_center_x - frame_center_x) < (image_data.shape[1] * 0.1)
        
        # Calculate attention score based on face position and size
        attention_score = min((w * h) / (image_data.shape[0] * image_data.shape[1] * 0.15), 1.0)
        
        # Calculate eye contact score
        eye_contact_score = 1.0 if eye_detected and looking_straight else 0.5
        
        # Calculate engagement based on multiple factors
        engagement = (attention_score + eye_contact_score) / 2
        
        # Analyze facial expression using pixel intensity in different regions
        upper_face = face_roi[:int(h/3), :]
        middle_face = face_roi[int(h/3):int(2*h/3), :]
        lower_face = face_roi[int(2*h/3):, :]
        
        # Calculate regional variances
        upper_variance = np.var(upper_face)
        middle_variance = np.var(middle_face)
        lower_variance = np.var(lower_face)
        
        # Determine mood based on combined analysis
        if smile_detected and eye_detected and engagement > 0.7:
            mood = 'Happy'
            confidence = 0.9
        elif smile_detected and engagement > 0.5:
            mood = 'Joy'
            confidence = 0.8
        elif not eye_detected or engagement < 0.3:
            mood = 'Relaxed'
            confidence = 0.7
        elif eye_detected and looking_straight and upper_variance > np.mean([middle_variance, lower_variance]):
            mood = 'Focused'
            confidence = 0.8
        elif upper_variance < np.mean([middle_variance, lower_variance]) and not smile_detected:
            mood = 'Sad'
            confidence = 0.7
        elif upper_variance > np.mean([middle_variance, lower_variance]) * 1.5:
            mood = 'Anger'
            confidence = 0.7
        elif engagement > 0.6:
            mood = 'Calm'
            confidence = 0.6
        else:
            mood = 'Neutral'
            confidence = 0.5
            
        logger.info(f"Detected mood: {mood} with confidence {confidence:.2f}")
        logger.debug(f"Eye contact score: {eye_contact_score:.2f}, Attention: {attention_score:.2f}")
        
        return {
            'success': True,
            'mood': mood,
            'emotion': mood.lower(),
            'confidence': float(f"{confidence:.2f}"),
            'metrics': {
                'eye_contact': float(f"{eye_contact_score:.2f}"),
                'attention': float(f"{attention_score:.2f}"),
                'engagement': float(f"{engagement:.2f}")
            }
        }
        
    except Exception as e:
        logger.error(f"Error in mood detection: {str(e)}")
        return {
            'success': False,
            'error': 'An error occurred while processing the image.'
        } 