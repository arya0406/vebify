# Mood-Based Music App

A Django web application that recommends music based on your current mood using Spotify's API.

## Features

- User Authentication (Email/Password & Spotify Authentication)
- Mood Selection and Detection
- Mood-Based Music Recommendations via Spotify
- Spotify Web Playback SDK Integration
- User Personalization (Custom playlists, mood history)
- Embedded Music Player
- Dark & Light Mode
- Mood History Tracking
- Admin Panel

## Tech Stack

- Frontend: HTML, CSS, JavaScript (with Bootstrap 5)
- Backend: Django (Python)
- Database: SQLite (default), compatible with MySQL
- APIs: Spotify Web API, Spotify Web Playback SDK

## Quick Start

To run the application:

1. Double-click on `start_project.bat` in the project folder
2. The application will automatically:
   - Set up the virtual environment
   - Install dependencies
   - Create necessary directories
   - Run database migrations
   - Start the Django server
3. Open http://127.0.0.1:8000/ in your browser
4. Connect your Spotify account (requires Spotify Premium for playback)

## Setup Instructions (Manual)

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv new_virtualenv
   new_virtualenv\Scripts\activate  # Windows
   source new_virtualenv/bin/activate  # Linux/Mac
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Make sure the database is up to date:
   ```
   python manage.py migrate
   ```
5. Start the development server:
   ```
   python manage.py runserver
   ```
6. Run the cleanup script to remove unnecessary files (after closing the app):
   ```
   cleanup.bat  # Windows
   ```

## TheAudioDB Integration

This app uses TheAudioDB's free API (key=2) to find and play music based on mood. The free API includes:
- Track searches by artist, genre
- Track details
- Album artwork and descriptions
- Music video links
- Trending tracks

No API key is required as the app uses the public free tier (key=2).

## Mood-Based Music Features

1. **Mood Categories**:
   - Basic moods: Happy, Sad, Love, Anger
   - Activity moods: Dance, Workout, Party, Focus
   - Emotional moods: Joy, Nostalgia, Frustration, etc.
   - Situational moods: Sunday Mood, Easy Rider, etc.

2. **Music Player**:
   - Play/pause controls
   - Previous/next track navigation
   - Volume control
   - Track progress bar
   - Auto-play next track

3. **Mood History**:
   - Tracks your mood selections over time
   - Shows mood trends
   - Recommends music based on your frequently selected moods

## Usage

1. Register or log in to the app
2. Select your current mood from the mood list or search for a specific mood
3. Browse the music recommendations for your mood
4. Play and enjoy the music directly in the app
5. Check your mood history to see your mood patterns

## Troubleshooting

If you encounter any issues:

1. Make sure all dependencies are installed: `pip install -r requirements.txt`
2. Check if the database is properly migrated: `python manage.py migrate`
3. Restart the server
4. If you see errors about missing modules, try reinstalling the required packages

## Project Structure

- `moods/`: Handles mood selection, music recommendations, and TheAudioDB integration
- `users/`: User authentication and profile management
- `playlists/`: User playlist functionality
- `mood_detection/`: Simple mood detection capabilities
- `templates/`: HTML templates for the application
- `static/`: CSS, JavaScript, and image files