// Initialize game state
let playerPos = { col: 0, row: 0 };  // Will be updated from GAME_CONFIG
let enemyPos = { col: 5, row: 4 };  // This will be set by the server

// Interaction mode flags
let interactionMode = 'move'; // Possible values: 'move', 'attack', 'drag'
let isDragging = false;
let isDrawingPath = false;
let selectedTargetCell = null;
let currentAOECells = [];

// Get player stats from config
const PLAYER = {
    stats: {
        speed: 30,  // Default speed
        ...window.GAME_CONFIG?.player?.stats  // Merge with any server-provided stats
    }
};

// player's current speed, default to config value
let playerSpeed = PLAYER.stats.speed;

let currentPath = [];
let drawingPath = false;

// Add these variables at the top with other globals
let highlightedCells = [];
let currentRange = 0;
let currentAOE = 0;
let previewAOECell = null;  // Add this for AOE preview

// Grid dimensions - use defaults if config is missing
const gridCols = window.GAME_CONFIG?.battlefield?.dimensions?.cols || 20;
const gridRows = window.GAME_CONFIG?.battlefield?.dimensions?.rows || 15;
const hexSize = window.GAME_CONFIG?.battlefield?.dimensions?.hex_size || 30;

// Current terrain settings - add fallbacks
let currentTerrain = window.GAME_CONFIG?.battlefield?.terrain_types?.[window.GAME_CONFIG?.currentTerrain] || {
    hex_fill: {
        colors: ['#2a6b3c'],  // Default green if not provided
        frequency: 0.3
    },
    grid_color: '#1a4020',
    movement_cost: 1
};
let hexColors = [];

// Добавляем переменные для Misty Step
let awaitingMistyStepTarget = false;
let selectedTeleportCell = null;

// Добавляем поддержку Hold Person
let holdPersonActive = false;

// Simple zoom and pan variables
let scale = 1;
let translateX = 0;
let translateY = 0;
let isPanning = false;
let lastMouseX = 0;
let lastMouseY = 0;
let lastTouchX = 0;
let lastTouchY = 0;
let longPressTimer = null;

// Min and max zoom
const MIN_SCALE = 0.5;
const MAX_SCALE = 3.0;

// Helper function for distance calculation
function getDistance(col1, row1, col2, row2) {
    // Basic Euclidean distance for now, can be replaced with a more hex-appropriate distance
    return Math.sqrt(Math.pow(col1 - col2, 2) + Math.pow(row1 - row2, 2));
}

// Function to get current path cost
function getCurrentPathCost() {
    if (currentPath.length < 2) return 0;
    const steps = currentPath.length - 1;
    const terrainMultiplier = currentTerrain.movement_cost || 1;
    return Math.floor(steps * window.GAME_CONFIG.rules.movement.base_cost * terrainMultiplier);
}

// Add zoom in/out helper functions
function zoomIn() {
    zoomCanvas(0.1);
}

function zoomOut() {
    zoomCanvas(-0.1);
}

// Single DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', function() {
    // Initialize hex colors and draw grid
    initializeHexColors();
    drawHexGrid();

    // Attack button handlers
    document.querySelectorAll('.attack-button').forEach(btn => {
        btn.addEventListener('click', function() {
            const attackType = this.dataset.attackType || this.dataset.spellName;
            const range = parseInt(this.dataset.range);
            const aoe = parseInt(this.dataset.aoe) || 0;
            const spellName = this.dataset.spellName;

            console.log('Attack button clicked:', attackType);

            // Clear any previous highlights
            clearHighlight();

            // Show range for spells/attacks if a range is specified
            if (range) {
                highlightRange(playerPos, range, aoe);
            }

            // Call the selectAttack function if it exists
            if (typeof selectAttack === 'function') {
                selectAttack(attackType, range, spellName);
            } else {
                console.error('selectAttack function is not defined');
            }
        });
    });

    // Apply move button handler
    const applyMoveButton = document.getElementById('applyMoveButton');
    if (applyMoveButton) {
        applyMoveButton.addEventListener('click', function() {
            console.log('Apply Move button clicked');
            applyMove();
        });
    }

    // End turn button handler
    const endTurnButton = document.getElementById('endTurnButton');
    if (endTurnButton) {
        endTurnButton.addEventListener('click', async function() {
            console.log('End turn clicked');
            
            // Reset movement state
            playerSpeed = PLAYER.stats.speed;
            currentPath = [];
            clearHighlight();
            
            // Update UI
            const charSpeedElem = document.getElementById('char_speed');
            if (charSpeedElem) {
                charSpeedElem.textContent = `${playerSpeed}/${PLAYER.stats.speed}`;
            }
            
            // Убеждаемся, что кнопка движения активна для следующего хода
            const applyMoveButton = document.getElementById('applyMoveButton');
            if (applyMoveButton) {
                applyMoveButton.disabled = false;
            }
            
            drawHexGrid();
            
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
                console.log('Enemy turn response:', data);
                
                if (data.combat_log) {
                    if (typeof addToBattleLog === 'function') {
                        addToBattleLog(data.combat_log);
                    } else {
                        console.error('addToBattleLog function is not defined');
                    }
                }
                
                const charHPElem = document.getElementById('char_hp');
                const enemyHPElem = document.getElementById('enemy_hp');
                if (charHPElem) {
                    charHPElem.textContent = data.character_hp;
                }
                if (enemyHPElem) {
                    enemyHPElem.textContent = data.enemy_hp;
                }
                
                if (data.enemy_pos) {
                    enemyPos = data.enemy_pos;
                    drawHexGrid();
                }
            } catch (error) {
                console.error('Error during enemy turn:', error);
                if (typeof addToBattleLog === 'function') {
                    addToBattleLog('Error during enemy turn: ' + error.message);
                }
            }
        });
    }

    // Add zoom button control in corner
    addZoomControls();
    
    // Update player position from game config
    updatePlayerPosition();
    
    // Set up event handlers for canvas
    setupCanvasEvents();
    
    // Update end turn button style
    updateEndTurnButton();
});

