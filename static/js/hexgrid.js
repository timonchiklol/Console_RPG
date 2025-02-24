// Initialize game state
let playerPos = BATTLEFIELD_CONFIG.dimensions.starting_position || { col: 0, row: 0 };
let enemyPos = { col: 5, row: 4 };  // This will be set by the server

// player's current speed, default 30
let playerSpeed = 30;

let currentPath = [];
let drawingPath = false;

// Add these variables at the top with other globals
let highlightedCells = [];
let currentRange = 0;

// Add TranslationManager initialization at the top
let translationManager;

// Grid dimensions from config
const gridCols = BATTLEFIELD_CONFIG.dimensions.cols;
const gridRows = BATTLEFIELD_CONFIG.dimensions.rows;
const hexSize = BATTLEFIELD_CONFIG.dimensions.hex_size;

// Current terrain settings
let currentTerrain = BATTLEFIELD_CONFIG.terrain_types[CURRENT_TERRAIN];
let hexColors = [];

document.addEventListener('DOMContentLoaded', async () => {
    translationManager = new TranslationManager();
    await translationManager.loadTranslations();
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
    currentTerrain = BATTLEFIELD_CONFIG.terrain_types[terrainType];
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
            
            // Check if this cell should be highlighted
            let isHighlighted = highlightedCells.some(cell => 
                cell.col === col && cell.row === row
            );
            
            drawHexagon(ctx, x, y, hexSize, isHighlighted);
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
    let moveCost = steps * GAME_RULES.movement.base_cost;
    let terrainMultiplier = currentTerrain.movement_cost || 1;
    let totalCost = Math.floor(moveCost * terrainMultiplier);
    
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

function drawHexagon(ctx, x, y, size, isHighlighted) {
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
    ctx.fillStyle = hexColors[Math.floor(x / (size * 1.5))][Math.floor(y / (size * Math.sqrt(3)))];
    ctx.fill();
    
    // Add highlight if needed
    if (isHighlighted) {
        ctx.fillStyle = 'rgba(255, 255, 0, 0.2)';
        ctx.fill();
    }
    
    ctx.strokeStyle = currentTerrain.grid_color;
    ctx.stroke();
}

function getCellFromPixel(x, y) {
    let canvas = document.getElementById("hexCanvas");
    let rect = canvas.getBoundingClientRect();
    let mx = x - rect.left;
    let my = y - rect.top;
    
    let hexWidth = hexSize * 2;
    let hexHeight = Math.sqrt(3) * hexSize;
    
    for (let col = 0; col < gridCols; col++) {
        for (let row = 0; row < gridRows; row++) {
            let cx = col * hexWidth * 0.75 + hexSize;
            let cy = row * hexHeight + ((col % 2) * hexHeight / 2) + hexSize;
            let dist = Math.sqrt((mx - cx) ** 2 + (my - cy) ** 2);
            if (dist < hexSize) {
                return { col: col, row: row };
            }
        }
    }
    return null;
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
    let maxSteps = Math.floor(playerSpeed / (GAME_RULES.movement.base_cost * terrainMultiplier));
    
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

function applyMove() {
    if (currentPath.length < 2) {
        addToBattleLog("No path selected!");
        return;
    }
    
    let dest = currentPath[currentPath.length - 1];
    if (dest.col === enemyPos.col && dest.row === enemyPos.row) {
        addToBattleLog("Cannot move onto enemy's square!");
        return;
    }
    
    let steps = currentPath.length - 1;
    let moveCost = steps * GAME_RULES.movement.base_cost;
    let terrainMultiplier = currentTerrain.movement_cost || 1;
    let totalCost = Math.floor(moveCost * terrainMultiplier);
    
    if (totalCost > playerSpeed) {
        addToBattleLog(`Not enough speed! Need ${totalCost}, but have ${playerSpeed}`);
        return;
    }
    
    playerSpeed -= totalCost;
    playerPos = dest;
    currentPath = [];
    drawHexGrid();
    
    // Update UI
    document.getElementById('char_speed').textContent = playerSpeed;
    addToBattleLog(`Moved ${steps} tiles. Cost: ${totalCost} speed. Remaining: ${playerSpeed}`);
}

// Mouse event handlers
let canvas = document.getElementById("hexCanvas");

canvas.addEventListener("mousedown", function(e) {
    let cell = getCellFromPixel(e.clientX, e.clientY);
    if (cell && cell.col === playerPos.col && cell.row === playerPos.row) {
        drawingPath = true;
        currentPath = [playerPos];
        drawHexGrid();
    }
});

canvas.addEventListener("mousemove", function(e) {
    if (!drawingPath) return;
    
    let cell = getCellFromPixel(e.clientX, e.clientY);
    if (cell) {
        currentPath = computePath(playerPos, cell);
        drawHexGrid();
    }
});

canvas.addEventListener("mouseup", function() {
    drawingPath = false;
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
function highlightRange(range) {
    currentRange = range;
    highlightedCells = getCellsInRange(playerPos, range);
    drawHexGrid();
}

// Add function to clear highlighting
function clearHighlight() {
    highlightedCells = [];
    currentRange = 0;
    drawHexGrid();
}

// Add function to check if target is in range
function isInRange(targetCol, targetRow, range) {
    return getCellsInRange(playerPos, range).some(cell => 
        cell.col === targetCol && cell.row === targetRow
    );
} 