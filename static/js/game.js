// Add CSS animations for dice rolling
const style = document.createElement('style');
style.textContent = `
  @keyframes spin-bounce {
    0%, 100% { transform: rotate(0deg) scale(1); }
    25% { transform: rotate(90deg) scale(1.1); }
    50% { transform: rotate(180deg) scale(1); }
    75% { transform: rotate(270deg) scale(1.1); }
  }

  @keyframes particle-1 { 0%, 100% { transform: rotate(0deg) translateY(-10px) scale(1); opacity: 1; }
    50% { transform: rotate(0deg) translateY(-15px) scale(0.5); opacity: 0.5; } }
  @keyframes particle-2 { 0%, 100% { transform: rotate(60deg) translateY(-10px) scale(1); opacity: 1; }
    50% { transform: rotate(60deg) translateY(-15px) scale(0.5); opacity: 0.5; } }
  @keyframes particle-3 { 0%, 100% { transform: rotate(120deg) translateY(-10px) scale(1); opacity: 1; }
    50% { transform: rotate(120deg) translateY(-15px) scale(0.5); opacity: 0.5; } }
  @keyframes particle-4 { 0%, 100% { transform: rotate(180deg) translateY(-10px) scale(1); opacity: 1; }
    50% { transform: rotate(180deg) translateY(-15px) scale(0.5); opacity: 0.5; } }
  @keyframes particle-5 { 0%, 100% { transform: rotate(240deg) translateY(-10px) scale(1); opacity: 1; }
    50% { transform: rotate(240deg) translateY(-15px) scale(0.5); opacity: 0.5; } }
  @keyframes particle-6 { 0%, 100% { transform: rotate(300deg) translateY(-10px) scale(1); opacity: 1; }
    50% { transform: rotate(300deg) translateY(-15px) scale(0.5); opacity: 0.5; } }

  @keyframes gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }

  .animate-spin-bounce {
    animation: spin-bounce 1s infinite linear;
  }

  .animate-gradient {
    background-size: 200% 200%;
    animation: gradient 2s ease infinite;
  }

  @keyframes roll-and-bounce {
    0% { transform: rotate3d(1, 1, 1, 0deg) translateY(0); }
    25% { transform: rotate3d(2, -1, 1, 180deg) translateY(-20px); }
    50% { transform: rotate3d(-1, 2, 1, 360deg) translateY(0); }
    75% { transform: rotate3d(1, 1, -2, 540deg) translateY(-10px); }
    100% { transform: rotate3d(1, 1, 1, 720deg) translateY(0); }
  }

  @keyframes glow {
    0%, 100% { filter: drop-shadow(0 0 2px #fbbf24) drop-shadow(0 0 4px #fbbf24); }
    50% { filter: drop-shadow(0 0 6px #fbbf24) drop-shadow(0 0 12px #fbbf24); }
  }

  @keyframes float {
    0%, 100% { transform: translateY(0) rotate3d(1, 1, 1, 0deg); }
    50% { transform: translateY(-5px) rotate3d(1, 1, 1, 10deg); }
  }

  .dice-container {
    position: relative;
    width: 80px;
    height: 80px;
    perspective: 1200px;
    transform-style: preserve-3d;
  }

  .dice-rolling {
    animation: roll-and-bounce 1.5s cubic-bezier(0.4, 0, 0.2, 1);
    transform-style: preserve-3d;
  }

  .dice-floating {
    animation: float 2s infinite ease-in-out;
    transform-style: preserve-3d;
  }

  .dice-glowing {
    animation: glow 2s infinite ease-in-out;
  }

  .roll-button {
    position: relative;
    overflow: visible;
    transition: all 0.3s ease;
    padding: 20px;
  }

  .roll-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(251, 191, 36, 0.3);
  }

  .roll-button:active {
    transform: translateY(0);
  }

  .roll-button::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(251, 191, 36, 0.4) 0%, rgba(251, 191, 36, 0) 70%);
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .roll-button:hover::after {
    opacity: 1;
  }
`;
document.head.appendChild(style);