// Function to add zoom controls
function addZoomControls() {
    const container = document.createElement('div');
    container.className = 'zoom-controls';
    container.style.position = 'absolute';
    container.style.bottom = '10px';
    container.style.right = '10px';
    container.style.zIndex = '1000';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.gap = '5px';
    
    // Add zoom in button
    const zoomInBtn = document.createElement('button');
    zoomInBtn.innerHTML = '🔍+';
    zoomInBtn.className = 'bg-gray-800 hover:bg-gray-700 text-white rounded p-2';
    zoomInBtn.onclick = function() {
        zoomCanvas(0.1);
    };
    
    // Add zoom out button
    const zoomOutBtn = document.createElement('button');
    zoomOutBtn.innerHTML = '🔍-';
    zoomOutBtn.className = 'bg-gray-800 hover:bg-gray-700 text-white rounded p-2';
    zoomOutBtn.onclick = function() {
        zoomCanvas(-0.1);
    };
    
    // Add reset button
    const resetBtn = document.createElement('button');
    resetBtn.innerHTML = '↺';
    resetBtn.className = 'bg-gray-800 hover:bg-gray-700 text-white rounded p-2';
    resetBtn.onclick = function() {
        resetView();
    };
    
    // Add buttons to container
    container.appendChild(zoomInBtn);
    container.appendChild(zoomOutBtn);
    container.appendChild(resetBtn);
    
    // Add container to canvas container
    const canvasContainer = document.querySelector('.canvas-container');
    if (canvasContainer) {
        canvasContainer.appendChild(container);
    }
}

// Set up canvas event handlers
function setupCanvasEvents() {
    const canvas = document.getElementById('hexCanvas');
    if (!canvas) return;
    
    // Add interaction mode controls
    addInteractionControls();
    
    // Mouse wheel for zoom
    canvas.addEventListener('wheel', function(e) {
        e.preventDefault(); // Prevent page scrolling
        const delta = e.deltaY < 0 ? 0.1 : -0.1;
        zoomCanvas(delta, e.offsetX, e.offsetY);
    });
    
    // Variables for pinch zoom
    let initialPinchDistance = 0;
    let initialScale = 1;
    
    // Touch start
    canvas.addEventListener('touchstart', function(e) {
        const rect = canvas.getBoundingClientRect();
        
        // Handle pinch zoom
        if (e.touches.length === 2) {
            // Store initial distance for pinch zoom
            initialPinchDistance = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            initialScale = scale;
        } 
        // Handle panning or path drawing
        else if (e.touches.length === 1) {
            const touch = e.touches[0];
            
            // Store touch position for panning
            lastTouchX = touch.clientX;
            lastTouchY = touch.clientY;
            
            // Calculate transformed coordinates for path/selection
            const x = (touch.clientX - rect.left - translateX) / scale;
            const y = (touch.clientY - rect.top - translateY) / scale;
            const cell = getCellFromPixel(x, y);
            
            if (interactionMode === 'move') {
                // If touching player position, start drawing path
                if (cell && cell.col === playerPos.col && cell.row === playerPos.row) {
                    isDrawingPath = true;
                    currentPath = [playerPos];
                    drawHexGrid();
                } else if (cell && playerSpeed > 0) {
                    // Allow starting the path from any position by clicking
                    currentPath = computePath(playerPos, cell);
                    drawHexGrid();
                }
                // Otherwise, switch to panning if long press
                else {
                    // Will be handled by timeout for long press
                    isDragging = false;
                    longPressTimer = setTimeout(() => {
                        setInteractionMode('drag');
                        isDragging = true;
                    }, 500); // 500ms for long press
                }
            } else if (interactionMode === 'attack') {
                // Handle attack targeting - check if in range
                if (cell && highlightedCells.some(c => c.col === cell.col && c.row === cell.row)) {
                    selectedTargetCell = cell;
                    currentAOECells = currentAOE > 0 ? getCellsInAOE(cell, currentAOE) : [];
                    drawHexGrid();
                }
            } else if (interactionMode === 'drag') {
                // Start panning
                isDragging = true;
            }
        }
    });
    
    // Touch move
    canvas.addEventListener('touchmove', function(e) {
        e.preventDefault(); // Prevent scrolling
        
        // Clear long press timer on movement
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
        }
        
        const rect = canvas.getBoundingClientRect();
        
        // Handle pinch zoom
        if (e.touches.length === 2) {
            const curDistance = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
            
            const ratio = curDistance / initialPinchDistance;
            const newScale = Math.min(Math.max(initialScale * ratio, MIN_SCALE), MAX_SCALE);
            
            // Zoom toward center of two fingers
            const touchCenter = {
                x: (e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left,
                y: (e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top
            };
            
            const scaleDiff = newScale - scale;
            translateX = translateX - (touchCenter.x - translateX) * (scaleDiff / scale);
            translateY = translateY - (touchCenter.y - translateY) * (scaleDiff / scale);
            scale = newScale;
            
            drawHexGrid();
        } 
        // Handle panning
        else if (e.touches.length === 1) {
            const touch = e.touches[0];
            
            if (interactionMode === 'drag' && isDragging) {
                const dx = touch.clientX - lastTouchX;
                const dy = touch.clientY - lastTouchY;
                
                translateX += dx;
                translateY += dy;
                
                lastTouchX = touch.clientX;
                lastTouchY = touch.clientY;
                
                drawHexGrid();
            }
            // Handle path drawing
            else if (interactionMode === 'move' && isDrawingPath) {
                const x = (touch.clientX - rect.left - translateX) / scale;
                const y = (touch.clientY - rect.top - translateY) / scale;
                const cell = getCellFromPixel(x, y);
                
                if (cell) {
                    // Don't allow moving to enemy position
                    if (cell.col === enemyPos.col && cell.row === enemyPos.row) {
                        return;
                    }
                    
                    // Calculate path to current cell
                    currentPath = computePath(playerPos, cell);
                    drawHexGrid();
                }
            }
            // Handle attack targeting on touch move (for previewing AOE)
            else if (interactionMode === 'attack') {
                const x = (touch.clientX - rect.left - translateX) / scale;
                const y = (touch.clientY - rect.top - translateY) / scale;
                const cell = getCellFromPixel(x, y);
                
                if (cell && highlightedCells.some(c => c.col === cell.col && c.row === cell.row)) {
                    // Update AOE preview but don't select yet
                    previewAOECell = cell;
                    drawHexGrid();
                }
            }
        }
    });
    
    // Touch end
    canvas.addEventListener('touchend', function() {
        // Clear long press timer
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
        }
        
        isPanning = false;
        isDrawingPath = false;
        isDragging = false;
    });
    
    // Mouse events
    canvas.addEventListener('mousedown', function(e) {
        // Get transformed coordinates
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left - translateX) / scale;
        const y = (e.clientY - rect.top - translateY) / scale;
        const cell = getCellFromPixel(x, y);
        
        // Store mouse position for panning
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
        
        // Handle special case: Misty Step target selection
        if (awaitingMistyStepTarget) {
            handleMistyStepTargetSelection(cell);
            return;
        }
        
        // Handle special case: Hold Person target selection
        if (holdPersonActive) {
            handleHoldPersonTargetSelection(cell);
            return;
        }
        
        // Right mouse button or Alt/Ctrl/Shift + left button always triggers drag mode
        if (e.button === 2 || e.altKey || e.ctrlKey || e.shiftKey) {
            e.preventDefault();
            setInteractionMode('drag');
            isDragging = true;
            canvas.style.cursor = 'grabbing';
            return;
        }
        
        // Handle based on current interaction mode
        if (interactionMode === 'move') {
            if (cell) {
                // Check if we're on the player's position or if a path already exists
                if ((cell.col === playerPos.col && cell.row === playerPos.row) || currentPath.length > 0) {
                    if (playerSpeed <= 0) return; // No movement left
                    
                    isDrawingPath = true;
                    if (currentPath.length === 0) {
                        currentPath = [playerPos];
                    }
                    drawHexGrid();
                } else {
                    // Start a new path from player to this cell
                    if (playerSpeed > 0) {
                        currentPath = computePath(playerPos, cell);
                        drawHexGrid();
                    }
                }
            }
        }
        else if (interactionMode === 'attack') {
            if (cell && highlightedCells.some(c => c.col === cell.col && c.row === cell.row)) {
                selectedTargetCell = cell;
                currentAOECells = currentAOE > 0 ? getCellsInAOE(cell, currentAOE) : [];
                drawHexGrid();
                
                // Update the attack preview if available
                updateAttackPreview(cell);
            }
        }
        else if (interactionMode === 'drag') {
            isDragging = true;
            canvas.style.cursor = 'grabbing';
        }
    });
    
    // Mouse move
    canvas.addEventListener('mousemove', function(e) {
        const rect = canvas.getBoundingClientRect();
        
        // Calculate grid coordinates from screen coordinates, accounting for zoom and pan
        const x = (e.clientX - rect.left - translateX) / scale;
        const y = (e.clientY - rect.top - translateY) / scale;
        const cell = getCellFromPixel(x, y);
        
        // Handle panning in drag mode
        if (interactionMode === 'drag' && isDragging) {
            const dx = e.clientX - lastMouseX;
            const dy = e.clientY - lastMouseY;
            
            translateX += dx;
            translateY += dy;
            
            lastMouseX = e.clientX;
            lastMouseY = e.clientY;
            
            drawHexGrid();
            return;
        }
        
        // Handle path drawing in move mode
        if (interactionMode === 'move' && isDrawingPath) {
            if (cell) {
                // Don't allow moving to enemy position
                if (cell.col === enemyPos.col && cell.row === enemyPos.row) {
                    return;
                }
                
                // Calculate path to current cell
                currentPath = computePath(playerPos, cell);
                drawHexGrid();
            }
            return;
        }
        
        // Preview AOE in attack mode on hover
        if (interactionMode === 'attack' && cell) {
            // Check if the cell is within range
            if (highlightedCells.some(c => c.col === cell.col && c.row === cell.row)) {
                previewAOECell = cell;
                drawHexGrid();
            } else {
                if (previewAOECell) {
                    previewAOECell = null;
                    drawHexGrid();
                }
            }
        }
    });
    
    // Mouse up
    canvas.addEventListener('mouseup', function() {
        isDragging = false;
        isDrawingPath = false;
        canvas.style.cursor = 'default';
    });
    
    // Mouse leave
    canvas.addEventListener('mouseleave', function() {
        isDragging = false;
        isDrawingPath = false;
        previewAOECell = null;
        canvas.style.cursor = 'default';
        drawHexGrid(); // Redraw to clear hover effects
    });
    
    // Prevent context menu on canvas
    canvas.addEventListener('contextmenu', function(e) {
        e.preventDefault();
    });
}

