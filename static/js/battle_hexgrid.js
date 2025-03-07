/**
 * Battle Hexgrid - Handles battlefield rendering and hexagonal grid logic
 */

// Canvas and context
const canvas = document.getElementById('battlefieldCanvas');
const ctx = canvas.getContext('2d');

// Get battlefield configuration
const battlefieldConfig = GAME_CONFIG.battlefield;
const dimensions = battlefieldConfig.dimensions;
const terrainConfig = battlefieldConfig.terrain_types[battlefieldConfig.default_terrain];

// Grid properties
const hexSize = dimensions.hex_size;
const hexHeight = hexSize * 2;
const hexWidth = Math.sqrt(3) * hexSize;
const cols = dimensions.cols;
const rows = dimensions.rows;

// Game state
let playerPos = GAME_CONFIG.player.position;
let enemyPos = GAME_CONFIG.enemy.position;
let playerSpeed = GAME_CONFIG.player.stats.speed;
let currentPlayerSpeed = playerSpeed;

// Interaction state
let interactionMode = 'move'; // 'move', 'attack', or 'none'
let isDrawingPath = false;
let currentPath = [];
let highlightedCells = [];
let selectedTargetCell = null;
let currentAttack = null;
let currentAOECells = [];
let zoomLevel = 1;
let panOffset = { x: 0, y: 0 };
let lastPanPos = { x: 0, y: 0 };
let isPanning = false;

// Initialize the game
function initGame() {
    // Set canvas size
    resizeCanvas();
    
    // Set up event listeners
    setupCanvasEvents();
    
    // Add interaction controls
    setupInteractionControls();
    
    // Draw the initial state
    drawBattlefield();
    
    // Set up window resize handler
    window.addEventListener('resize', () => {
        resizeCanvas();
        drawBattlefield();
    });
}

// Resize canvas to fit container
function resizeCanvas() {
    const container = canvas.parentElement;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
}

// Set up canvas event handlers
function setupCanvasEvents() {
    // Mouse events
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('wheel', handleMouseWheel);
    
    // Touch events for mobile
    canvas.addEventListener('touchstart', handleTouchStart);
    canvas.addEventListener('touchmove', handleTouchMove);
    canvas.addEventListener('touchend', handleTouchEnd);
}

// Handle mouse down
function handleMouseDown(e) {
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoomLevel - panOffset.x;
    const y = (e.clientY - rect.top) / zoomLevel - panOffset.y;
    
    // Right-click or ctrl+click for panning
    if (e.button === 2 || e.ctrlKey) {
        e.preventDefault();
        isPanning = true;
        lastPanPos = { x: e.clientX, y: e.clientY };
        canvas.style.cursor = 'grabbing';
        return;
    }
    
    // Left-click for interaction
    const cell = getCellFromPixel(x, y);
    
    if (cell) {
        if (interactionMode === 'move') {
            // Start drawing a movement path
            if (cell.col === playerPos.col && cell.row === playerPos.row) {
                isDrawingPath = true;
                currentPath = [{ col: cell.col, row: cell.row }];
                drawBattlefield();
            }
        } else if (interactionMode === 'attack') {
            // Select a target for attack
            if (isInRange(cell.col, cell.row, currentAttack.range)) {
                selectedTargetCell = cell;
                document.getElementById('attackBtn').disabled = false;
                
                // Calculate AoE cells
                if (currentAttack.aoe > 0) {
                    currentAOECells = getCellsInAOE(selectedTargetCell, currentAttack.aoe);
                }
                
                drawBattlefield();
            }
        }
    }
}

