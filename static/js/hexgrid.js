// Initialize game state
let playerPos = { col: 0, row: 0 };  // Will be updated from GAME_CONFIG
let enemyPos = { col: 5, row: 4 };  // This will be set by the server

// Get player stats from config
const PLAYER = {
    stats: {
        speed: 30,  // Default speed
        ...window.GAME_CONFIG?.player?.stats  // Merge with any server-provided stats
    }
};

// player's current speed, default to config value
let playerSpeed = PLAYER.stats.speed;
let hasMoved = false;  // Track if player has moved this turn

let currentPath = [];
let drawingPath = false;

// Add these variables at the top with other globals
let highlightedCells = [];
let currentRange = 0;
let selectedCell = null;  // Store selected cell for AOE
let currentAOE = 0;      // Store current AOE size

// Grid dimensions from config
const gridCols = window.GAME_CONFIG.battlefield.dimensions.cols;
const gridRows = window.GAME_CONFIG.battlefield.dimensions.rows;
const hexSize = window.GAME_CONFIG.battlefield.dimensions.hex_size;

// Current terrain settings
let currentTerrain = window.GAME_CONFIG.battlefield.terrain_types[window.GAME_CONFIG.currentTerrain];
let hexColors = [];

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
                highlightRange(range, aoe);
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
            hasMoved = false;
            playerSpeed = PLAYER.stats.speed;
            currentPath = [];
            clearHighlight();
            
            // Update UI
            const charSpeedElem = document.getElementById('char_speed');
            if (charSpeedElem) {
                charSpeedElem.textContent = `${playerSpeed}/${PLAYER.stats.speed}`;
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

    // Update end turn button style
    updateEndTurnButton();
});

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
    
    let hexWidth = hexSize * 2;
    let hexHeight = Math.sqrt(3) * hexSize;
    
    // Initialize hex colors if needed
    if (hexColors.length === 0) {
        initializeHexColors();
    }
    
    // Draw hexagons
    for (let col = 0; col < gridCols; col++) {
        for (let row = 0; row < gridRows; row++) {
            let x = col * hexWidth * 0.75 + hexSize;
            let y = row * hexHeight + ((col % 2) * hexHeight / 2) + hexSize;
            
            // Check if this cell should be highlighted for range
            let isHighlighted = highlightedCells.some(cell => 
                cell.col === col && cell.row === row
            );
            
            // Check if this cell should be highlighted for AOE
            let isInAOE = false;
            if (selectedCell && currentAOE > 0) {
                isInAOE = getCellsInAOE(selectedCell, currentAOE).some(cell =>
                    cell.col === col && cell.row === row
                );
            }
            
            drawHexagon(ctx, x, y, hexSize, isHighlighted, isInAOE);
        }
    }
    
    // Draw path if exists
    if (currentPath.length > 1) {
        drawPath(ctx);
    }
    
    // Draw tokens
    drawTokens(ctx);
}

function drawPath(ctx) {
    if (currentPath.length < 2) return;
    
    ctx.beginPath();
    ctx.strokeStyle = "green";
    ctx.lineWidth = 3;
    
    let hexWidth = hexSize * 2;
    let hexHeight = Math.sqrt(3) * hexSize;
    
    for (let i = 0; i < currentPath.length; i++) {
        let cell = currentPath[i];
        let x = cell.col * hexWidth * 0.75 + hexSize;
        let y = cell.row * hexHeight + ((cell.col % 2) * hexHeight / 2) + hexSize;
        
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
    let x = playerPos.col * hexWidth * 0.75 + hexSize;
    let y = playerPos.row * hexHeight + ((playerPos.col % 2) * hexHeight / 2) + hexSize;
    
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
    x = enemyPos.col * hexWidth * 0.75 + hexSize;
    y = enemyPos.row * hexHeight + ((enemyPos.col % 2) * hexHeight / 2) + hexSize;
    
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

function drawHexagon(ctx, x, y, size, isHighlighted, isInAOE) {
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
    let col = Math.floor(x / (size * 1.5));
    let row = Math.floor(y / (size * Math.sqrt(3)));
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
    
    ctx.strokeStyle = currentTerrain.grid_color;
    ctx.stroke();
}

/* Missing helper functions added */
if (typeof getCellFromPixel !== 'function') {
    function getCellFromPixel(clientX, clientY) {
        let hexWidth = hexSize * 2;
        let hexHeight = Math.sqrt(3) * hexSize;
        let col = Math.floor((clientX - hexSize) / (hexWidth * 0.75));
        if (col < 0) col = 0;
        let row = Math.floor((clientY - hexSize - ((col % 2) * hexHeight / 2)) / hexHeight);
        if (row < 0) row = 0;
        if (col >= gridCols) col = gridCols - 1;
        if (row >= gridRows) row = gridRows - 1;
        return { col, row };
    }
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
    if (hasMoved) {
        addToBattleLog("You can only move once per turn!");
        return;
    }

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
    hasMoved = true;  // Mark that player has moved this turn
    
    // Update UI
    document.getElementById('char_speed').textContent = playerSpeed;
    addToBattleLog(`Moved ${steps} tiles. Cost: ${totalCost} speed. Remaining: ${playerSpeed}`);
    
    // Clear path and redraw
    currentPath = [];
    drawHexGrid();
}

// Mouse event handlers
let canvas = document.getElementById("hexCanvas");

canvas.addEventListener("mousedown", function(e) {
    if (hasMoved) {
        return;  // Don't allow path drawing if already moved
    }
    let cell = getCellFromPixel(e.clientX, e.clientY);
    if (cell && cell.col === playerPos.col && cell.row === playerPos.row) {
        drawingPath = true;
        currentPath = [playerPos];
        drawHexGrid();
    }
});

canvas.addEventListener("mousemove", function(e) {
    if (drawingPath) {
        let cell = getCellFromPixel(e.clientX, e.clientY);
        if (cell) {
            currentPath = computePath(playerPos, cell);
            drawHexGrid();
        }
    } else if (currentRange > 0) {
        let cell = getCellFromPixel(e.clientX, e.clientY);
        if (cell && isInRange(cell.col, cell.row, currentRange)) {
            selectedCell = cell;
            drawHexGrid();
        }
    }
});

canvas.addEventListener("mouseup", function() {
    drawingPath = false;
});

canvas.addEventListener("click", function(e) {
    if (currentRange > 0 && !drawingPath) {
        let cell = getCellFromPixel(e.clientX, e.clientY);
        if (cell && isInRange(cell.col, cell.row, currentRange)) {
            selectedCell = cell;
            drawHexGrid();
        }
    }
});

// Initialize
window.addEventListener("load", function() {
    initializeHexColors();
    drawHexGrid();
});

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
function highlightRange(range, aoe = 0) {
    currentRange = range;
    currentAOE = aoe;
    highlightedCells = getCellsInRange(playerPos, range);
    drawHexGrid();
}

// Add function to clear highlighting
function clearHighlight() {
    highlightedCells = [];
    currentRange = 0;
    currentAOE = 0;
    selectedCell = null;
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

/* Expose functions and variables to the global window object */
window.playerPos = playerPos;
window.enemyPos = enemyPos;
window.hasMoved = hasMoved;
window.playerSpeed = playerSpeed;
window.currentPath = currentPath;
window.drawHexGrid = drawHexGrid;
window.initializeHexColors = initializeHexColors;
window.getCellsInRange = getCellsInRange;
window.checkAdjacent = checkAdjacent;
window.applyMove = applyMove; 