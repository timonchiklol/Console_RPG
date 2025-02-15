let playerPos = { col: 0, row: 0 };
let enemyPos = { col: 5, row: 4 };

// player's current speed, default 30
let playerSpeed = 30;

let currentPath = [];
let drawingPath = false;

// Add these variables at the top with other globals
let highlightedCells = [];
let currentRange = 0;

function drawHexGrid() {
    let canvas = document.getElementById("hexCanvas");
    if (!canvas.getContext) return;
    let ctx = canvas.getContext("2d");
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    let hexSize = 30;
    let cols = 10;
    let rows = 8;
    let hexWidth = hexSize * 2;
    let hexHeight = Math.sqrt(3) * hexSize;
    
    // Draw all hexagons first
    for (let col = 0; col < cols; col++) {
        for (let row = 0; row < rows; row++) {
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
        drawPath(ctx, hexSize);
    }
    
    // Draw tokens
    drawTokens(ctx, hexSize, hexWidth, hexHeight);
}

function drawPath(ctx, hexSize) {
    ctx.beginPath();
    ctx.strokeStyle = "green";
    ctx.lineWidth = 3;
    for (let i = 0; i < currentPath.length; i++) {
        let cell = currentPath[i];
        let x = cell.col * (hexSize * 2) * 0.75 + hexSize;
        let hexHeight = Math.sqrt(3) * hexSize;
        let y = cell.row * hexHeight + ((cell.col % 2) * hexHeight / 2) + hexSize;
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }
    ctx.stroke();
    ctx.strokeStyle = "black";
    ctx.lineWidth = 1;
}

function drawTokens(ctx, hexSize, hexWidth, hexHeight) {
    // Draw player token (blue circle)
    let col = playerPos.col;
    let row = playerPos.row;
    let x = col * hexWidth * 0.75 + hexSize;
    let y = row * hexHeight + ((col % 2) * hexHeight / 2) + hexSize;
    ctx.beginPath();
    ctx.arc(x, y, hexSize / 3, 0, 2 * Math.PI);
    ctx.fillStyle = "blue";
    ctx.fill();

    // Draw enemy token (red circle)
    col = enemyPos.col;
    row = enemyPos.row;
    x = col * hexWidth * 0.75 + hexSize;
    y = row * hexHeight + ((col % 2) * hexHeight / 2) + hexSize;
    ctx.beginPath();
    ctx.arc(x, y, hexSize / 3, 0, 2 * Math.PI);
    ctx.fillStyle = "red";
    ctx.fill();
}

function drawHexagon(ctx, x, y, size, isHighlighted) {
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
        let angle = Math.PI / 180 * (60 * (i + 1));
        let x_i = x + size * Math.cos(angle);
        let y_i = y + size * Math.sin(angle);
        if (i === 0) {
            ctx.moveTo(x_i, y_i);
        } else {
            ctx.lineTo(x_i, y_i);
        }
    }
    ctx.closePath();
    
    if (isHighlighted) {
        ctx.fillStyle = 'rgba(255, 255, 0, 0.2)';
        ctx.fill();
    }
    
    ctx.stroke();
}

function getCellFromPixel(x, y) {
    let canvas = document.getElementById("hexCanvas");
    let rect = canvas.getBoundingClientRect();
    let mx = x - rect.left;
    let my = y - rect.top;
    let hexSize = 30;
    let hexWidth = hexSize * 2;
    let hexHeight = Math.sqrt(3) * hexSize;
    let found = null;
    for (let col = 0; col < 10; col++) {
        for (let row = 0; row < 8; row++) {
            let cx = col * hexWidth * 0.75 + hexSize;
            let cy = row * hexHeight + ((col % 2) * hexHeight / 2) + hexSize;
            let dist = Math.sqrt((mx - cx) ** 2 + (my - cy) ** 2);
            if (dist < hexSize) {
                found = { col: col, row: row };
            }
        }
    }
    return found;
}

function computePath(start, end) {
    let path = [start];
    let current = start;
    
    // Don't compute path if end point is enemy's position
    if (end.col === enemyPos.col && end.row === enemyPos.row) {
        return path;
    }
    
    // Calculate max steps based on remaining speed
    let maxSteps = Math.floor(playerSpeed / 5);
    
    while (current.col !== end.col || current.row !== end.row) {
        // Check if we've already reached the maximum path length based on speed
        if (path.length > maxSteps) { // +1 because path includes start position
            return path;
        }
        
        let neighbors = getNeighbors(current);
        let best = null;
        let bestDist = Infinity;
        
        for (let n of neighbors) {
            // Skip if this neighbor is enemy's position
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
    return neighbors.filter(n => n.col >= 0 && n.col < 10 && n.row >= 0 && n.row < 8);
}

function checkAdjacent() {
    let neighbors = getNeighbors(playerPos);
    for (let n of neighbors) {
        if (n.col === enemyPos.col && n.row === enemyPos.row) {
            return true;
        }
    }
    return false;
}

function applyMove() {
    if (currentPath.length < 2) {
        alert("No path selected!");
        return;
    }
    let dest = currentPath[currentPath.length - 1];
    if (dest.col === enemyPos.col && dest.row === enemyPos.row) {
        alert("Cannot move onto enemy's square!");
        return;
    }
    let steps = currentPath.length - 1;
    if (steps > 5) {
        alert("Cannot move more than 5 tiles! Maximum allowed: 5.");
        return;
    }
    let moveCost = steps * 5;
    if (moveCost > playerSpeed) {
        alert("Not enough speed for that move! Available: " + playerSpeed);
        return;
    }
    playerSpeed -= moveCost;
    playerPos.col = dest.col;
    playerPos.row = dest.row;
    currentPath = [];
    drawHexGrid();
}

// Mouse event handlers for path drawing
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
        
        // Show feedback about path length and speed cost
        let steps = currentPath.length - 1;
        let maxSteps = Math.floor(playerSpeed / 5);
        let moveCost = steps * 5;
        let canvas = document.getElementById("hexCanvas");
        let ctx = canvas.getContext("2d");
        ctx.fillStyle = moveCost > playerSpeed ? "red" : "green";
        ctx.font = "14px Arial";
        ctx.fillText(`Path: ${steps} tiles (Cost: ${moveCost} speed, Available: ${playerSpeed})`, 10, 20);
    }
});

canvas.addEventListener("mouseup", function(e) {
    drawingPath = false;
});

// Initial draw on load
window.addEventListener("load", drawHexGrid);

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