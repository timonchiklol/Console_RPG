// Get translations
const translations = getTranslations();

// Translate the page based on saved language
translatePage();

// Create Vue app
const app = Vue.createApp({
    data() {
        return {
            playerName: '',
            joinRoomId: '',
            feedbackVisible: false,
            settingsVisible: false,
            language: document.documentElement.lang || 'en'
        };
    },
    methods: {
        translate(key) {
            return translations[this.language]?.[key] || key;
        },
        toggleSettings() {
            this.settingsVisible = !this.settingsVisible;
            console.log('Settings visibility toggled:', this.settingsVisible);
        },
        closeSettings() {
            this.settingsVisible = false;
            console.log('Settings closed');
        },
        async createRoom() {
            if (!this.playerName.trim()) return;
            
            try {
                // First set the language
                await fetch('/start_game', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ language: this.language }),
                });
                
                // Then create the room
                const response = await fetch('/create_room', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ player_name: this.playerName }),
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    // Redirect to character creation
                    window.location.href = '/character';
                } else {
                    console.error('Error creating room:', data.message);
                }
            } catch (error) {
                console.error('Error creating room:', error);
            }
        },
        async joinRoom() {
            if (!this.playerName.trim() || !this.joinRoomId.trim()) return;
            
            try {
                const response = await fetch('/join_room', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        player_name: this.playerName,
                        room_id: this.joinRoomId.trim()
                    }),
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    // Check if player has character
                    const player = data.players[data.player_id];
                    
                    if (player && player.race && player.class_name) {
                        // Player has character, go to game
                        window.location.href = '/game';
                    } else {
                        // Player needs to create character
                        window.location.href = '/character';
                    }
                } else {
                    console.error('Error joining room:', data.message);
                    alert(this.translate('room_not_found'));
                }
            } catch (error) {
                console.error('Error joining room:', error);
                alert(this.translate('join_error'));
            }
        },
        async changeLanguage() {
            try {
                // Save language to server
                await fetch('/start_game', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ language: this.language }),
                });
                
                // Update page language
                document.documentElement.lang = this.language;
                translatePage(this.language);
                this.closeSettings();
                
                // Reload translations
                Object.assign(translations, getTranslations());
            } catch (error) {
                console.error('Error changing language:', error);
            }
        }
    },
    mounted() {
        // Translate the page on load
        translatePage(this.language);
        
        // Ensure settings menu is closed on initial load
        this.settingsVisible = false;
        
        // Add event listener for Escape key to close settings
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.settingsVisible) {
                this.closeSettings();
            }
        });
    }
});

// Mount the app
app.mount('#app'); 