// Handle mouse move
function handleMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoomLevel - panOffset.x;
    const y = (e.clientY - rect.top) / zoomLevel - panOffset.y;
    
    // If panning
    if (isPanning) {
        const dx = e.clientX - lastPanPos.x;
        const dy = e.clientY - lastPanPos.y;
        
        panOffset.x += dx / zoomLevel;
        panOffset.y += dy / zoomLevel;
        
        lastPanPos = { x: e.clientX, y: e.clientY };
        drawBattlefield();
        return;
    }
    
    const cell = getCellFromPixel(x, y);
    
    if (cell) {
        if (interactionMode === 'move' && isDrawingPath) {
            // Continue drawing movement path
            if (isCellAdjacent(currentPath[currentPath.length - 1], cell)) {
                if (!isCellInPath(cell)) {
                    currentPath.push({ col: cell.col, row: cell.row });
                } else {
                    // If moving back, remove cells after this one
                    const index = currentPath.findIndex(p => p.col === cell.col && p.row === cell.row);
                    currentPath = currentPath.slice(0, index + 1);
                }
                
                // Update button state based on path cost
                const pathCost = calculatePathCost(currentPath);
                document.getElementById('confirmMoveBtn').disabled = pathCost > currentPlayerSpeed;
                
                drawBattlefield();
            }
        } else if (interactionMode === 'attack') {
            // Preview AoE if hovering over a valid target
            if (isInRange(cell.col, cell.row, currentAttack.range)) {
                // Display AoE preview
                if (currentAttack.aoe > 0) {
                    currentAOECells = getCellsInAOE(cell, currentAttack.aoe);
                } else {
                    currentAOECells = [];
                }
                
                drawBattlefield();
            }
        }
    }
}

// Handle mouse up
function handleMouseUp(e) {
    if (isPanning) {
        isPanning = false;
        canvas.style.cursor = 'default';
        return;
    }
    
    if (interactionMode === 'move') {
        isDrawingPath = false;
    }
}

// Handle mouse wheel for zooming
function handleMouseWheel(e) {
    e.preventDefault();
    
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Determine direction and zoom amount
    const delta = -Math.sign(e.deltaY) * 0.1;
    const newZoom = Math.max(0.5, Math.min(3, zoomLevel + delta));
    
    // Adjust pan offset to zoom around mouse position
    if (delta !== 0 && newZoom !== zoomLevel) {
        const scale = newZoom / zoomLevel;
        panOffset.x = mouseX / zoomLevel - (mouseX / zoomLevel - panOffset.x) * scale;
        panOffset.y = mouseY / zoomLevel - (mouseY / zoomLevel - panOffset.y) * scale;
        zoomLevel = newZoom;
    }
    
    drawBattlefield();
}

// Touch event handlers for mobile
function handleTouchStart(e) {
    e.preventDefault();
    
    if (e.touches.length === 1) {
        // Single touch - convert to mouse event
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    } else if (e.touches.length === 2) {
        // Two touches - prepare for pinch zoom
        isPanning = false;
    }
}

function handleTouchMove(e) {
    e.preventDefault();
    
    if (e.touches.length === 1) {
        // Single touch - convert to mouse event
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    }
}

function handleTouchEnd(e) {
    e.preventDefault();
    
    const mouseEvent = new MouseEvent('mouseup');
    canvas.dispatchEvent(mouseEvent);
}

// Set up interaction control buttons
function setupInteractionControls() {
    // Confirm move button
    document.getElementById('confirmMoveBtn').addEventListener('click', confirmMove);
    
    // Attack button
    document.getElementById('attackBtn').addEventListener('click', confirmAttack);
    
    // End turn button
    document.getElementById('endTurnBtn').addEventListener('click', endTurn);
    
    // Attack items
    document.querySelectorAll('.attack-item').forEach(item => {
        item.addEventListener('click', function() {
            selectAttack(this);
        });
    });
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Update active tab button
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Show selected tab content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
    
    // Zoom controls
    document.getElementById('zoomIn').addEventListener('click', () => {
        zoomLevel = Math.min(3, zoomLevel + 0.2);
        drawBattlefield();
    });
    
    document.getElementById('zoomOut').addEventListener('click', () => {
        zoomLevel = Math.max(0.5, zoomLevel - 0.2);
        drawBattlefield();
    });
    
    document.getElementById('resetView').addEventListener('click', resetView);
}

// Reset view to center on player
function resetView() {
    zoomLevel = 1;
    centerOnPlayer();
    drawBattlefield();
}