const gameApp = Vue.createApp({
    data() {
        return {
            gameState: {},
            messages: [],
            pendingMessage: null,
            userInput: '',
            isLoading: false,
            diceNeeded: false,
            diceReason: '',
            diceType: 'd20',
            diceRollRequest: null,
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
            customProficient: false,
            currentFace: 1,
            timeoutId: null,
            transitionDuration: 500,
            animationDuration: 3000,
            lastFace: null
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
            const translations = {
                'roll': 'Roll',
                'check': 'check',
                'with_proficiency': 'with proficiency',
            };
            return translations[key] || translationManager.translate(key);
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
                        this.diceReason = (data.dice_roll_request && data.dice_roll_request.reason) || '';
                        this.diceRollRequest = data.dice_roll_request;
                        // Reset dice state for new roll
                        this.currentFace = null;
                        this.diceRolling = false;
                        console.log('Dice roll request data:', data);
                    } else {
                        this.diceNeeded = false;
                        this.diceReason = '';
                        this.diceRollRequest = null;
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
            // Prevent rolling if already rolling
            if (this.diceRolling) return;
            
            // Start dice animation
            this.diceRolling = true;
            this.isThinking = true;
            
            try {
                const rollResponse = await fetch('/roll_dice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dice_type: this.diceType })
                });
                const rollData = await rollResponse.json();
                
                if (rollData.error) {
                    alert(rollData.error);
                    this.diceRolling = false;
                    return;
                }
                
                // Get the base roll from the detailed result
                const baseRoll = rollData.detailed_result?.base_roll || rollData.roll;
                
                // Add roll message with animation
                this.pendingMessage = {
                    id: 'pending-roll',
                    type: 'player',
                    message: rollData.roll_details_message || `${this.translate('rolled_message').replace('{roll}', rollData.roll).replace('{dice}', this.diceType)}`,
                    player_name: this.gameState.name || this.translate('you'),
                    detailed_result: rollData.detailed_result
                };
                
                // Show dice animation and then process the roll
                this.timeoutId = setTimeout(async () => {
                    this.diceRolling = false;
                    
                    // Set the face to match the base roll
                    this.currentFace = baseRoll;
                    
                    // Process the roll after showing the result
                    setTimeout(async () => {
                        const processResponse = await fetch('/process_roll', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                roll: rollData.roll, 
                                dice_type: this.diceType,
                                detailed_result: rollData.detailed_result
                            })
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
                        
                        // Hide dice overlay after processing
                        setTimeout(() => {
                            this.diceNeeded = false;
                            this.resetDice();
                            this.pendingMessage = null;
                            this.isThinking = false;
                            this.diceRollRequest = null;
                        }, 1000);
                    }, 1000);
                }, this.animationDuration);
                
            } catch (e) {
                console.error(e);
                this.diceRolling = false;
                this.diceNeeded = false;
                this.resetDice();
                this.pendingMessage = null;
                this.isThinking = false;
                this.diceRollRequest = null;
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
                    if (data.dice_roll_required) {
                        this.diceNeeded = true;
                        this.diceType = data.dice_roll_request?.dice_type || 'd20';
                        this.diceReason = data.dice_roll_request?.dice_modifier?.reason || '';
                        this.diceRollRequest = data.dice_roll_request;
                    }
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
        },
        computeAbilityModifier(ability) {
            if (!ability || !this.gameState.ability_scores) return '';
            const score = this.gameState.ability_scores[ability.toLowerCase()] || 10;
            return Math.floor((score - 10) / 2);
        },
        randomFace() {
            let face = Math.floor((Math.random() * 20)) + 1;
            this.lastFace = face === this.lastFace ? this.randomFace() : face;
            return face;
        },
        rollTo(face) {
            clearTimeout(this.timeoutId);
            this.currentFace = face;
        },
        resetDice() {
            this.currentFace = null;
            this.diceRolling = false;
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