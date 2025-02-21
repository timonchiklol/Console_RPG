const gameApp = Vue.createApp({
    data() {
        return {
            gameState: {},
            messages: [],
            pendingMessage: null,
            userInput: '',
            isLoading: false,
            diceNeeded: false,
            diceType: 'd20',
            room: {},
            diceRolling: false,
            showPlayers: false,
            showStats: false,
            codeCopied: false,
            wasJustCopied: false,
            isThinking: false,
            testMode: window.TEST_MODE === "true",
            customType: 'normal',
            customDice: 'd20',
            customAbility: 'strength',
            customProficient: false
        };
    },
    computed: {
        allMessages() {
            let result = [...this.messages];
            if (this.pendingMessage) {
                result.push(this.pendingMessage);
            }
            if (this.isThinking) {
                result.push({ id: 'thinking', type: 'thinking' });
            }
            return result;
        },
        currentPlayer() {
            return this.gameState;
        }
    },
    methods: {
        translate(key) {
            return translationManager.translate(key);
        },
        formatMessage(message) {
            if (!message) return '';
            // Replace **text** with <strong>text</strong> for bold formatting
            return message.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold">$1</strong>');
        },
        resetCopyState() {
            if (this.codeCopied) {
                this.wasJustCopied = true;
            } else {
                this.wasJustCopied = false;
            }
        },
        async copyRoomCode() {
            if (!this.room.room_id) return;
            
            try {
                await navigator.clipboard.writeText(this.room.room_id);
                this.codeCopied = true;
                setTimeout(() => {
                    this.codeCopied = false;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy room code:', err);
            }
        },
        togglePlayers() {
            this.showPlayers = !this.showPlayers;
        },
        toggleStats() {
            this.showStats = !this.showStats;
            if (this.showStats) {
                this.showPlayers = false;
            }
        },
        async sendMessage() {
            if (!this.userInput.trim()) return;
            
            const messageText = this.userInput;
            this.userInput = ''; // Clear input immediately
            
            // Add pending message immediately
            this.pendingMessage = {
                id: 'pending',
                type: 'player',
                message: messageText,
                player_name: this.gameState.name || this.translate('you')
            };
            
            // Show thinking indicator
            this.isThinking = true;
            
            this.isLoading = true;
            try {
                const response = await fetch('/game_action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: messageText })
                });
                const data = await response.json();
                if (data.error) {
                    alert(data.error);
                } else {
                    this.gameState = data.player;
                    if (data.room) {
                        this.room = data.room;
                    }
                    if (data.dice_roll_required) {
                        this.diceNeeded = true;
                        this.diceType = (data.dice_roll_request && data.dice_roll_request.dice_type) || 'd20';
                        console.log('Dice roll request data:', data);
                    } else {
                        this.diceNeeded = false;
                    }
                    if (data.messages) {
                        this.messages = data.messages;
                    }
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.isLoading = false;
                this.pendingMessage = null;
                this.isThinking = false;
            }
        },
        async rollDice() {
            if (this.diceRolling) return;
            
            // Show thinking indicator immediately
            this.diceRolling = true;
            this.isThinking = true;
            
            try {
                const rollResponse = await fetch('/roll_dice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dice_type: 'd20' })  // Always send d20
                });
                const rollData = await rollResponse.json();
                if (rollData.error) {
                    alert(rollData.error);
                    return;
                }
                
                // Add roll message immediately
                this.pendingMessage = {
                    id: 'pending-roll',
                    type: 'player',
                    message: translationManager.translate('rolled_message')
                        .replace('{roll}', rollData.roll)
                        .replace('{dice}', 'd20'),
                    player_name: this.gameState.name || this.translate('you')
                };
                
                const processResponse = await fetch('/process_roll', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ roll: rollData.roll, dice_type: 'd20' })
                });
                const processData = await processResponse.json();
                if (processData.error) {
                    alert(processData.error);
                } else {
                    this.gameState = processData.player;
                    if (processData.messages) {
                        this.messages = processData.messages;
                    }
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.diceRolling = false;
                this.diceNeeded = false;
                this.pendingMessage = null;
                this.isThinking = false;
            }
        },
        async saveGame() {
            try {
                const response = await fetch('/save_game', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
                alert(data.message);
            } catch (e) {
                console.error(e);
            }
        },
        async loadGame() {
            try {
                const response = await fetch('/load_game', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
                if (data.status === 'success') {
                    this.gameState = data.player;
                    alert(data.message);
                } else {
                    alert(data.error || data.message || this.translate('load_game_error'));
                }
            } catch (e) {
                console.error(e);
            }
        },
        async leaveRoom() {
            if (!confirm(this.translate('leave_confirm'))) return;
            try {
                const response = await fetch('/leave_room', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
                if (data.status === 'success') {
                    window.location.href = '/';
                } else {
                    alert(data.message || this.translate('leave_room_error'));
                }
            } catch (e) {
                console.error(e);
            }
        },
        async loadInitialState() {
            try {
                const response = await fetch('/get_room_state');
                const data = await response.json();
                if (data.status === 'success') {
                    if (data.player) {
                        this.gameState = data.player;
                        // Ensure ability_scores is properly set
                        if (data.player.ability_scores) {
                            this.gameState.ability_scores = data.player.ability_scores;
                        }
                    }
                    this.messages = data.messages || [];
                    this.room = data.room;
                }
            } catch (e) {
                console.error(e);
            }
        },
        async customRoll() {
            // Build the dice command based on customType:
            let diceCommand = '';
            if (this.customType === 'normal') {
                diceCommand = this.customDice.trim();
            } else if (this.customType === 'ability') {
                diceCommand = 'ability_check:' + this.customAbility;
                if (this.customProficient) {
                    diceCommand += ':proficient';
                }
            }
            console.log('Custom Dice Command:', diceCommand);
            
            try {
                // First, roll the dice
                const rollResponse = await fetch('/roll_dice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dice_type: diceCommand })
                });
                const rollData = await rollResponse.json();
                if (rollData.error) {
                    alert(rollData.error);
                    return;
                }
                
                // Now, process the roll with game logic (simulate Gemini response)
                const processResponse = await fetch('/process_roll', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ roll: rollData.roll, dice_type: diceCommand })
                });
                const processData = await processResponse.json();
                if (processData.error) {
                    alert(processData.error);
                    return;
                }
                
                // Update game state and messages
                this.gameState = processData.player;
                if (processData.room) {
                    this.room = processData.room;
                }
                if (processData.messages) {
                    this.messages = processData.messages;
                }
                
                // Show the outcome with detailed dice info and game response
                alert(`Roll: ${rollData.roll}\nDetailed: ${JSON.stringify(rollData.detailed_result)}\n\nGame Response: ${processData.message || processData.response}`);
            } catch (e) {
                console.error(e);
            }
        },
        async testRoll() {
            try {
                const response = await fetch('/test_roll?dice_type=d20');
                const data = await response.json();
                if (data.error) {
                    alert(data.error);
                } else {
                    console.log('Test Roll:', data);
                    alert(`Roll: ${data.roll}\nDetails: ${JSON.stringify(data.detailed_result)}`);
                }
            } catch (e) {
                console.error(e);
            }
        },
        async testBattle() {
            try {
                const response = await fetch('/test_battle');
                const data = await response.json();
                if (data.error) {
                    alert(data.error);
                } else {
                    console.log('Test Battle:', data);
                    alert(`Battle Test:\nResponse: ${data.combat_response}\nEnemy: ${JSON.stringify(data.enemy)}\nIn Combat: ${data.in_combat}`);
                }
            } catch (e) {
                console.error(e);
            }
        }
    },
    watch: {
        allMessages: {
            handler() {
                this.$nextTick(() => {
                    if (this.$refs.messagesContainer) {
                        this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight;
                    }
                });
            },
            deep: true
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
    
    const app = gameApp.mount('#game-app');
    app.loadInitialState();
}); 