// Function to zoom canvas
function zoomCanvas(delta, focalX, focalY) {
    const canvas = document.getElementById("hexCanvas");
    if (!canvas) return;
    
    // Calculate new scale with limits
    const newScale = Math.min(Math.max(scale + delta, MIN_SCALE), MAX_SCALE);
    
    // If no change in scale, exit early
    if (newScale === scale) return;
    
    // If focal point not provided, use center of canvas
    if (focalX === undefined || focalY === undefined) {
        focalX = canvas.width / 2;
        focalY = canvas.height / 2;
    }
    
    // Adjust translate to keep focal point fixed
    const scaleDiff = newScale - scale;
    translateX = translateX - (focalX - translateX) * (scaleDiff / scale);
    translateY = translateY - (focalY - translateY) * (scaleDiff / scale);
    
    // Apply new scale
    scale = newScale;
    
    // Redraw
    drawHexGrid();
    
    // Show notification with debouncing
    if (window.showNotification) {
        // Remove any existing zoom notifications
        const container = document.querySelector('.notification-container');
        if (container) {
            const notifications = container.querySelectorAll('.notification');
            notifications.forEach(notif => {
                if (notif.textContent.includes('Zoom:')) {
                    notif.remove();
                }
            });
        }
        
        // Add new notification
        window.showNotification(`Zoom: ${Math.round(scale * 100)}%`, "info", 1000);
    }
}

// Reset view to original state
function resetView() {
    scale = 1;
    translateX = 0;
    translateY = 0;
    drawHexGrid();
    
    if (window.showNotification) {
        window.showNotification("View reset to default", "info");
    }
}

