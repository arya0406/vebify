// Spotify Web Playback SDK Integration

// Player variables
let player;
let deviceId;
let isPlayerActive = false;
let currentTrack = null;
let playerProgressInterval;
let isPlayerReady = false;
let retryAttempts = 0;
const MAX_RETRY_ATTEMPTS = 3;

// DOM elements
const token = document.getElementById('spotify-token').value;
const togglePlayerBtn = document.getElementById('toggle-player');
const playButton = document.getElementById('play-button');
const pauseButton = document.getElementById('pause-button');
const prevButton = document.getElementById('prev-button');
const nextButton = document.getElementById('next-button');
const progressBar = document.getElementById('progress-bar');
const currentTimeLabel = document.getElementById('current-time');
const durationLabel = document.getElementById('duration');
const currentTrackImg = document.getElementById('current-track-img').querySelector('img');
const currentTrackName = document.getElementById('current-track-name');
const currentTrackArtist = document.getElementById('current-track-artist');
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const searchResults = document.getElementById('search-results');
const tracksContainer = document.getElementById('tracks-container');
const moodButtons = document.querySelectorAll('.mood-buttons button');
const spotifyPlayerContainer = document.getElementById('spotifyPlayerContainer');
const spotifyPlayerTrackInfo = document.getElementById('spotifyPlayerTrackInfo');
const spotifyPlayerClose = document.getElementById('spotifyPlayerClose');

// Check if we have a valid token
if (!token) {
    console.error('No Spotify token found');
    alert('Please connect your Spotify account first');
    window.location.href = '/spotify/login/';
}

// Initialize Spotify Web Playback SDK
window.onSpotifyWebPlaybackSDKReady = () => {
    if (!token) {
        console.error('No Spotify token found');
        window.location.href = '/spotify/login/';
        return;
    }

    initializePlayer();
};

// Initialize player
async function initializePlayer() {
    if (retryAttempts >= MAX_RETRY_ATTEMPTS) {
        console.error('Max retry attempts reached');
        return;
    }

    try {
        player = new Spotify.Player({
            name: 'Web Player',
            getOAuthToken: cb => { cb(token); },
            volume: 0.5
        });

        // Error handling
        player.addListener('initialization_error', ({ message }) => {
            console.error('Failed to initialize player:', message);
            retryAttempts++;
            setTimeout(initializePlayer, 1000);
        });
        
        player.addListener('authentication_error', ({ message }) => {
            console.error('Failed to authenticate:', message);
            window.location.href = '/spotify/login/';
        });
        
        player.addListener('account_error', ({ message }) => {
            console.error('Premium account required:', message);
        });
        
        player.addListener('playback_error', ({ message }) => {
            console.error('Failed to perform playback:', message);
            if (currentTrack) {
                setTimeout(() => startPlayback(currentTrack), 1000);
            }
        });

        // Playback status updates
        player.addListener('player_state_changed', state => {
            if (!state) {
                isPlayerReady = false;
                spotifyPlayerTrackInfo.textContent = 'Not Playing';
                return;
            }
            
            currentTrack = state.track_window.current_track;
            updatePlayerInfo(currentTrack);
            
            if (state.paused) {
                spotifyPlayerContainer.classList.add('translate-y-full');
            } else {
                spotifyPlayerContainer.classList.remove('translate-y-full');
            }
        });

        // Ready
        player.addListener('ready', ({ device_id }) => {
            console.log('Player ready');
            deviceId = device_id;
            isPlayerActive = true;
            isPlayerReady = true;
            retryAttempts = 0;
            
            // Set this device as active
            fetch('https://api.spotify.com/v1/me/player', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_ids: [device_id],
                    play: false,
                }),
            }).catch(error => {
                console.error('Error setting active device:', error);
            });
        });

        // Connect to the player
        const success = await player.connect();
        if (!success) {
            throw new Error('Failed to connect to Spotify');
        }

    } catch (error) {
        console.error('Error initializing player:', error);
        retryAttempts++;
        setTimeout(initializePlayer, 1000);
    }
}

// Update player info
function updatePlayerInfo(track) {
    if (!track) return;
    spotifyPlayerTrackInfo.textContent = `${track.name} - ${track.artists[0].name}`;
}

