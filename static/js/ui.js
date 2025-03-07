// UI utilities
const gameUI = {
    battleLogContainer: null,
    
    // Initialize UI elements
    init: function() {
        // Create battle log if needed
        if (!this.battleLogContainer) {
            this.createBattleLog();
        }
        
        // Add keyboard shortcuts
        this.setupKeyboardShortcuts();
    },
    
    // Create a battle log container
    createBattleLog: function() {
        const container = document.createElement('div');
        container.className = 'battle-log-container';
        container.style.position = 'fixed';
        container.style.bottom = '10px';
        container.style.left = '10px';
        container.style.maxWidth = '300px';
        container.style.maxHeight = '200px';
        container.style.overflowY = 'auto';
        container.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        container.style.color = 'white';
        container.style.padding = '10px';
        container.style.borderRadius = '5px';
        container.style.zIndex = '1000';
        container.style.fontSize = '14px';
        
        document.body.appendChild(container);
        this.battleLogContainer = container;
        
        // Add a title
        const title = document.createElement('div');
        title.textContent = 'Battle Log';
        title.style.fontWeight = 'bold';
        title.style.borderBottom = '1px solid #666';
        title.style.marginBottom = '5px';
        title.style.paddingBottom = '5px';
        
        container.appendChild(title);
    },
    
    // Add a message to the battle log
    addToBattleLog: function(message) {
        if (!this.battleLogContainer) {
            this.createBattleLog();
        }
        
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logEntry.style.marginBottom = '5px';
        logEntry.style.borderBottom = '1px solid #333';
        logEntry.style.paddingBottom = '5px';
        
        this.battleLogContainer.appendChild(logEntry);
        
        // Scroll to bottom
        this.battleLogContainer.scrollTop = this.battleLogContainer.scrollHeight;
    },
    
    // Set up keyboard shortcuts
    setupKeyboardShortcuts: function() {
        document.addEventListener('keydown', function(e) {
            // 'M' key for move mode
            if (e.key === 'm' || e.key === 'M') {
                if (window.setInteractionMode) {
                    window.setInteractionMode('move');
                }
            }
            
            // 'A' key for attack mode
            if (e.key === 'a' || e.key === 'A') {
                if (window.setInteractionMode) {
                    window.setInteractionMode('attack');
                }
            }
            
            // 'D' key for drag/pan mode
            if (e.key === 'd' || e.key === 'D') {
                if (window.setInteractionMode) {
                    window.setInteractionMode('drag');
                }
            }
            
            // '+' key for zoom in
            if (e.key === '+' || e.key === '=') {
                if (window.zoomIn) {
                    window.zoomIn();
                }
            }
            
            // '-' key for zoom out
            if (e.key === '-' || e.key === '_') {
                if (window.zoomOut) {
                    window.zoomOut();
                }
            }
            
            // 'R' key to reset view
            if (e.key === 'r' || e.key === 'R') {
                if (window.resetView) {
                    window.resetView();
                }
            }
            
            // Space to end turn
            if (e.key === ' ') {
                const endTurnButton = document.getElementById('endTurnButton');
                if (endTurnButton) {
                    endTurnButton.click();
                }
            }
        });
    }
};

// Expose functions to window
window.gameUI = gameUI;
window.addToBattleLog = function(message) {
    gameUI.addToBattleLog(message);
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    gameUI.init();
});