// Update player position from game config
function updatePlayerPosition() {
    if (window.GAME_CONFIG && window.GAME_CONFIG.character && window.GAME_CONFIG.character.pos) {
        playerPos = window.GAME_CONFIG.character.pos;
    }
    if (window.GAME_CONFIG && window.GAME_CONFIG.enemy && window.GAME_CONFIG.enemy.pos) {
        enemyPos = window.GAME_CONFIG.enemy.pos;
    }
}

// Initialize hex colors
function initializeHexColors() {
    hexColors = [];
    for (let col = 0; col < gridCols; col++) {
        hexColors[col] = [];
        for (let row = 0; row < gridRows; row++) {
            let colors = currentTerrain.hex_fill.colors;
            let colorIndex = Math.random() < currentTerrain.hex_fill.frequency ? 
                Math.floor(Math.random() * colors.length) : 0;
            hexColors[col][row] = colors[colorIndex];
        }
    }
}

function changeTerrain(terrainType) {
    currentTerrain = window.GAME_CONFIG.battlefield.terrain_types[terrainType];
    initializeHexColors();
    drawHexGrid();
}

function drawHexGrid() {
    let canvas = document.getElementById("hexCanvas");
    if (!canvas.getContext) return;
    let ctx = canvas.getContext("2d");
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Apply transformations
    ctx.save();
    ctx.translate(translateX, translateY);
    ctx.scale(scale, scale);
    
    // Initialize hex colors if needed
    if (hexColors.length === 0) {
        initializeHexColors();
    }
    
    // Draw hexagons
    for (let col = 0; col < gridCols; col++) {
        for (let row = 0; row < gridRows; row++) {
            // Calculate the center coordinates of the hexagon
            let x = col * hexSize * 1.5 + hexSize;
            let y = row * hexSize * Math.sqrt(3) + (col % 2) * hexSize * Math.sqrt(3) / 2 + hexSize;
            
            // Check if the cell is in a highlighted zone
            let isHighlighted = highlightedCells.some(cell => cell.col === col && cell.row === row);
            let isInAOE = selectedTargetCell && currentAOE > 0 && 
                          getDistance(col, row, selectedTargetCell.col, selectedTargetCell.row) <= currentAOE;
            
            drawHexagon(ctx, x, y, hexSize, isHighlighted, isInAOE, col, row);
        }
    }
    
    // Draw path if exists
    if (currentPath.length > 1) {
        drawPath(ctx);
    }
    
    // Draw tokens
    drawTokens(ctx);
    
    // Restore context (removes transformations)
    ctx.restore();
    
    // Draw zoom indicator
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(10, 10, 100, 30);
    ctx.fillStyle = 'white';
    ctx.font = '12px Arial';
    ctx.fillText(`Zoom: ${Math.round(scale * 100)}%`, 20, 30);
}

function drawPath(ctx) {
    if (currentPath.length < 2 || interactionMode === 'attack') return;
    
    ctx.beginPath();
    ctx.strokeStyle = "green";
    ctx.lineWidth = 3;
    
    let hexWidth = hexSize * 2;
    let hexHeight = Math.sqrt(3) * hexSize;
    
    for (let i = 0; i < currentPath.length; i++) {
        let cell = currentPath[i];
        // Use the same hex center calculation as in drawHexagon
        let x = cell.col * hexSize * 1.5 + hexSize;
        let y = cell.row * hexSize * Math.sqrt(3) + ((cell.col % 2) * hexSize * Math.sqrt(3) / 2) + hexSize;
        
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }
    
    ctx.stroke();
    
    // Draw movement cost
    let steps = currentPath.length - 1;
    let moveCost = steps * window.GAME_CONFIG.rules.movement.base_cost;
    let terrainMultiplier = currentTerrain.movement_cost || 1;
    let totalCost = Math.floor(moveCost * terrainMultiplier);
    
    // Update move cost display
    document.getElementById('moveCost').textContent = totalCost;
    
    // Color based on whether we can afford the move
    ctx.fillStyle = totalCost > playerSpeed ? "red" : "green";
    ctx.font = "14px Arial";
    ctx.fillText(`Movement Cost: ${totalCost} speed`, 10, 20);
    
    // Reset styles
    ctx.strokeStyle = "black";
    ctx.lineWidth = 1;
}

function drawTokens(ctx) {
    let hexWidth = hexSize * 2;
    let hexHeight = Math.sqrt(3) * hexSize;
    
    // Draw player token (blue circle)
    let x = playerPos.col * hexSize * 1.5 + hexSize;
    let y = playerPos.row * hexSize * Math.sqrt(3) + ((playerPos.col % 2) * hexSize * Math.sqrt(3) / 2) + hexSize;
    
    ctx.beginPath();
    ctx.arc(x, y, hexSize / 3, 0, 2 * Math.PI);
    ctx.fillStyle = "rgba(0, 255, 0, 0.8)";
    ctx.fill();
    ctx.shadowColor = '#00ff00';
    ctx.shadowBlur = 15;
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.shadowBlur = 0;
    
    // Add player symbol
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 20px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('P', x, y);
    
    // Draw enemy token (red circle)
    x = enemyPos.col * hexSize * 1.5 + hexSize;
    y = enemyPos.row * hexSize * Math.sqrt(3) + ((enemyPos.col % 2) * hexSize * Math.sqrt(3) / 2) + hexSize;
    
    ctx.beginPath();
    ctx.arc(x, y, hexSize / 3, 0, 2 * Math.PI);
    ctx.fillStyle = "rgba(255, 0, 0, 0.8)";
    ctx.fill();
    ctx.shadowColor = '#ff0000';
    ctx.shadowBlur = 15;
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.shadowBlur = 0;
    
    // Add enemy symbol
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 20px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('E', x, y);
}