// Play a track
async function playTrack(uri) {
    if (!isPlayerReady || !deviceId) {
        try {
            await initializePlayer();
        } catch (error) {
            console.error('Failed to initialize player:', error);
            return;
        }
    }

    try {
        // Set this device as active and start playback
        await fetch('https://api.spotify.com/v1/me/player', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                device_ids: [deviceId],
                play: true
            }),
        });

        // Start playing the track
        const response = await fetch(`https://api.spotify.com/v1/me/player/play?device_id=${deviceId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                uris: [uri],
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'Failed to play track');
        }

        // Show the player container
        spotifyPlayerContainer.classList.remove('translate-y-full');

    } catch (error) {
        console.error('Error playing track:', error);
        if (error.message.includes('Premium')) {
            alert('Spotify Premium is required for playback');
        }
    }
}

// Handle play button clicks
document.querySelectorAll('.spotify-play-button').forEach(button => {
    button.addEventListener('click', async function() {
        const trackUri = this.dataset.trackUri;
        if (!trackUri) {
            console.error('No track URI provided');
            return;
        }
        await playTrack(trackUri);
    });
});

// Handle player close button
spotifyPlayerClose.addEventListener('click', () => {
    spotifyPlayerContainer.classList.add('translate-y-full');
    if (player) {
        player.pause().catch(error => console.error('Error pausing playback:', error));
    }
});

// Helper function to show player messages
function showPlayerMessage(message, type = 'info') {
    const playerMessages = document.getElementById('player-messages');
    if (playerMessages) {
        playerMessages.className = `alert alert-${type} mt-3`;
        playerMessages.classList.remove('d-none');
        playerMessages.textContent = message;
        
        // Hide message after 5 seconds
        setTimeout(() => {
            playerMessages.classList.add('d-none');
        }, 5000);
    }
}

// Update UI with current track information
function updatePlayerUI(track, state) {
    if (!track) return;
    
    currentTrackImg.src = track.album.images[0].url;
    currentTrackName.textContent = track.name;
    currentTrackArtist.textContent = track.artists.map(artist => artist.name).join(', ');
    
    // Update progress bar
    const duration = state.duration;
    const position = state.position;
    
    if (duration) {
        const percentage = (position / duration) * 100;
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', percentage);
        
        currentTimeLabel.textContent = formatTime(position);
        durationLabel.textContent = formatTime(duration);
    }
}

// Format time in MM:SS
function formatTime(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// Start progress timer
function startProgressTimer(state) {
    clearInterval(playerProgressInterval);
    
    let position = state.position;
    const duration = state.duration;
    const updateFrequency = 1000; // Update every second
    
    playerProgressInterval = setInterval(() => {
        position += updateFrequency;
        
        if (position >= duration) {
            clearInterval(playerProgressInterval);
            return;
        }
        
        const percentage = (position / duration) * 100;
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', percentage);
        
        currentTimeLabel.textContent = formatTime(position);
    }, updateFrequency);
}

// Control buttons event listeners
playButton.addEventListener('click', () => {
    if (player && deviceId) {
        player.resume();
    }
});

pauseButton.addEventListener('click', () => {
    if (player && deviceId) {
        player.pause();
    }
});

prevButton.addEventListener('click', () => {
    if (player && deviceId) {
        player.previousTrack();
    }
});

nextButton.addEventListener('click', () => {
    if (player && deviceId) {
        player.nextTrack();
    }
});

// Search for tracks
searchButton.addEventListener('click', () => {
    const query = searchInput.value.trim();
    if (query) {
        searchSpotify(query);
    }
});

searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const query = searchInput.value.trim();
        if (query) {
            searchSpotify(query);
        }
    }
});

// Search Spotify API
function searchSpotify(query) {
    fetch(`/spotify/search/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Error searching tracks:', error);
            searchResults.innerHTML = '<div class="alert alert-danger">Error searching tracks</div>';
        });
}

