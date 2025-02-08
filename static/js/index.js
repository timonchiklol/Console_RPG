const indexApp = Vue.createApp({
    data() {
        return {
            playerName: '',
            joinRoomId: '',
            roomJoined: false,
            roomId: '',
            feedbackVisible: false
        };
    },
    methods: {
        translate(key) {
            return translationManager.translate(key);
        },
        async createRoom() {
            if (!this.playerName.trim()) return;
            try {
                const response = await fetch('/create_room', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ player_name: this.playerName })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    this.roomId = data.room_id;
                    this.roomJoined = true;
                    window.location.href = '/character';
                } else {
                    alert(this.translate('room_creation_error'));
                }
            } catch (e) {
                console.error(e);
            }
        },
        async joinRoom() {
            if (!this.playerName.trim() || !this.joinRoomId.trim()) return;
            try {
                const response = await fetch('/join_room', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ player_name: this.playerName, room_id: this.joinRoomId })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    this.roomId = data.room_id;
                    this.roomJoined = true;
                    window.location.href = '/character';
                } else {
                    alert(data.message || this.translate('room_join_error'));
                }
            } catch (e) {
                console.error(e);
            }
        }
    }
});

// Initialize the app after translations are loaded
document.addEventListener('DOMContentLoaded', async () => {
    await translationManager.loadTranslations();
    
    // Update all elements with data-trans attribute
    document.querySelectorAll('[data-trans]').forEach(el => {
        const key = el.getAttribute('data-trans');
        el.textContent = translationManager.translate(key);
    });
    
    indexApp.mount('#app');
}); 