function drawHexagon(ctx, x, y, size, isHighlighted, isInAOE, col, row) {
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
        let angle = Math.PI / 180 * (60 * i);
        let x_i = x + size * Math.cos(angle);
        let y_i = y + size * Math.sin(angle);
        if (i === 0) {
            ctx.moveTo(x_i, y_i);
        } else {
            ctx.lineTo(x_i, y_i);
        }
    }
    ctx.closePath();
    
    // Fill with terrain color
    if (col >= 0 && col < hexColors.length && row >= 0 && row < hexColors[col].length) {
        ctx.fillStyle = hexColors[col][row];
        ctx.fill();
    }
    
    // Add highlight if needed
    if (isHighlighted) {
        ctx.fillStyle = 'rgba(255, 255, 0, 0.2)';
        ctx.fill();
    }
    
    // Add AOE highlight if needed
    if (isInAOE) {
        ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
        ctx.fill();
    }
    
    // Добавляем подсветку клетки телепортации
    if (selectedTeleportCell && col === selectedTeleportCell.col && row === selectedTeleportCell.row) {
        ctx.fillStyle = 'rgba(0, 191, 255, 0.5)';  // Голубой цвет для телепортации
        ctx.fill();
        ctx.strokeStyle = 'rgba(0, 191, 255, 0.8)';
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.lineWidth = 1;
    }
    
    // Это особое выделение для выбранной клетки Hold Person
    if (holdPersonActive && window.holdPersonTarget) {
        // Проверяем координаты врага напрямую, а не вычисленные col и row
        if (enemyPos.col === window.holdPersonTarget.col && 
            enemyPos.row === window.holdPersonTarget.row && 
            col === enemyPos.col && row === enemyPos.row) {
            
            // Заливка более насыщенным фиолетовым без белой обводки
            ctx.fillStyle = 'rgba(138, 43, 226, 0.6)';
            ctx.fill();
            
            // Добавляем маленький внутренний круг для лучшей видимости
            ctx.beginPath();
            ctx.arc(x, y, size * 0.3, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(138, 43, 226, 0.9)';
            ctx.fill();
        }
    }
    
    // Add target selection highlight
    if (selectedTargetCell && col === selectedTargetCell.col && row === selectedTargetCell.row) {
        ctx.fillStyle = 'rgba(255, 215, 0, 0.5)'; // Gold color for selected target
        ctx.fill();
        ctx.strokeStyle = 'rgba(255, 215, 0, 0.8)';
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.lineWidth = 1;
    }
    
    // Add AOE preview highlight on hover
    if (previewAOECell && currentAOE > 0 && 
        previewAOECell.col !== col && previewAOECell.row !== row && // Not the hovered cell
        Math.abs(previewAOECell.col - col) + Math.abs(previewAOECell.row - row) <= currentAOE) {
        ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
        ctx.fill();
    }
    
    ctx.strokeStyle = currentTerrain.grid_color;
    ctx.stroke();
}

// Modified getCellFromPixel to account for transforms
function getCellFromPixel(x, y) {
    // Note: x and y should already be adjusted for translation and scale
    
    // Hexagon dimensions
    const hexWidth = hexSize * 2;
    const hexHeight = Math.sqrt(3) * hexSize;
    
    // First find approximate column and row
    let col = Math.floor(x / (hexSize * 1.5));
    let row;
    
    // Account for offset on odd columns
    if (col % 2 === 0) {
        row = Math.floor(y / (hexSize * Math.sqrt(3)));
    } else {
        row = Math.floor((y - (hexSize * Math.sqrt(3) / 2)) / (hexSize * Math.sqrt(3)));
    }
    
    // Additional check for boundary cells
    // Since hexagons have sloped boundaries
    const centerX = col * (hexSize * 1.5) + hexSize;
    const centerY = row * (hexSize * Math.sqrt(3)) + ((col % 2) * (hexSize * Math.sqrt(3) / 2)) + hexSize;
    
    // Calculate distance from cell center to click point
    const dx = x - centerX;
    const dy = y - centerY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    // If point is far from center, check neighboring cells
    if (distance > hexSize / 2) {
        // Check neighboring cells to find the closest
        const possibleCells = [
            {col: col, row: row},
            {col: col+1, row: row},
            {col: col-1, row: row},
            {col: col, row: row+1},
            {col: col, row: row-1}
        ];
        
        // Add diagonal neighbors based on column parity
        if (col % 2 === 0) {
            possibleCells.push({col: col+1, row: row-1});
            possibleCells.push({col: col-1, row: row-1});
        } else {
            possibleCells.push({col: col+1, row: row+1});
            possibleCells.push({col: col-1, row: row+1});
        }
        
        let bestDistance = distance;
        let bestCell = {col, row};
        
        for (const cell of possibleCells) {
            // Skip cells outside the grid
            if (cell.col < 0 || cell.col >= gridCols || cell.row < 0 || cell.row >= gridRows) {
                continue;
            }
            
            // Calculate coordinates for cell center using same formula as in drawHexGrid
            const cellCenterX = cell.col * (hexSize * 1.5) + hexSize;
            const cellCenterY = cell.row * (hexSize * Math.sqrt(3)) + ((cell.col % 2) * (hexSize * Math.sqrt(3) / 2)) + hexSize;
            
            const cellDx = x - cellCenterX;
            const cellDy = y - cellCenterY;
            const cellDistance = Math.sqrt(cellDx * cellDx + cellDy * cellDy);
            
            if (cellDistance < bestDistance) {
                bestDistance = cellDistance;
                bestCell = cell;
            }
        }
        
        col = bestCell.col;
        row = bestCell.row;
    }
    
    // Check that the found cell is within the grid
    if (col < 0 || col >= gridCols || row < 0 || row >= gridRows) {
        return null;
    }
    
    return {col, row};
}

if (typeof addToBattleLog !== 'function') {
    function addToBattleLog(message) {
        console.log('Battle Log:', message);
    }
}

if (typeof selectAttack !== 'function') {
    function selectAttack(attackType, range, spellName) {
        console.log('Selected attack:', attackType, 'with range', range, 'and spell', spellName);
    }
}

function computePath(start, end) {
    let path = [start];
    let current = start;
    
    // Don't compute path if end point is enemy's position
    if (end.col === enemyPos.col && end.row === enemyPos.row) {
        return path;
    }
    
    // Calculate max steps based on remaining speed and terrain
    let terrainMultiplier = currentTerrain.movement_cost || 1;
    let maxSteps = Math.floor(playerSpeed / (window.GAME_CONFIG.rules.movement.base_cost * terrainMultiplier));
    
    while (current.col !== end.col || current.row !== end.row) {
        if (path.length > maxSteps) {
            return path;
        }
        
        let neighbors = getNeighbors(current);
        let best = null;
        let bestDist = Infinity;
        
        for (let n of neighbors) {
            if (n.col === enemyPos.col && n.row === enemyPos.row) {
                continue;
            }
            let dx = n.col - end.col;
            let dy = n.row - end.row;
            let d = Math.sqrt(dx * dx + dy * dy);
            if (d < bestDist) {
                bestDist = d;
                best = n;
            }
        }
        
        if (!best) break;
        current = best;
        path.push(current);
    }
    return path;
}