// Display search results
function displaySearchResults(data) {
    searchResults.innerHTML = '';
    
    if (!data.tracks || !data.tracks.items.length) {
        searchResults.innerHTML = '<div class="alert alert-info">No tracks found</div>';
        return;
    }
    
    const tracksList = document.createElement('div');
    tracksList.className = 'list-group';
    
    data.tracks.items.forEach(track => {
        const trackItem = document.createElement('div');
        trackItem.className = 'list-group-item track-item';
        
        const artistNames = track.artists.map(artist => artist.name).join(', ');
        
        trackItem.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center flex-grow-1">
                    <img src="${track.album.images.length ? track.album.images[track.album.images.length-1].url : ''}" 
                         alt="${track.name}" width="40" height="40" class="me-3">
                    <div>
                        <h6 class="mb-0">${track.name}</h6>
                        <small class="text-muted">${artistNames}</small>
                    </div>
                </div>
                <div class="ms-3">
                    <button class="btn btn-success btn-sm play-spotify" data-uri="${track.uri}">
                        <i class="fas fa-play me-1"></i> Play on Spotify
                    </button>
                    <a href="${track.external_urls.spotify}" target="_blank" class="btn btn-outline-secondary btn-sm ms-2">
                        <i class="fab fa-spotify"></i> Open
                    </a>
                </div>
            </div>
        `;
        
        const playButton = trackItem.querySelector('.play-spotify');
        playButton.addEventListener('click', (e) => {
            e.preventDefault();
            const uri = e.currentTarget.dataset.uri;
            playTrack(uri);
            
            // Update button state
            const allPlayButtons = document.querySelectorAll('.play-spotify');
            allPlayButtons.forEach(btn => {
                btn.innerHTML = '<i class="fas fa-play me-1"></i> Play on Spotify';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-success');
            });
            
            e.currentTarget.innerHTML = '<i class="fas fa-pause me-1"></i> Playing';
            e.currentTarget.classList.remove('btn-success');
            e.currentTarget.classList.add('btn-danger');
        });
        
        tracksList.appendChild(trackItem);
    });
    
    searchResults.appendChild(tracksList);
}

// Handle mood button clicks
moodButtons.forEach(button => {
    button.addEventListener('click', (e) => {
        // Remove active class from all buttons
        moodButtons.forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active class to clicked button
        e.target.classList.add('active');
        
        // Get mood recommendations
        const moodId = e.target.dataset.moodId;
        getMoodRecommendations(moodId);
    });
});

// Get mood-based recommendations
function getMoodRecommendations(moodId) {
    fetch(`/spotify/recommendations/${moodId}/`)
        .then(response => response.json())
        .then(data => {
            displayRecommendations(data);
        })
        .catch(error => {
            console.error('Error getting recommendations:', error);
            tracksContainer.innerHTML = '<div class="alert alert-danger">Error getting recommendations</div>';
        });
}

// Display recommendations
function displayRecommendations(data) {
    tracksContainer.innerHTML = '';
    
    if (!data.tracks || !data.tracks.length) {
        tracksContainer.innerHTML = '<div class="alert alert-info">No recommendations found</div>';
        return;
    }
    
    data.tracks.forEach(track => {
        const trackItem = document.createElement('div');
        trackItem.className = 'list-group-item track-item';
        
        const artistNames = track.artists.map(artist => artist.name).join(', ');
        
        trackItem.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center flex-grow-1">
                    <img src="${track.album.images.length ? track.album.images[track.album.images.length-1].url : ''}" 
                         alt="${track.name}" width="40" height="40" class="me-3">
                    <div>
                        <h6 class="mb-0">${track.name}</h6>
                        <small class="text-muted">${artistNames}</small>
                    </div>
                </div>
                <div class="ms-3">
                    <button class="btn btn-success btn-sm play-spotify" data-uri="${track.uri}">
                        <i class="fas fa-play me-1"></i> Play on Spotify
                    </button>
                    <a href="${track.external_urls.spotify}" target="_blank" class="btn btn-outline-secondary btn-sm ms-2">
                        <i class="fab fa-spotify"></i> Open
                    </a>
                </div>
            </div>
        `;
        
        const playButton = trackItem.querySelector('.play-spotify');
        playButton.addEventListener('click', (e) => {
            e.preventDefault();
            const uri = e.currentTarget.dataset.uri;
            playTrack(uri);
            
            // Update button state
            const allPlayButtons = document.querySelectorAll('.play-spotify');
            allPlayButtons.forEach(btn => {
                btn.innerHTML = '<i class="fas fa-play me-1"></i> Play on Spotify';
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-success');
            });
            
            e.currentTarget.innerHTML = '<i class="fas fa-pause me-1"></i> Playing';
            e.currentTarget.classList.remove('btn-success');
            e.currentTarget.classList.add('btn-danger');
        });
        
        tracksContainer.appendChild(trackItem);
    });
}

// Get Happy mood recommendations by default when page loads
document.addEventListener('DOMContentLoaded', () => {
    const happyButton = document.querySelector('[data-mood-id="1"]');
    if (happyButton) {
        happyButton.classList.add('active');
        getMoodRecommendations(1);
    }
}); 