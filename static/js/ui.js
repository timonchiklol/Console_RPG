// UI-related functionality
class GameUI {
    constructor(config) {
        this.config = config;
        this.setupEventListeners();
        this.adjustCanvasSize();
    }

    setupEventListeners() {
        // Terrain button handlers
        document.querySelectorAll('.terrain-btn').forEach(btn => {
            btn.addEventListener('click', () => this.changeTerrain(btn.dataset.terrain));
        });

        // End turn button handler
        const endTurnButton = document.getElementById('endTurnButton');
        if (endTurnButton) {
            endTurnButton.onclick = (event) => this.handleEndTurn(event.target);
        }

        // Adjust canvas size on window resize
        window.addEventListener('resize', () => {
            this.adjustCanvasSize();
            this.fixScrolling();
        });
        
        // Call fixScrolling when window is fully loaded to ensure correct formatting
        window.addEventListener('load', () => this.fixScrolling());
        
        // Ensure page is scrollable
        this.fixScrolling();
    }
    
    // Make sure page is scrollable
    fixScrolling() {
        // Fix the game container for proper scrolling
        const gameContainer = document.querySelector('.game-container');
        if (gameContainer) {
            gameContainer.style.display = 'flex';
            gameContainer.style.flexDirection = 'column';
            gameContainer.style.height = '100vh';
            gameContainer.style.overflow = 'hidden';
        }
        
        // Make the main content area scrollable
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.style.height = 'auto';
            mainContent.style.flex = '1';
            mainContent.style.overflowY = 'auto';
            mainContent.style.overflowX = 'hidden';
            mainContent.style.padding = '0 1rem';
        }
    }
    
    // Adjust canvas size based on container width
    adjustCanvasSize() {
        const canvas = document.getElementById('hexCanvas');
        if (!canvas) return;
        
        const container = canvas.parentElement;
        const containerWidth = container.clientWidth;
        
        // Maintain aspect ratio for the hexCanvas
        const aspectRatio = 1.6; // width/height
        const height = containerWidth / aspectRatio;
        
        canvas.width = containerWidth;
        canvas.height = height;
        
        // Redraw the grid with new dimensions
        if (window.drawHexGrid) {
            window.drawHexGrid();
        }
    }

    async handleEndTurn(buttonElement) {
        console.log("End turn clicked");
        
        // Show notification
        window.showNotification("Ending your turn...", "info", buttonElement);
        
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
            console.log("Enemy turn response:", data);
            
            if (data.combat_log) {
                window.showNotification(data.combat_log, "info");
            }
            
            // Update UI
            document.getElementById('char_hp').textContent = data.character_hp;
            document.getElementById('enemy_hp').textContent = data.enemy_hp;
            
            // Update enemy position if it moved
            if (data.enemy_pos) {
                window.enemyPos = data.enemy_pos;
                window.drawHexGrid();
                window.showNotification("Enemy has moved!", "info");
            }
        } catch (error) {
            console.error('Error during enemy turn:', error);
            window.showNotification('Error during enemy turn: ' + error.message, "error", buttonElement);
        }
    }

    changeTerrain(terrainType) {
        window.currentTerrain = this.config.battlefield.terrain_types[terrainType];
        window.initializeHexColors();
        window.drawHexGrid();
        window.showNotification(`Changed terrain to ${terrainType}`, "info");
    }

    addToBattleLog(message, targetElement = null) {
        // Use the notification system instead
        window.showNotification(message, "info", targetElement);
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