function getNeighbors(cell) {
    let col = cell.col;
    let row = cell.row;
    let neighbors = [];
    
    if (col % 2 === 0) {
        neighbors.push({ col: col, row: row - 1 });       // up
        neighbors.push({ col: col, row: row + 1 });       // down
        neighbors.push({ col: col + 1, row: row - 1 });   // upper right
        neighbors.push({ col: col + 1, row: row });       // lower right
        neighbors.push({ col: col - 1, row: row - 1 });   // upper left
        neighbors.push({ col: col - 1, row: row });       // lower left
    } else {
        neighbors.push({ col: col, row: row - 1 });       // up
        neighbors.push({ col: col, row: row + 1 });       // down
        neighbors.push({ col: col + 1, row: row });       // upper right
        neighbors.push({ col: col + 1, row: row + 1 });   // lower right
        neighbors.push({ col: col - 1, row: row });       // upper left
        neighbors.push({ col: col - 1, row: row + 1 });   // lower left
    }
    
    return neighbors.filter(n => 
        n.col >= 0 && n.col < gridCols && 
        n.row >= 0 && n.row < gridRows
    );
}

function checkAdjacent() {
    let neighbors = getNeighbors(playerPos);
    return neighbors.some(n => n.col === enemyPos.col && n.row === enemyPos.row);
}

// Add this function to handle movement application
async function applyMove() {
    if (currentPath.length < 2) {
        addToBattleLog("No path selected!");
        return;
    }
    
    let steps = currentPath.length - 1;
    let moveCost = steps * window.GAME_CONFIG.rules.movement.base_cost;
    let terrainMultiplier = currentTerrain.movement_cost || 1;
    let totalCost = Math.floor(moveCost * terrainMultiplier);
    
    if (totalCost > playerSpeed) {
        addToBattleLog(`Not enough speed! Need ${totalCost}, but have ${playerSpeed}`);
        return;
    }
    
    // Update position and speed
    playerPos = currentPath[currentPath.length - 1];
    playerSpeed -= totalCost;
    
    // Update UI
    document.getElementById('char_speed').textContent = `${playerSpeed}/${PLAYER.stats.speed}`;
    addToBattleLog(`Moved ${steps} tiles. Cost: ${totalCost} speed. Remaining: ${playerSpeed}`);
    
    // Clear path and redraw
    currentPath = [];
    drawHexGrid();
    
    // Проверяем, осталось ли движение, и включаем/отключаем кнопку движения
    const applyMoveButton = document.getElementById('applyMoveButton');
    if (applyMoveButton) {
        applyMoveButton.disabled = (playerSpeed <= 0);
    }
}

// Add this function to get cells within range using BFS
function getCellsInRange(startCell, range) {
    let cells = [];
    let visited = new Set();
    let queue = [{cell: startCell, distance: 0}];
    
    while (queue.length > 0) {
        let current = queue.shift();
        let cellKey = `${current.cell.col},${current.cell.row}`;
        
        if (visited.has(cellKey)) continue;
        visited.add(cellKey);
        
        if (current.distance <= range) {
            cells.push(current.cell);
            
            // Add neighbors to queue
            let neighbors = getNeighbors(current.cell);
            for (let neighbor of neighbors) {
                if (!visited.has(`${neighbor.col},${neighbor.row}`)) {
                    queue.push({
                        cell: neighbor,
                        distance: current.distance + 1
                    });
                }
            }
        }
    }
    return cells;
}

// Add function to highlight range
function highlightRange(center, range, aoe = 0) {
    currentRange = range;
    currentAOE = aoe;
    highlightedCells = getCellsInRange(center, range);
    drawHexGrid();
}

// Add function to clear highlighting
function clearHighlight() {
    highlightedCells = [];
    currentRange = 0;
    currentAOE = 0;
    selectedTargetCell = null;
    currentAOECells = [];
    previewAOECell = null;
    
    // Reset special mode states
    awaitingMistyStepTarget = false;
    selectedTeleportCell = null;
    holdPersonActive = false;
    window.holdPersonTarget = null;
    
    // Reset to move mode
    setInteractionMode('move');
    
    drawHexGrid();
}

// Add function to check if target is in range
function isInRange(targetCol, targetRow, range) {
    return highlightedCells.some(cell => 
        cell.col === targetCol && cell.row === targetRow
    );
}

// Add function to get cells in AOE
function getCellsInAOE(center, size) {
    if (size <= 0) return [];
    return getCellsInRange(center, size - 1);
}

// Update the end turn button styling function
function updateEndTurnButton() {
    const endTurnButton = document.getElementById('endTurnButton');
    if (endTurnButton) {
        // Add hover effect directly to preserve existing click event listener
        endTurnButton.addEventListener('mouseover', function() {
            this.style.backgroundColor = '#45a049';
        });
        endTurnButton.addEventListener('mouseout', function() {
            this.style.backgroundColor = '#4CAF50';
        });
    }
}

// Обновляем функцию телепортации для использования глобальной переменной
function teleportToSelectedCell() {
    if (!selectedTeleportCell) {
        if (window.showNotification) {
            window.showNotification("Сначала выберите клетку для телепортации", "warning");
        } else {
            alert("Сначала выберите клетку для телепортации");
        }
        return;
    }
    
    console.log("Телепортация игрока из", playerPos, "в точку", selectedTeleportCell);
    
    // Телепортируем игрока точно в выбранную клетку
    playerPos = {
        col: selectedTeleportCell.col,
        row: selectedTeleportCell.row
    };
    
    // Сбрасываем выделение
    highlightedCells = [];
    
    // Обновляем отображение
    drawHexGrid();
    
    // Сбрасываем состояние телепортации
    awaitingMistyStepTarget = false;
    selectedTeleportCell = null;
    
    // Уменьшаем количество ячеек заклинаний
    const spellSlots2Element = document.getElementById('spell_slots_2');
    if (spellSlots2Element) {
        const current = parseInt(spellSlots2Element.textContent);
        spellSlots2Element.textContent = Math.max(0, current - 1);
    }
    
    // Отображаем уведомление об успешной телепортации
    if (window.showNotification) {
        window.showNotification("Телепортация успешна!", "success");
    } else {
        alert("Телепортация успешна!");
    }
    
    // Добавляем запись в боевой журнал
    if (window.addToBattleLog) {
        window.addToBattleLog(`Вы используете Misty Step и телепортируетесь на (${playerPos.col}, ${playerPos.row})!`);
    }
}

