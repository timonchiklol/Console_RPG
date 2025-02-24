// UI-related functionality
class GameUI {
    constructor(config) {
        this.config = config;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Terrain button handlers
        document.querySelectorAll('.terrain-btn').forEach(btn => {
            btn.addEventListener('click', () => this.changeTerrain(btn.dataset.terrain));
        });

        // End turn button handler
        const endTurnButton = document.getElementById('endTurnButton');
        if (endTurnButton) {
            endTurnButton.onclick = () => this.handleEndTurn();
        }

        // Initialize end turn button style
        this.updateEndTurnButton();
    }

    async handleEndTurn() {
        console.log("End turn clicked"); // Debug log
        
        // Reset movement state
        window.hasMoved = false;
        window.playerSpeed = this.config.player.stats.speed;
        window.currentPath = [];
        this.clearHighlight();
        
        // Update UI
        document.getElementById('char_speed').textContent = `${window.playerSpeed}/${this.config.player.stats.speed}`;
        window.drawHexGrid();
        
        // Enemy turn
        try {
            const response = await fetch('/api/enemy_attack', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log("Enemy turn response:", data); // Debug log
            
            if (data.combat_log) {
                this.addToBattleLog(data.combat_log);
            }
            
            // Update UI
            document.getElementById('char_hp').textContent = data.character_hp;
            document.getElementById('enemy_hp').textContent = data.enemy_hp;
            
            // Update enemy position if it moved
            if (data.enemy_pos) {
                window.enemyPos = data.enemy_pos;
                window.drawHexGrid();
            }
        } catch (error) {
            console.error('Error during enemy turn:', error);
            this.addToBattleLog('Error during enemy turn: ' + error.message);
        }
    }

    updateEndTurnButton() {
        const endTurnButton = document.getElementById('endTurnButton');
        if (endTurnButton) {
            // Apply styles
            const styles = {
                'display': 'block',
                'marginTop': '10px',
                'padding': '10px 20px',
                'backgroundColor': '#4CAF50',
                'color': 'white',
                'border': 'none',
                'borderRadius': '4px',
                'cursor': 'pointer',
                'transition': 'background-color 0.3s ease',
                'fontSize': '16px',
                'fontWeight': 'bold'
            };
            
            Object.assign(endTurnButton.style, styles);
            
            // Add hover effect
            endTurnButton.addEventListener('mouseover', function() {
                this.style.backgroundColor = '#45a049';
            });
            
            endTurnButton.addEventListener('mouseout', function() {
                this.style.backgroundColor = '#4CAF50';
            });
        }
    }

    changeTerrain(terrainType) {
        window.currentTerrain = this.config.battlefield.terrain_types[terrainType];
        window.initializeHexColors();
        window.drawHexGrid();
    }

    addToBattleLog(message) {
        const battleLog = document.getElementById('battleLog');
        const entry = document.createElement('div');
        entry.textContent = message;
        battleLog.appendChild(entry);
        battleLog.scrollTop = battleLog.scrollHeight;
    }

    clearHighlight() {
        window.highlightedCells = [];
        window.currentRange = 0;
        window.currentAOE = 0;
        window.selectedCell = null;
        window.drawHexGrid();
    }

    highlightRange(range, aoe = 0) {
        window.currentRange = range;
        window.currentAOE = aoe;
        window.highlightedCells = window.getCellsInRange(window.playerPos, range);
        window.drawHexGrid();
    }

    checkAdjacent() {
        return window.checkAdjacent();
    }

    isInRange(targetCol, targetRow, range) {
        return window.isInRange(targetCol, targetRow, range);
    }
}

// Initialize UI manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gameUI = new GameUI(window.GAME_CONFIG);
}); 