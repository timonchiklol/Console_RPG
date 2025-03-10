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
let isDragging = false;

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
    
    // Right-click or middle-click or ctrl+click for panning
    if (e.button === 2 || e.button === 1 || e.ctrlKey) {
        e.preventDefault();
        isPanning = true;
        isDragging = true;
        lastPanPos = { x: e.clientX, y: e.clientY };
        canvas.style.cursor = 'grabbing';
        return;
    }
    
    // Left-click for interaction
    const cell = getCellFromPixel(x, y);
    
    if (cell) {
        if (interactionMode === 'move') {
            // Only start drawing path if clicking on player
            if (cell.col === playerPos.col && cell.row === playerPos.row) {
                isDrawingPath = true;
                currentPath = [{ col: cell.col, row: cell.row }];
                drawBattlefield();
            } else {
                // Don't auto-calculate path when clicking elsewhere
                // The path will remain visible until user applies the move or draws a new path
            }
        } else if (interactionMode === 'attack') {
            // Select a target for attack using proper hex distance
            if (isInHexRange(cell.col, cell.row, currentAttack.range)) {
                selectedTargetCell = cell;
                document.getElementById('attackBtn').disabled = false;
                
                // Calculate AoE cells using proper hex geometry
                if (currentAttack.aoe > 0) {
                    currentAOECells = getHexCellsInAOE(selectedTargetCell, currentAttack.aoe);
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
    if (isPanning && isDragging) {
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
        if (interactionMode === 'move') {
            if (isDrawingPath) {
                // Only draw path if user clicked on player and is dragging
                if (isHexAdjacent(currentPath[currentPath.length - 1], cell)) {
                    if (!isHexCellInPath(cell)) {
                        // Add new cell to path
                        currentPath.push({ col: cell.col, row: cell.row });
                    } else {
                        // If moving back, remove cells after this one
                        const index = currentPath.findIndex(p => p.col === cell.col && p.row === cell.row);
                        currentPath = currentPath.slice(0, index + 1);
                    }
                    
                    // Check if path is within speed limit
                    const pathCost = calculateManualPathCost(currentPath);
                    document.getElementById('confirmMoveBtn').disabled = pathCost > currentPlayerSpeed;
                    
                    drawBattlefield();
                }
            }
            // Remove the auto path preview on hover since we want the path to stay visible
        } else if (interactionMode === 'attack') {
            // Preview AoE if hovering over a valid target using hex geometry
            if (isInHexRange(cell.col, cell.row, currentAttack.range)) {
                if (currentAttack.aoe > 0) {
                    currentAOECells = getHexCellsInAOE(cell, currentAttack.aoe);
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
        isDragging = false;
        canvas.style.cursor = 'default';
        return;
    }
    
    if (interactionMode === 'move' && isDrawingPath) {
        // End path drawing but keep the path visible
        isDrawingPath = false;
        
        // Enable/disable confirm button based on path cost
        if (currentPath.length > 1) {
            const pathCost = calculateManualPathCost(currentPath);
            document.getElementById('confirmMoveBtn').disabled = pathCost > currentPlayerSpeed;
        } else {
            document.getElementById('confirmMoveBtn').disabled = true;
        }
        
        drawBattlefield();
    }
    
    isDragging = false;
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

// Touch event handlers for mobile - updated for manual path drawing
function handleTouchStart(e) {
    e.preventDefault();
    
    if (e.touches.length === 1) {
        // Single touch - check for interaction first, then pan
        const touch = e.touches[0];
        const rect = canvas.getBoundingClientRect();
        const x = (touch.clientX - rect.left) / zoomLevel - panOffset.x;
        const y = (touch.clientY - rect.top) / zoomLevel - panOffset.y;
        
        const cell = getCellFromPixel(x, y);
        
        // Start touch tracking for potential pan operation
        lastPanPos = { x: touch.clientX, y: touch.clientY };
        
        if (cell) {
            if (interactionMode === 'move') {
                // If touching player, start drawing path
                if (cell.col === playerPos.col && cell.row === playerPos.row) {
                    isDrawingPath = true;
                    currentPath = [{ col: cell.col, row: cell.row }];
                    drawBattlefield();
                    
                    // Set flag to prevent immediate panning
                    isDragging = false;
                    return;
                } else {
                    // If touching elsewhere, calculate auto path
                    pathDrawingMode = 'auto';
                    const pathCost = calculateHexDistance(playerPos, cell) * GAME_CONFIG.game_rules.movement.base_cost * (terrainConfig.movement_cost || 1);
                    
                    if (pathCost <= currentPlayerSpeed) {
                        currentPath = findHexPath(playerPos, cell);
                        document.getElementById('confirmMoveBtn').disabled = false;
                    } else {
                        currentPath = [];
                        document.getElementById('confirmMoveBtn').disabled = true;
                        addBattleLog(`That location is too far away. Maximum movement: ${currentPlayerSpeed}`);
                    }
                    drawBattlefield();
                    return;
                }
            } else if (interactionMode === 'attack') {
                // Select attack target
                if (isInHexRange(cell.col, cell.row, currentAttack.range)) {
                    selectedTargetCell = cell;
                    document.getElementById('attackBtn').disabled = false;
                    
                    if (currentAttack.aoe > 0) {
                        currentAOECells = getHexCellsInAOE(selectedTargetCell, currentAttack.aoe);
                    }
                    
                    drawBattlefield();
                    return;
                }
            }
        }
        
        // If not interacting with a cell, enable panning after a short delay and movement
        setTimeout(() => {
            // Only start panning if the touch has moved significantly
            if (Math.abs(touch.clientX - lastPanPos.x) > 10 || 
                Math.abs(touch.clientY - lastPanPos.y) > 10) {
                isPanning = true;
                isDragging = true;
            }
        }, 100);
        
    } else if (e.touches.length === 2) {
        // Two touches - pinch zoom
        isPanning = false;
        isDragging = false;
        isDrawingPath = false;
        
        // Calculate initial distance for zoom
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const initialDistance = Math.hypot(
            touch2.clientX - touch1.clientX,
            touch2.clientY - touch1.clientY
        );
        
        // Store initial values
        canvas.dataset.initialPinchDistance = initialDistance;
        canvas.dataset.initialZoom = zoomLevel;
    }
}

function handleTouchMove(e) {
    e.preventDefault();
    
    if (e.touches.length === 1) {
        const touch = e.touches[0];
        const rect = canvas.getBoundingClientRect();
        const x = (touch.clientX - rect.left) / zoomLevel - panOffset.x;
        const y = (touch.clientY - rect.top) / zoomLevel - panOffset.y;
        
        // Handle manual path drawing
        if (isDrawingPath && pathDrawingMode === 'manual' && interactionMode === 'move') {
            const cell = getCellFromPixel(x, y);
            
            if (cell && isHexAdjacent(currentPath[currentPath.length - 1], cell)) {
                if (!isHexCellInPath(cell)) {
                    // Add new cell to path
                    currentPath.push({ col: cell.col, row: cell.row });
                } else {
                    // If moving back, remove cells after this one
                    const index = currentPath.findIndex(p => p.col === cell.col && p.row === cell.row);
                    currentPath = currentPath.slice(0, index + 1);
                }
                
                // Check if path is within speed limit
                const pathCost = calculateManualPathCost(currentPath);
                document.getElementById('confirmMoveBtn').disabled = pathCost > currentPlayerSpeed;
                
                drawBattlefield();
                
                // Since we're drawing a path, don't pan
                isPanning = false;
                return;
            }
        }
        
        // Handle panning
        if (isPanning && isDragging) {
            const dx = touch.clientX - lastPanPos.x;
            const dy = touch.clientY - lastPanPos.y;
            
            panOffset.x += dx / zoomLevel;
            panOffset.y += dy / zoomLevel;
            
            lastPanPos = { x: touch.clientX, y: touch.clientY };
            drawBattlefield();
        } else {
            // Update last position even if not actively panning
            lastPanPos = { x: touch.clientX, y: touch.clientY };
        }
    } else if (e.touches.length === 2) {
        // Two finger pinch zoom
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        
        // Calculate new distance
        const currentDistance = Math.hypot(
            touch2.clientX - touch1.clientX,
            touch2.clientY - touch1.clientY
        );
        
        // Get initial values
        const initialDistance = parseFloat(canvas.dataset.initialPinchDistance);
        const initialZoom = parseFloat(canvas.dataset.initialZoom);
        
        if (initialDistance && initialZoom) {
            // Calculate new zoom level
            const scaleFactor = currentDistance / initialDistance;
            const newZoom = Math.max(0.5, Math.min(3, initialZoom * scaleFactor));
            
            // Calculate center point of the pinch
            const centerX = (touch1.clientX + touch2.clientX) / 2;
            const centerY = (touch1.clientY + touch2.clientY) / 2;
            
            // Adjust pan offset to zoom around center of pinch
            const rect = canvas.getBoundingClientRect();
            const mouseX = centerX - rect.left;
            const mouseY = centerY - rect.top;
            
            // Adjust pan offset to zoom around pinch center
            if (newZoom !== zoomLevel) {
                panOffset.x = mouseX / zoomLevel - (mouseX / newZoom - panOffset.x * zoomLevel / newZoom);
                panOffset.y = mouseY / zoomLevel - (mouseY / newZoom - panOffset.y * zoomLevel / newZoom);
                zoomLevel = newZoom;
            }
            
            drawBattlefield();
        }
    }
}

function handleTouchEnd(e) {
    e.preventDefault();
    
    // Reset states
    if (e.touches.length === 0) {
        isPanning = false;
        isDragging = false;
        
        if (interactionMode === 'move') {
            isDrawingPath = false;
        }
    }
    
    // Clean up pinch zoom data
    delete canvas.dataset.initialPinchDistance;
    delete canvas.dataset.initialZoom;
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
        // Calculate path cost using the manual path cost calculation
        const pathCost = calculateManualPathCost(currentPath);
        
        if (pathCost <= currentPlayerSpeed) {
            // Update player position to the end of the path
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
            const distance = calculateHexDistance(center, { col, row });
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
        // Use deterministic color generation based on cell position
        const colorIndex = Math.floor((col * 3 + row * 7) % hexFillColors.length);
        const baseColor = hexFillColors[colorIndex];
        
        // Use a deterministic random value instead of Math.random()
        // This ensures consistent coloring regardless of interactions
        const pseudoRandom = ((col * 13 + row * 23) % 100) / 100;
        
        if (pseudoRandom < hexFillFrequency) {
            ctx.fillStyle = baseColor;
        } else {
            // Create a slightly different shade in a deterministic way
            const r = parseInt(baseColor.slice(1, 3), 16);
            const g = parseInt(baseColor.slice(3, 5), 16);
            const b = parseInt(baseColor.slice(5, 7), 16);
            
            // Use deterministic factor instead of random
            const factor = 0.9 + (((col * 7 + row * 11) % 20) / 100);
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

// Add a function to calculate minimal path cost (A* algorithm)
function calculateMinimalPathCost(startCell, endCell) {
    // Implement a simplified distance calculation
    const terrainMovementCost = terrainConfig.movement_cost || 1;
    const baseCost = GAME_CONFIG.game_rules.movement.base_cost;
    
    // Calculate Manhattan distance for hex grid
    const dx = Math.abs(endCell.col - startCell.col);
    const dy = Math.abs(endCell.row - startCell.row);
    
    // The cost is the distance multiplied by the base movement cost and terrain modifier
    const distance = Math.max(dx, dy);
    return distance * baseCost * terrainMovementCost;
}

// Add pathfinding function using A* algorithm
function findShortestPath(startCell, endCell) {
    // Create open and closed sets for A* search
    const openSet = [startCell];
    const closedSet = [];
    
    // Store g-scores (movement cost from start) and f-scores (g-score + heuristic)
    const gScore = {};
    const fScore = {};
    
    // Store how we got to each cell
    const cameFrom = {};
    
    // Initialize scores
    const startKey = `${startCell.col},${startCell.row}`;
    gScore[startKey] = 0;
    fScore[startKey] = heuristic(startCell, endCell);
    
    while (openSet.length > 0) {
        // Find cell with lowest f-score
        let current = openSet[0];
        let lowestFScore = fScore[`${current.col},${current.row}`];
        let currentIndex = 0;
        
        for (let i = 1; i < openSet.length; i++) {
            const cell = openSet[i];
            const cellKey = `${cell.col},${cell.row}`;
            
            if (fScore[cellKey] < lowestFScore) {
                lowestFScore = fScore[cellKey];
                current = cell;
                currentIndex = i;
            }
        }
        
        // If we've reached the end, reconstruct and return the path
        if (current.col === endCell.col && current.row === endCell.row) {
            return reconstructPath(cameFrom, current);
        }
        
        // Remove current from open set and add to closed set
        openSet.splice(currentIndex, 1);
        closedSet.push(current);
        
        // Check all neighbors
        const neighbors = getNeighbors(current);
        
        for (const neighbor of neighbors) {
            const neighborKey = `${neighbor.col},${neighbor.row}`;
            
            // Skip if in closed set
            if (closedSet.some(cell => cell.col === neighbor.col && cell.row === neighbor.row)) {
                continue;
            }
            
            // Calculate new g-score
            const currentKey = `${current.col},${current.row}`;
            const moveCost = 1; // Basic move cost between adjacent cells
            const terrainFactor = terrainConfig.movement_cost || 1;
            const newGScore = gScore[currentKey] + (moveCost * GAME_CONFIG.game_rules.movement.base_cost * terrainFactor);
            
            // If not in open set, add it
            if (!openSet.some(cell => cell.col === neighbor.col && cell.row === neighbor.row)) {
                openSet.push(neighbor);
            }
            // Skip if we already have a better path
            else if (gScore[neighborKey] !== undefined && newGScore >= gScore[neighborKey]) {
                continue;
            }
            
            // This is the best path so far
            cameFrom[neighborKey] = current;
            gScore[neighborKey] = newGScore;
            fScore[neighborKey] = newGScore + heuristic(neighbor, endCell);
        }
    }
    
    // No path found
    return [startCell];
}

// Heuristic function for A* (Manhattan distance for hex grid)
function heuristic(a, b) {
    return Math.max(Math.abs(a.col - b.col), Math.abs(a.row - b.row));
}

// Get all valid neighbors of a cell
function getNeighbors(cell) {
    const neighbors = [];
    
    // Directions for hex grid
    const directions = [
        { col: 1, row: 0 },   // right
        { col: -1, row: 0 },  // left
        { col: 0, row: 1 },   // down
        { col: 0, row: -1 },  // up
        { col: 1, row: -1 },  // up-right
        { col: -1, row: -1 }, // up-left
        { col: 1, row: 1 },   // down-right
        { col: -1, row: 1 }   // down-left
    ];
    
    for (const dir of directions) {
        const newCol = cell.col + dir.col;
        const newRow = cell.row + dir.row;
        
        // Check if within bounds
        if (newCol >= 0 && newCol < cols && newRow >= 0 && newRow < rows) {
            neighbors.push({ col: newCol, row: newRow });
        }
    }
    
    return neighbors;
}

// Reconstruct path from cameFrom records
function reconstructPath(cameFrom, current) {
    const path = [current];
    
    while (true) {
        const currentKey = `${current.col},${current.row}`;
        
        if (cameFrom[currentKey] === undefined) {
            break;
        }
        
        current = cameFrom[currentKey];
        path.unshift(current);
    }
    
    return path;
}

// Calculate proper hex grid distance (cube coordinates method)
function calculateHexDistance(a, b) {
    // Convert to cube coordinates first
    const aCube = offsetToCube(a.col, a.row);
    const bCube = offsetToCube(b.col, b.row);
    
    // Calculate cube distance
    return Math.max(
        Math.abs(aCube.x - bCube.x),
        Math.abs(aCube.y - bCube.y),
        Math.abs(aCube.z - bCube.z)
    );
}

// Convert offset coordinates to cube coordinates
function offsetToCube(col, row) {
    // For odd-q offset (horizontal layout, odd rows shifted right)
    const x = col - Math.floor(row / 2);
    const z = row;
    const y = -x - z;
    return { x, y, z };
}

// Convert cube coordinates to offset coordinates
function cubeToOffset(x, y, z) {
    const col = x + Math.floor(z / 2);
    const row = z;
    return { col, row };
}

// Check if a cell is in hex range from player
function isInHexRange(col, row, range) {
    return calculateHexDistance(playerPos, { col, row }) <= range;
}

// Get all cells within hex AoE radius
function getHexCellsInAOE(center, radius) {
    const aoeCells = [];
    const centerCube = offsetToCube(center.col, center.row);
    
    // Check all potential cells within bounds
    for (let col = 0; col < cols; col++) {
        for (let row = 0; row < rows; row++) {
            const cellCube = offsetToCube(col, row);
            
            // Calculate hex distance in cube coordinates
            const distance = Math.max(
                Math.abs(centerCube.x - cellCube.x),
                Math.abs(centerCube.y - cellCube.y),
                Math.abs(centerCube.z - cellCube.z)
            );
            
            if (distance <= radius) {
                aoeCells.push({ col, row });
            }
        }
    }
    
    return aoeCells;
}

// Find a path using proper hex neighbors
function findHexPath(startCell, endCell) {
    // Create open and closed sets
    const openSet = [startCell];
    const closedSet = [];
    
    // Store g-scores and f-scores
    const gScore = {};
    const fScore = {};
    
    // Store how we got to each cell
    const cameFrom = {};
    
    // Initialize scores
    const startKey = `${startCell.col},${startCell.row}`;
    gScore[startKey] = 0;
    fScore[startKey] = hexHeuristic(startCell, endCell);
    
    while (openSet.length > 0) {
        // Find cell with lowest f-score
        let current = openSet[0];
        let lowestFScore = fScore[`${current.col},${current.row}`];
        let currentIndex = 0;
        
        for (let i = 1; i < openSet.length; i++) {
            const cell = openSet[i];
            const cellKey = `${cell.col},${cell.row}`;
            
            if (fScore[cellKey] < lowestFScore) {
                lowestFScore = fScore[cellKey];
                current = cell;
                currentIndex = i;
            }
        }
        
        // If we've reached the end, reconstruct and return the path
        if (current.col === endCell.col && current.row === endCell.row) {
            return reconstructHexPath(cameFrom, current);
        }
        
        // Remove current from open set and add to closed set
        openSet.splice(currentIndex, 1);
        closedSet.push(current);
        
        // Check all hex neighbors
        const neighbors = getHexNeighbors(current);
        
        for (const neighbor of neighbors) {
            const neighborKey = `${neighbor.col},${neighbor.row}`;
            
            // Skip if in closed set
            if (closedSet.some(cell => cell.col === neighbor.col && cell.row === neighbor.row)) {
                continue;
            }
            
            // Calculate new g-score
            const currentKey = `${current.col},${current.row}`;
            const moveCost = GAME_CONFIG.game_rules.movement.base_cost * (terrainConfig.movement_cost || 1);
            const newGScore = gScore[currentKey] + moveCost;
            
            // If not in open set, add it
            if (!openSet.some(cell => cell.col === neighbor.col && cell.row === neighbor.row)) {
                openSet.push(neighbor);
            }
            // Skip if we already have a better path
            else if (gScore[neighborKey] !== undefined && newGScore >= gScore[neighborKey]) {
                continue;
            }
            
            // This is the best path so far
            cameFrom[neighborKey] = current;
            gScore[neighborKey] = newGScore;
            fScore[neighborKey] = newGScore + hexHeuristic(neighbor, endCell);
        }
    }
    
    // No path found
    return [startCell];
}

// Hex-specific heuristic for A* (hex distance)
function hexHeuristic(a, b) {
    return calculateHexDistance(a, b);
}

// Get all valid hex neighbors
function getHexNeighbors(cell) {
    const neighbors = [];
    
    // Proper hex directions for odd-q offset grid
    const directions = [
        [+1,  0], // right
        [+1, -1], // up-right
        [ 0, -1], // up-left
        [-1,  0], // left
        [ 0, +1], // down-left
        [+1, +1]  // down-right
    ];
    
    // Even rows have different neighbors than odd rows
    if (cell.row % 2 === 1) {
        // Odd row
        directions[1] = [0, -1]; // up-right -> up
        directions[2] = [-1, -1]; // up-left
        directions[4] = [-1, +1]; // down-left
        directions[5] = [0, +1]; // down-right -> down
    }
    
    for (const [dCol, dRow] of directions) {
        const newCol = cell.col + dCol;
        const newRow = cell.row + dRow;
        
        // Check if within bounds
        if (newCol >= 0 && newCol < cols && newRow >= 0 && newRow < rows) {
            neighbors.push({ col: newCol, row: newRow });
        }
    }
    
    return neighbors;
}

// Reconstruct path from cameFrom records
function reconstructHexPath(cameFrom, current) {
    const path = [current];
    
    while (true) {
        const currentKey = `${current.col},${current.row}`;
        
        if (cameFrom[currentKey] === undefined) {
            break;
        }
        
        current = cameFrom[currentKey];
        path.unshift(current);
    }
    
    return path;
}

// Calculate the cost of a manually drawn path
function calculateManualPathCost(path) {
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

// Check if two hex cells are adjacent
function isHexAdjacent(cell1, cell2) {
    return calculateHexDistance(cell1, cell2) === 1;
}

// Check if a cell is in the current path
function isHexCellInPath(cell) {
    return currentPath.some(p => p.col === cell.col && p.row === cell.row);
}

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', function() {
    initGame();
    
    // Center the view on the player
    centerOnPlayer();
}); 