// Добавляем функцию активации режима Misty Step
function activateMistyStep() {
    awaitingMistyStepTarget = true;
    selectedTeleportCell = null;
    
    // Подсвечиваем все возможные клетки для телепортации
    // Используем большой радиус, как указано в заклинании (100)
    highlightedCells = [];
    for (let col = 0; col < gridCols; col++) {
        for (let row = 0; row < gridRows; row++) {
            // Не добавляем клетку с врагом
            if (col === enemyPos.col && row === enemyPos.row) continue;
            highlightedCells.push({col, row});
        }
    }
    
    drawHexGrid();
    
    // Показать уведомление
    if (window.showNotification) {
        window.showNotification("Выберите клетку для телепортации", "info");
    } else {
        alert("Выберите клетку для телепортации");
    }
}

// Переделываем функцию activateHoldPerson для поддержки смены выбора
function activateHoldPerson() {
    // Сбрасываем состояние
    holdPersonActive = true;
    window.holdPersonTarget = null;
    
    // Подсвечиваем клетки в радиусе от игрока (60 футов = 12 клеток)
    const spellRange = 12;
    highlightedCells = getCellsInRange(playerPos, spellRange);
    
    // Перерисовываем поле
    drawHexGrid();
    
    // Показываем подсказку
    if (window.showNotification) {
        window.showNotification("Выберите врага в радиусе для применения Hold Person", "info");
    }
    
    // Добавляем обработчик для кнопки Cast Spell
    const castSpellButton = document.getElementById('castSpellButton');
    if (castSpellButton) {
        // Сохраняем оригинальный обработчик
        const originalOnClick = castSpellButton.onclick;
        
        // Устанавливаем новый обработчик
        castSpellButton.onclick = function(e) {
            if (holdPersonActive) {
                // Проверяем, что цель выбрана
                if (!window.holdPersonTarget) {
                    if (window.showNotification) {
                        window.showNotification("Сначала выберите врага для Hold Person", "warning");
                    }
                    return;
                }
                
                // Отправляем запрос на сервер
                fetch('/api/cast_spell', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        spell_name: "Hold Person",
                        target: window.holdPersonTarget
                    })
                })
                .then(response => response.json())
                .then(data => {
                    // Обработка успешного ответа
                    if (data.combat_log) {
                        if (window.showNotification) {
                            window.showNotification(data.combat_log, "success");
                        }
                        if (window.addToBattleLog) {
                            window.addToBattleLog(data.combat_log);
                        }
                    }
                    
                    // Обновляем слоты заклинаний
                    if (data.spell_slots) {
                        const level2Element = document.getElementById('spell_slots_2');
                        if (level2Element) {
                            level2Element.textContent = data.spell_slots['2'];
                        }
                    }
                    
                    // Сбрасываем режим Hold Person
                    holdPersonActive = false;
                    window.holdPersonTarget = null;
                    highlightedCells = [];
                    drawHexGrid();
                    
                    // Восстанавливаем оригинальный обработчик
                    castSpellButton.onclick = originalOnClick;
                })
                .catch(error => {
                    console.error("Error casting Hold Person:", error);
                    if (window.showNotification) {
                        window.showNotification("Ошибка при применении Hold Person", "error");
                    }
                    
                    // Сбрасываем режим даже при ошибке
                    holdPersonActive = false;
                    window.holdPersonTarget = null;
                    highlightedCells = [];
                    drawHexGrid();
                    
                    // Восстанавливаем оригинальный обработчик
                    castSpellButton.onclick = originalOnClick;
                });
                
                // Предотвращаем дальнейшую обработку клика
                e.preventDefault();
                e.stopPropagation();
                return false;
            } else if (originalOnClick) {
                // Для других заклинаний вызываем оригинальный обработчик
                return originalOnClick.call(this, e);
            }
        };
    }
}

// Helper function to update attack preview
function updateAttackPreview(cell) {
    const previewElement = document.getElementById('attackPreview');
    if (!previewElement) return;
    
    const selectedAttack = document.querySelector('.attack-button.selected');
    if (!selectedAttack) {
        previewElement.classList.add('hidden');
        return;
    }
    
    const attackType = selectedAttack.dataset.attackType;
    const spellName = selectedAttack.dataset.spellName;
    
    // Get target name (enemy if targeting enemy position)
    const isTargetingEnemy = cell.col === enemyPos.col && cell.row === enemyPos.row;
    const targetName = isTargetingEnemy ? 'Enemy' : `Hex (${cell.col},${cell.row})`;
    
    // Calculate affected cells
    const affectedCellsCount = currentAOECells.length;
    
    let previewText = `Targeting ${targetName} with ${spellName || attackType}. `;
    if (affectedCellsCount > 0) {
        previewText += `Affects ${affectedCellsCount} cells.`;
    }
    
    previewElement.textContent = previewText;
    previewElement.classList.remove('hidden');
}

// Function to add interaction controls
function addInteractionControls() {
    // Create controls container if it doesn't exist
    let controls = document.querySelector('.interaction-controls');
    if (!controls) {
        controls = document.createElement('div');
        controls.className = 'interaction-controls';
        
        // Create move mode button
        const moveBtn = document.createElement('button');
        moveBtn.innerHTML = '🏃 Move';
        moveBtn.title = 'Movement Mode';
        moveBtn.classList.add('active');
        moveBtn.addEventListener('click', () => setInteractionMode('move'));
        
        // Create attack mode button  
        const attackBtn = document.createElement('button');
        attackBtn.innerHTML = '⚔️ Attack';
        attackBtn.title = 'Attack Mode';
        attackBtn.addEventListener('click', () => setInteractionMode('attack'));
        
        // Create pan mode button
        const panBtn = document.createElement('button');
        panBtn.innerHTML = '👆 Pan';
        panBtn.title = 'Pan Mode';
        panBtn.addEventListener('click', () => setInteractionMode('drag'));
        
        // Add buttons to controls
        controls.appendChild(moveBtn);
        controls.appendChild(attackBtn);
        controls.appendChild(panBtn);
        
        // Add controls to canvas container
        const canvasContainer = document.querySelector('.canvas-container');
        if (canvasContainer) {
            canvasContainer.appendChild(controls);
        }
    }
}