// Center view on player position
function centerOnPlayer() {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    
    const { x, y } = getPixelFromCell(playerPos.col, playerPos.row);
    
    panOffset.x = centerX / zoomLevel - x;
    panOffset.y = centerY / zoomLevel - y;
}

// Select an attack or spell
function selectAttack(attackItem) {
    // Clear previous selection
    document.querySelectorAll('.attack-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Mark as selected
    attackItem.classList.add('selected');
    
    // Get attack details
    const attackName = attackItem.getAttribute('data-attack');
    const damage = attackItem.getAttribute('data-damage');
    const range = parseInt(attackItem.getAttribute('data-range'), 10);
    const aoe = parseInt(attackItem.getAttribute('data-aoe') || '0', 10);
    const attackType = attackItem.getAttribute('data-type');
    const manaCost = parseInt(attackItem.getAttribute('data-mana') || '0', 10);
    
    // Store current attack
    currentAttack = {
        name: attackName,
        damage: damage,
        range: range,
        aoe: aoe,
        type: attackType,
        manaCost: manaCost
    };
    
    // Switch to attack mode
    setInteractionMode('attack');
    
    // Highlight cells in range
    highlightCellsInRange(playerPos, range);
    
    // Reset target selection
    selectedTargetCell = null;
    currentAOECells = [];
    document.getElementById('attackBtn').disabled = true;
    
    // Check if player has enough mana (for spells)
    if (attackType === 'spell') {
        const currentMana = parseInt(document.getElementById('playerMana').textContent.split('/')[0], 10);
        if (currentMana < manaCost) {
            addBattleLog(`Not enough mana to cast ${attackName}!`);
            document.getElementById('attackBtn').disabled = true;
        }
    }
    
    drawBattlefield();
}

// Set the interaction mode
function setInteractionMode(mode) {
    interactionMode = mode;
    
    // Clear highlights and path
    highlightedCells = [];
    currentPath = [];
    selectedTargetCell = null;
    currentAOECells = [];
    
    // Update button states
    document.getElementById('confirmMoveBtn').disabled = true;
    document.getElementById('attackBtn').disabled = true;
    
    if (mode === 'move') {
        addBattleLog('Select a path to move.');
    } else if (mode === 'attack') {
        addBattleLog(`Select a target within range for ${currentAttack.name}.`);
    }
    
    drawBattlefield();
}

// Confirm movement
function confirmMove() {
    if (currentPath.length > 1) {
        // Calculate path cost
        const pathCost = calculatePathCost(currentPath);
        
        if (pathCost <= currentPlayerSpeed) {
            // Update player position
            playerPos = { ...currentPath[currentPath.length - 1] };
            
            // Deduct movement speed
            currentPlayerSpeed -= pathCost;
            
            // Add to battle log
            addBattleLog(`Moved to (${playerPos.col}, ${playerPos.row}). ${currentPlayerSpeed} movement remaining.`);
            
            // Reset path
            currentPath = [];
            
            // Update button state
            document.getElementById('confirmMoveBtn').disabled = true;
            
            // Center view on new position
            centerOnPlayer();
            
            // Redraw
            drawBattlefield();
        } else {
            addBattleLog(`Cannot move that far! Path cost: ${pathCost}, Movement remaining: ${currentPlayerSpeed}.`);
        }
    }
}

// Confirm attack
function confirmAttack() {
    if (selectedTargetCell) {
        const targetIsEnemy = 
            selectedTargetCell.col === enemyPos.col && 
            selectedTargetCell.row === enemyPos.row;
        
        // Check if enemy is in the targeted cell or AoE
        const enemyInAOE = currentAOECells.some(cell => 
            cell.col === enemyPos.col && cell.row === enemyPos.row
        );
        
        if (targetIsEnemy || enemyInAOE) {
            // Execute attack
            performAttack();
        } else {
            // No enemy in target
            addBattleLog('No enemy at the targeted location.');
        }
    }
}

// End the player's turn and trigger enemy actions
function endTurn() {
    addBattleLog('Ending your turn...');
    
    // Reset player's movement for next turn
    currentPlayerSpeed = playerSpeed;
    
    // Reset interaction state
    setInteractionMode('none');
    
    // Restore some mana
    const playerManaElem = document.getElementById('playerMana');
    const [current, max] = playerManaElem.textContent.split('/').map(v => parseInt(v, 10));
    const restored = Math.min(max, current + 5);  // Restore 5 mana per turn
    playerManaElem.textContent = `${restored}/${max}`;
    
    // Update player mana bar
    const manaPercentage = (restored / max) * 100;
    document.querySelector('.mana-fill').style.width = `${manaPercentage}%`;
    
    // Trigger enemy turn
    executeEnemyTurn();
}

// Highlight cells within range of a center cell
function highlightCellsInRange(center, range) {
    highlightedCells = [];
    
    for (let col = 0; col < cols; col++) {
        for (let row = 0; row < rows; row++) {
            const distance = getDistance(center.col, center.row, col, row);
            if (distance <= range) {
                highlightedCells.push({ col, row });
            }
        }
    }
}

// Get distance between two hex cells
function getDistance(col1, row1, col2, row2) {
    const dx = Math.abs(col2 - col1);
    const dy = Math.abs(row2 - row1);
    return Math.max(dx, dy);
}

// Check if a cell is in range of player
function isInRange(col, row, range) {
    return getDistance(playerPos.col, playerPos.row, col, row) <= range;
}

// Get all cells in an area of effect
function getCellsInAOE(center, radius) {
    const aoeCells = [];
    
    for (let col = 0; col < cols; col++) {
        for (let row = 0; row < rows; row++) {
            const distance = getDistance(center.col, center.row, col, row);
            if (distance <= radius) {
                aoeCells.push({ col, row });
            }
        }
    }
    
    return aoeCells;
}

// Check if two cells are adjacent
function isCellAdjacent(cell1, cell2) {
    return getDistance(cell1.col, cell1.row, cell2.col, cell2.row) <= 1;
}

// Check if a cell is already in the current path
function isCellInPath(cell) {
    return currentPath.some(p => p.col === cell.col && p.row === cell.row);
}

// Calculate the cost of a movement path
function calculatePathCost(path) {
    if (path.length <= 1) return 0;
    
    let cost = 0;
    const terrainMovementCost = terrainConfig.movement_cost || 1;
    
    for (let i = 1; i < path.length; i++) {
        // Base movement cost from game rules
        const baseCost = GAME_CONFIG.game_rules.movement.base_cost;
        
        // Apply terrain modifier
        cost += baseCost * terrainMovementCost;
    }
    
    return cost;
}

// Get pixel coordinates for a hex cell
function getPixelFromCell(col, row) {
    // Offset for even rows in a pointy-top hexgrid
    const offset = row % 2 === 0 ? 0 : hexWidth / 2;
    
    const x = col * hexWidth + offset;
    const y = row * (hexHeight * 0.75);
    
    return { x, y };
}

// Get the hex cell at a pixel coordinate
function getCellFromPixel(x, y) {
    // Convert from screen to canvas coordinates
    const canvasX = x;
    const canvasY = y;
    
    // Estimate row first (rough approximation)
    const row = Math.floor(canvasY / (hexHeight * 0.75));
    const offset = row % 2 === 0 ? 0 : hexWidth / 2;
    
    // Then calculate column
    const col = Math.floor((canvasX - offset) / hexWidth);
    
    // Check if in bounds
    if (col >= 0 && col < cols && row >= 0 && row < rows) {
        // Verify if point is actually inside the hexagon
        const { x: hexX, y: hexY } = getPixelFromCell(col, row);
        const dx = canvasX - hexX;
        const dy = canvasY - hexY;
        
        // Rough check if point is close to hex center
        if (Math.sqrt(dx * dx + dy * dy) <= hexSize) {
            return { col, row };
        }
        
        // For more precise detection, check surrounding cells
        for (let dCol = -1; dCol <= 1; dCol++) {
            for (let dRow = -1; dRow <= 1; dRow++) {
                const checkCol = col + dCol;
                const checkRow = row + dRow;
                
                if (checkCol >= 0 && checkCol < cols && checkRow >= 0 && checkRow < rows) {
                    const { x: checkX, y: checkY } = getPixelFromCell(checkCol, checkRow);
                    const checkDx = canvasX - checkX;
                    const checkDy = canvasY - checkY;
                    
                    if (Math.sqrt(checkDx * checkDx + checkDy * checkDy) <= hexSize) {
                        return { col: checkCol, row: checkRow };
                    }
                }
            }
        }
    }
    
    return null;
}

// Draw the battlefield
function drawBattlefield() {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Apply zoom and pan transformations
    ctx.save();
    ctx.translate(panOffset.x * zoomLevel, panOffset.y * zoomLevel);
    ctx.scale(zoomLevel, zoomLevel);
    
    // Draw grid
    drawHexGrid();
    
    // Draw path
    if (currentPath.length > 0) {
        drawPath();
    }
    
    // Draw highlighted cells
    if (highlightedCells.length > 0) {
        drawHighlightedCells();
    }
    
    // Draw AoE cells
    if (currentAOECells.length > 0) {
        drawAOECells();
    }
    
    // Draw tokens
    drawTokens();
    
    // Restore canvas context
    ctx.restore();
}

// Draw the hex grid
function drawHexGrid() {
    // Configure grid appearance
    const gridColor = terrainConfig.grid_color || '#333333';
    const hexFillColors = terrainConfig.hex_fill.colors || ['#ffffff'];
    const hexFillFrequency = terrainConfig.hex_fill.frequency || 1.0;
    
    for (let col = 0; col < cols; col++) {
        for (let row = 0; row < rows; row++) {
            const { x, y } = getPixelFromCell(col, row);
            
            // Determine if this hex is highlighted
            const isHighlighted = highlightedCells.some(cell => 
                cell.col === col && cell.row === row
            );
            
            // Determine if this hex is in AoE
            const isInAOE = currentAOECells.some(cell => 
                cell.col === col && cell.row === row
            );
            
            // Determine if this hex is the target
            const isTarget = selectedTargetCell && 
                selectedTargetCell.col === col && 
                selectedTargetCell.row === row;
            
            // Draw the hexagon
            drawHexagon(x, y, col, row, isHighlighted, isInAOE, isTarget, hexFillColors, gridColor, hexFillFrequency);
        }
    }
}

// Draw a single hexagon
function drawHexagon(x, y, col, row, isHighlighted, isInAOE, isTarget, hexFillColors, gridColor, hexFillFrequency) {
    const hexPoints = [];
    
    // Calculate hexagon vertices (pointy-top orientation)
    for (let i = 0; i < 6; i++) {
        const angle = 2 * Math.PI / 6 * i + Math.PI / 6;
        hexPoints.push({
            x: x + hexSize * Math.cos(angle),
            y: y + hexSize * Math.sin(angle)
        });
    }
    
    // Begin drawing the hexagon
    ctx.beginPath();
    ctx.moveTo(hexPoints[0].x, hexPoints[0].y);
    
    for (let i = 1; i < 6; i++) {
        ctx.lineTo(hexPoints[i].x, hexPoints[i].y);
    }
    
    ctx.closePath();
    
    // Fill the hexagon
    if (isTarget) {
        // Target cell (selected for attack)
        ctx.fillStyle = 'rgba(255, 0, 0, 0.4)';
    } else if (isInAOE) {
        // Area of effect cell
        ctx.fillStyle = 'rgba(255, 165, 0, 0.3)';
    } else if (isHighlighted) {
        // Cells in attack range
        ctx.fillStyle = 'rgba(255, 255, 0, 0.2)';
    } else {
        // Regular terrain cell
        // Choose a fill color randomly but consistently for each cell
        const colorIndex = Math.floor((col * 3 + row * 7) % hexFillColors.length);
        
        // Apply color variation based on frequency
        if (Math.random() < hexFillFrequency) {
            ctx.fillStyle = hexFillColors[colorIndex];
        } else {
            // Alternate with a slightly different shade
            const baseColor = hexFillColors[colorIndex];
            const r = parseInt(baseColor.slice(1, 3), 16);
            const g = parseInt(baseColor.slice(3, 5), 16);
            const b = parseInt(baseColor.slice(5, 7), 16);
            
            // Lighten or darken the color slightly
            const factor = 0.9 + Math.random() * 0.2;
            ctx.fillStyle = `rgb(${Math.floor(r * factor)}, ${Math.floor(g * factor)}, ${Math.floor(b * factor)})`;
        }
    }
    
    ctx.fill();
    
    // Draw hexagon outline
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    ctx.stroke();
    
    // Draw coordinates for debugging (uncomment if needed)
    // ctx.fillStyle = 'black';
    // ctx.font = '10px Arial';
    // ctx.fillText(`${col},${row}`, x - 10, y + 3);
}

// Draw the movement path
function drawPath() {
    if (currentPath.length < 2) return;
    
    ctx.beginPath();
    
    // Get the first point
    const start = getPixelFromCell(currentPath[0].col, currentPath[0].row);
    ctx.moveTo(start.x, start.y);
    
    // Draw line to each point in path
    for (let i = 1; i < currentPath.length; i++) {
        const { x, y } = getPixelFromCell(currentPath[i].col, currentPath[i].row);
        ctx.lineTo(x, y);
    }
    
    // Path styling
    ctx.strokeStyle = 'rgba(0, 120, 255, 0.8)';
    ctx.lineWidth = 3;
    ctx.stroke();
    
    // Draw dots at each point
    currentPath.forEach((point, index) => {
        const { x, y } = getPixelFromCell(point.col, point.row);
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        
        // First point is green, last point is red
        if (index === 0) {
            ctx.fillStyle = 'rgba(0, 200, 0, 0.9)';
        } else if (index === currentPath.length - 1) {
            ctx.fillStyle = 'rgba(200, 0, 0, 0.9)';
        } else {
            ctx.fillStyle = 'rgba(0, 100, 255, 0.9)';
        }
        
        ctx.fill();
    });
    
    // Display path cost
    const pathCost = calculatePathCost(currentPath);
    const lastPoint = getPixelFromCell(
        currentPath[currentPath.length - 1].col, 
        currentPath[currentPath.length - 1].row
    );
    
    ctx.font = '14px Arial';
    ctx.fillStyle = pathCost <= currentPlayerSpeed ? 'green' : 'red';
    ctx.fillText(`Cost: ${pathCost}/${currentPlayerSpeed}`, lastPoint.x + 15, lastPoint.y);
}

// Draw highlighted cells (for attack range)
function drawHighlightedCells() {
    // Handled directly in drawHexGrid
}

// Draw area of effect cells
function drawAOECells() {
    // Handled directly in drawHexGrid
}

// Draw player and enemy tokens
function drawTokens() {
    // Draw player token
    const playerPixel = getPixelFromCell(playerPos.col, playerPos.row);
    drawToken(playerPixel.x, playerPixel.y, 'player');
    
    // Draw enemy token
    const enemyPixel = getPixelFromCell(enemyPos.col, enemyPos.row);
    drawToken(enemyPixel.x, enemyPixel.y, 'enemy');
}

// Draw a token (player or enemy)
function drawToken(x, y, type) {
    const tokenSize = hexSize * 0.7;
    
    ctx.beginPath();
    ctx.arc(x, y, tokenSize, 0, Math.PI * 2);
    
    if (type === 'player') {
        // Player token
        ctx.fillStyle = 'rgba(0, 100, 200, 0.8)';
        ctx.strokeStyle = '#0066cc';
    } else {
        // Enemy token
        ctx.fillStyle = 'rgba(200, 50, 50, 0.8)';
        ctx.strokeStyle = '#cc3333';
    }
    
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();
    
    // Add icon or letter
    ctx.fillStyle = 'white';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(type === 'player' ? 'P' : 'E', x, y);
}

// Add a message to the battle log
function addBattleLog(message) {
    const log = document.getElementById('battleLog');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = message;
    log.appendChild(entry);
    
    // Scroll to bottom
    log.scrollTop = log.scrollHeight;
}

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', function() {
    initGame();
    
    // Center the view on the player
    centerOnPlayer();
}); 