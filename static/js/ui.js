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
            
            // Используем нашу новую функцию для обработки хода врага
            if (typeof handleEnemyTurnResponse === 'function') {
                handleEnemyTurnResponse(data);
            } else {
                // Резервный вариант, если функция не определена
                if (data.combat_log) {
                    window.showNotification(data.combat_log, "info");
                }
                
                // Update UI
                document.getElementById('char_hp').textContent = data.character_hp;
                document.getElementById('enemy_hp').textContent = data.enemy_hp;
                
                // Update enemy position
                if (data.enemy_pos) {
                    const oldPos = JSON.stringify(window.enemyPos);
                    const newPos = JSON.stringify(data.enemy_pos);
                    
                    window.enemyPos = data.enemy_pos;
                    window.drawHexGrid();
                    
                    // Показываем сообщение только если позиция действительно изменилась
                    if (oldPos !== newPos) {
                        window.showNotification("Enemy has moved!", "info");
                    }
                }
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

// Изменим функцию handleEnemyTurnResponse для учета статуса врага
function handleEnemyTurnResponse(response) {
    // Обновляем здоровье персонажа и врага
    if (document.getElementById('character_hp')) {
        document.getElementById('character_hp').textContent = response.character_hp;
    }
    if (document.getElementById('enemy_hp')) {
        document.getElementById('enemy_hp').textContent = response.enemy_hp;
    }
    
    // Проверяем статус врага - мы добавили специальный флаг в ответ сервера
    const enemyStatus = response.enemy_status;
    const isFrozenOrParalyzed = enemyStatus === "frozen" || enemyStatus === "paralyzed" ||
                              (response.combat_log && 
                               (response.combat_log.includes("заморожен") || 
                                response.combat_log.includes("парализован")));
    
    // Обновляем позицию врага и проверяем движение
    if (response.enemy_pos) {
        const oldPos = JSON.stringify(window.enemyPos || {});
        const newPos = JSON.stringify(response.enemy_pos);
        
        // Обновляем позицию врага в любом случае
        window.enemyPos = response.enemy_pos;
        
        // Показываем сообщение только если:
        // 1. Позиция реально изменилась
        // 2. Враг НЕ заморожен и НЕ парализован
        if (oldPos !== newPos && !isFrozenOrParalyzed) {
            console.log("Enemy moved from", oldPos, "to", newPos);
            if (window.showNotification) {
                window.showNotification("Enemy has moved!", "info");
            }
        }
    }
    
    // Перерисовываем поле
    if (window.drawHexGrid) {
        window.drawHexGrid();
    }
    
    // Добавляем боевой лог
    if (response.combat_log) {
        if (window.showNotification) {
            window.showNotification(response.combat_log, "info");
        }
        
        if (window.addToBattleLog) {
            window.addToBattleLog(response.combat_log);
        }
    }

    // Добавим в handleEnemyTurnResponse дополнительные отладочные сообщения
    console.log("Enemy position from server:", response.enemy_pos);
    console.log("Current enemy position:", window.enemyPos);
    console.log("Is frozen or paralyzed:", isFrozenOrParalyzed);
} 