// Function to switch interaction mode
function setInteractionMode(mode) {
    interactionMode = mode;
    // Clear appropriate visual elements based on mode
    if (mode === 'attack' || mode === 'drag') {
        currentPath = [];
    }
    if (mode === 'move' || mode === 'drag') {
        selectedTargetCell = null;
        currentAOECells = [];
    }
    // Update UI to reflect current mode
    const canvas = document.getElementById('hexCanvas');
    if (canvas) {
        canvas.className = mode === 'drag' ? 'pan-mode' : (mode === 'move' ? 'move-mode' : 'attack-mode');
    }
    
    // Update instructions text
    const instructions = document.getElementById('instructions');
    if (instructions) {
        switch(mode) {
            case 'move':
                instructions.textContent = `Click and drag from your character to plan movement. Movement cost: ${window.GAME_CONFIG.rules.movement.base_cost} speed per hex.`;
                break;
            case 'attack':
                instructions.textContent = 'Select a tile within range to target with your attack or spell.';
                break;
            case 'drag':
                instructions.textContent = 'Click and drag to move the map. Right-click or use Alt+drag to pan.';
                break;
        }
    }
    
    // Redraw to update visualization
    drawHexGrid();
}

// Helper functions for special spells
function handleMistyStepTargetSelection(cell) {
    console.log("In Misty Step target selection mode");
    
    if (!cell) return;
    
    // Check if cell is valid for teleport
    if (cell.col === enemyPos.col && cell.row === enemyPos.row) {
        if (window.showNotification) {
            window.showNotification("Cannot teleport to enemy's position", "warning");
        } else {
            alert("Cannot teleport to enemy's position");
        }
        return;
    }
    
    // Save selected cell and redraw
    selectedTeleportCell = cell;
    drawHexGrid();
    
    if (window.showNotification) {
        window.showNotification(`Cell (${cell.col}, ${cell.row}) selected. Click 'Teleport' to confirm.`, "info");
    } else {
        alert(`Cell (${cell.col}, ${cell.row}) selected. Click 'Teleport' to confirm.`);
    }
    
    // Show teleport button
    const teleportButton = document.getElementById('teleportButton');
    if (teleportButton) {
        teleportButton.classList.remove('hidden');
    }
}

function handleHoldPersonTargetSelection(cell) {
    if (!cell) return;
    
    // Check if cell is in range
    const isInRange = highlightedCells.some(c => c.col === cell.col && c.row === cell.row);
    if (!isInRange) {
        if (window.showNotification) {
            window.showNotification("This cell is out of Hold Person range", "warning");
        }
        return;
    }
    
    // Check if enemy is in cell
    if (cell.col === enemyPos.col && cell.row === enemyPos.row) {
        window.holdPersonTarget = {col: cell.col, row: cell.row};
        drawHexGrid();
        
        if (window.showNotification) {
            window.showNotification("Enemy targeted for Hold Person. Click 'Cast Spell'", "success");
        }
    } else {
        if (window.showNotification) {
            window.showNotification("No enemy in this cell for Hold Person", "warning");
        }
    }
}

/* Expose functions and variables to the global window object */
// Core game variables
window.playerPos = playerPos;
window.enemyPos = enemyPos;
window.playerSpeed = playerSpeed;
window.currentPath = currentPath;
window.hexSize = hexSize;
window.gridCols = gridCols;
window.gridRows = gridRows;

// Core rendering functions
window.drawHexGrid = drawHexGrid;
window.initializeHexColors = initializeHexColors;
window.drawTokens = drawTokens;

// Path and movement functions
window.computePath = computePath;
window.applyMove = applyMove;
window.getCurrentPathCost = getCurrentPathCost;
window.getNeighbors = getNeighbors;
window.checkAdjacent = checkAdjacent;

// Targeting and range functions
window.getCellsInRange = getCellsInRange;
window.highlightRange = highlightRange;
window.clearHighlight = clearHighlight;
window.isInRange = isInRange;
window.getCellsInAOE = getCellsInAOE;
window.updateAttackPreview = updateAttackPreview;
window.selectAttack = selectAttack;
window.selectedTargetCell = selectedTargetCell;

// Special abilities functions
window.teleportToSelectedCell = teleportToSelectedCell;
window.activateMistyStep = activateMistyStep;
window.activateHoldPerson = activateHoldPerson;
window.handleMistyStepTargetSelection = handleMistyStepTargetSelection;
window.handleHoldPersonTargetSelection = handleHoldPersonTargetSelection;

// Utility functions
window.getCellFromPixel = getCellFromPixel;
window.updatePlayerPosition = updatePlayerPosition;
window.updateEndTurnButton = updateEndTurnButton;
window.setInteractionMode = setInteractionMode;

// Zoom and pan functions
window.zoomCanvas = zoomCanvas;
window.zoomOut = zoomOut;
window.zoomIn = zoomIn;
window.resetView = resetView;

// State variables
window.currentRange = currentRange;
window.currentAOE = currentAOE;
window.highlightedCells = highlightedCells;
window.previewAOECell = previewAOECell;
window.awaitingMistyStepTarget = awaitingMistyStepTarget;
window.selectedTeleportCell = selectedTeleportCell;
window.holdPersonActive = holdPersonActive;

// Zoom and pan state
window.scale = scale;
window.translateX = translateX;
window.translateY = translateY;
window.isPanning = isPanning;
window.lastMouseX = lastMouseX;
window.lastMouseY = lastMouseY;
window.lastTouchX = lastTouchX;
window.lastTouchY = lastTouchY;
window.MIN_SCALE = MIN_SCALE;
window.MAX_SCALE = MAX_SCALE; 