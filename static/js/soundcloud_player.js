/**
 * SoundCloud Music Player
 * This script handles the SoundCloud music player functionality.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Player state
    const playerState = {
        tracks: initialTracks || [],
        currentTrackIndex: 0,
        isPlaying: false,
        currentTime: 0,
        duration: 0,
        audio: new Audio(),
        currentMood: ''
    };

    // DOM Elements
    const tracksContainer = document.getElementById('tracks-container');
    const currentTrackArtwork = document.getElementById('current-track-artwork');
    const currentTrackTitle = document.getElementById('current-track-title');
    const currentTrackArtist = document.getElementById('current-track-artist');
    const playPauseBtn = document.getElementById('play-pause-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const likeBtn = document.getElementById('like-btn');
    const progressBar = document.querySelector('.progress-bar .progress');
    const currentTimeEl = document.getElementById('current-time');
    const totalTimeEl = document.getElementById('total-time');
    const moodButtons = document.querySelectorAll('.mood-btn');

    // Initialize player
    function initPlayer() {
        renderTrackList();
        setupEventListeners();
        if (playerState.tracks.length > 0) {
            loadTrack(0);
        }
    }

    // Render track list
    function renderTrackList() {
        tracksContainer.innerHTML = '';
        
        if (playerState.tracks.length === 0) {
            tracksContainer.innerHTML = '<p>No tracks available. Select a mood to see tracks.</p>';
            return;
        }
        
        playerState.tracks.forEach((track, index) => {
            const trackItem = document.createElement('div');
            trackItem.className = 'track-item';
            trackItem.dataset.index = index;
            
            const thumbnail = document.createElement('div');
            thumbnail.className = 'track-thumbnail';
            
            const img = document.createElement('img');
            img.src = track.artwork_url || '/static/images/default-album-art.jpg';
            img.alt = track.title;
            thumbnail.appendChild(img);
            
            const info = document.createElement('div');
            info.className = 'track-info';
            
            const title = document.createElement('h4');
            title.textContent = track.title;
            
            const artist = document.createElement('p');
            artist.textContent = track.artist;
            
            info.appendChild(title);
            info.appendChild(artist);
            
            trackItem.appendChild(thumbnail);
            trackItem.appendChild(info);
            
            tracksContainer.appendChild(trackItem);
        });
    }

    // Load track
    function loadTrack(index) {
        if (index < 0 || index >= playerState.tracks.length) {
            return;
        }
        
        playerState.currentTrackIndex = index;
        const track = playerState.tracks[index];
        
        // Update UI
        currentTrackTitle.textContent = track.title;
        currentTrackArtist.textContent = track.artist;
        currentTrackArtwork.src = track.artwork_url || '/static/images/default-album-art.jpg';
        
        // Update audio source
        playerState.audio.src = track.stream_url;
        playerState.audio.load();
        
        // Update track items
        const trackItems = document.querySelectorAll('.track-item');
        trackItems.forEach((item, i) => {
            if (i === index) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        // Log play to server
        logPlayToServer(track.id);
        
        // Start playing if was playing before
        if (playerState.isPlaying) {
            playerState.audio.play()
                .then(() => {
                    updatePlayPauseButton(true);
                })
                .catch(error => {
                    console.error("Error playing track:", error);
                    updatePlayPauseButton(false);
                });
        }
    }

    // Play/Pause toggle
    function togglePlayPause() {
        if (playerState.tracks.length === 0) {
            return;
        }
        
        if (playerState.isPlaying) {
            playerState.audio.pause();
            playerState.isPlaying = false;
        } else {
            playerState.audio.play()
                .then(() => {
                    playerState.isPlaying = true;
                })
                .catch(error => {
                    console.error("Error playing track:", error);
                });
        }
        
        updatePlayPauseButton(playerState.isPlaying);
    }

    // Update play/pause button
    function updatePlayPauseButton(isPlaying) {
        if (isPlaying) {
            playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    }

    // Format time (seconds to MM:SS)
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    // Update progress bar
    function updateProgress() {
        const currentTime = playerState.audio.currentTime;
        const duration = playerState.audio.duration || 0;
        
        if (duration > 0) {
            const progressPercent = (currentTime / duration) * 100;
            progressBar.style.width = `${progressPercent}%`;
            
            currentTimeEl.textContent = formatTime(currentTime);
            totalTimeEl.textContent = formatTime(duration);
        }
    }

    // Set progress when user clicks on progress bar
    function setProgress(e) {
        const progressBarWidth = e.currentTarget.clientWidth;
        const clickPosition = e.offsetX;
        const duration = playerState.audio.duration;
        
        if (duration > 0) {
            playerState.audio.currentTime = (clickPosition / progressBarWidth) * duration;
        }
    }

    // Play next track
    function playNext() {
        let nextIndex = playerState.currentTrackIndex + 1;
        if (nextIndex >= playerState.tracks.length) {
            nextIndex = 0; // Loop back to first track
        }
        loadTrack(nextIndex);
        
        if (playerState.isPlaying) {
            playerState.audio.play()
                .catch(error => console.error("Error playing next track:", error));
        }
    }

    // Play previous track
    function playPrev() {
        let prevIndex = playerState.currentTrackIndex - 1;
        if (prevIndex < 0) {
            prevIndex = playerState.tracks.length - 1; // Loop to last track
        }
        loadTrack(prevIndex);
        
        if (playerState.isPlaying) {
            playerState.audio.play()
                .catch(error => console.error("Error playing previous track:", error));
        }
    }

    // Toggle like for current track
    function toggleLike() {
        if (playerState.tracks.length === 0) {
            return;
        }
        
        const track = playerState.tracks[playerState.currentTrackIndex];
        
        fetch(`/soundcloud/api/tracks/${track.id}/like/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                likeBtn.innerHTML = data.action === 'liked' 
                    ? '<i class="fas fa-heart"></i>' 
                    : '<i class="far fa-heart"></i>';
            }
        })
        .catch(error => console.error("Error toggling like:", error));
    }

    // Log play to server
    function logPlayToServer(trackId) {
        fetch(`/soundcloud/api/tracks/${trackId}/play/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `mood=${encodeURIComponent(playerState.currentMood)}`
        })
        .catch(error => console.error("Error logging play:", error));
    }

    // Load tracks for selected mood
    function loadTracksByMood(mood) {
        playerState.currentMood = mood;
        
        // Update mood button UI
        moodButtons.forEach(btn => {
            if (btn.dataset.mood === mood) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        fetch(`/soundcloud/api/tracks/mood/${mood}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.tracks) {
                    playerState.tracks = data.tracks;
                    renderTrackList();
                    if (playerState.tracks.length > 0) {
                        loadTrack(0);
                    }
                }
            })
            .catch(error => console.error("Error loading tracks for mood:", error));
    }

    // Get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Setup event listeners
    function setupEventListeners() {
        // Player controls
        playPauseBtn.addEventListener('click', togglePlayPause);
        prevBtn.addEventListener('click', playPrev);
        nextBtn.addEventListener('click', playNext);
        likeBtn.addEventListener('click', toggleLike);
        
        // Progress bar
        document.querySelector('.progress-bar').addEventListener('click', setProgress);
        
        // Audio events
        playerState.audio.addEventListener('timeupdate', updateProgress);
        playerState.audio.addEventListener('ended', playNext);
        
        // Track list
        tracksContainer.addEventListener('click', e => {
            const trackItem = e.target.closest('.track-item');
            if (trackItem) {
                const index = parseInt(trackItem.dataset.index);
                loadTrack(index);
                playerState.isPlaying = true;
                playerState.audio.play()
                    .then(() => {
                        updatePlayPauseButton(true);
                    })
                    .catch(error => console.error("Error playing track:", error));
            }
        });
        
        // Mood buttons
        moodButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const mood = btn.dataset.mood;
                loadTracksByMood(mood);
            });
        });
    }

    // Initialize player
    initPlayer();
}); 