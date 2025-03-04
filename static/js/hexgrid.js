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

// Добавляем переменные для Misty Step
let awaitingMistyStepTarget = false;
let selectedTeleportCell = null;

// Добавляем поддержку Hold Person
let holdPersonActive = false;

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
            // Вычисляем координаты центра гексагона
            let x = col * hexSize * 1.5 + hexSize;
            let y = row * hexSize * Math.sqrt(3) + (col % 2) * hexSize * Math.sqrt(3) / 2 + hexSize;
            
            // Проверка, находится ли клетка в подсвеченной зоне
            let isHighlighted = highlightedCells.some(cell => cell.col === col && cell.row === row);
            let isInAOE = selectedCell && currentAOE > 0 && 
                          getDistance(col, row, selectedCell.col, selectedCell.row) <= currentAOE;
            
            drawHexagon(ctx, x, y, hexSize, isHighlighted, isInAOE, col, row);
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
    
    ctx.strokeStyle = currentTerrain.grid_color;
    ctx.stroke();
}

// Исправленная функция получения клетки из координат клика
function getCellFromPixel(x, y) {
    // Размеры шестиугольника
    const hexWidth = hexSize * 2;
    const hexHeight = Math.sqrt(3) * hexSize;
    
    // Сначала находим приблизительную колонку и строку
    let col = Math.floor(x / (hexWidth * 0.75));
    let row = Math.floor(y / hexHeight);
    
    // Учитываем смещение для нечетных колонок
    if (col % 2 === 1) {
        row = Math.floor((y - hexHeight / 2) / hexHeight);
    }
    
    // Дополнительная проверка для граничных ячеек
    // Поскольку шестиугольники имеют наклонные границы
    const centerX = col * (hexWidth * 0.75) + hexSize;
    const centerY = row * hexHeight + ((col % 2) * (hexHeight / 2)) + hexSize;
    
    // Расчет расстояния от центра ячейки до точки клика
    const dx = x - centerX;
    const dy = y - centerY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    // Если точка находится далеко от центра, проверяем соседние ячейки
    if (distance > hexSize / 2) {
        // Проверяем соседние ячейки, чтобы найти ближайшую
        const possibleCells = [
            {col: col, row: row},
            {col: col+1, row: row},
            {col: col-1, row: row},
            {col: col, row: row+1},
            {col: col, row: row-1},
            {col: col+1, row: row + (col % 2 === 0 ? 0 : 1)},
            {col: col-1, row: row + (col % 2 === 0 ? 0 : 1)},
            {col: col+1, row: row + (col % 2 === 0 ? -1 : 0)},
            {col: col-1, row: row + (col % 2 === 0 ? -1 : 0)}
        ];
        
        let bestDistance = distance;
        let bestCell = {col, row};
        
        for (const cell of possibleCells) {
            // Пропускаем ячейки за пределами сетки
            if (cell.col < 0 || cell.col >= gridCols || cell.row < 0 || cell.row >= gridRows) {
                continue;
            }
            
            const cellCenterX = cell.col * (hexWidth * 0.75) + hexSize;
            const cellCenterY = cell.row * hexHeight + ((cell.col % 2) * (hexHeight / 2)) + hexSize;
            
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
    
    // Проверка границ сетки
    if (col < 0) col = 0;
    if (row < 0) row = 0;
    if (col >= gridCols) col = gridCols - 1;
    if (row >= gridRows) row = gridRows - 1;
    
    console.log(`Точные координаты клика: (${x}, ${y}), выбрана клетка: (${col}, ${row})`);
    
    return { col, row };
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

// Mouse event handlers
let canvas = document.getElementById("hexCanvas");

canvas.addEventListener("mousedown", function(e) {
    console.log("Mouse down event", awaitingMistyStepTarget);
    
    // Сначала проверяем режим Misty Step (важно проверить это первым)
    if (awaitingMistyStepTarget) {
        console.log("In Misty Step target selection mode");
        let rect = canvas.getBoundingClientRect();
        let x = e.clientX - rect.left;
        let y = e.clientY - rect.top;
        let cell = getCellFromPixel(x, y);
        
        console.log("Selected cell:", cell);
        
        // Проверяем, что клетка не занята врагом
        if (cell.col === enemyPos.col && cell.row === enemyPos.row) {
            if (window.showNotification) {
                window.showNotification("Нельзя телепортироваться на клетку с врагом", "warning");
            } else {
                alert("Нельзя телепортироваться на клетку с врагом");
            }
            return;
        }
        
        // Сохраняем выбранную клетку
        selectedTeleportCell = cell;
        
        // Перерисовываем с новой выбранной клеткой
        drawHexGrid();
        
        if (window.showNotification) {
            window.showNotification(`Клетка (${cell.col}, ${cell.row}) выбрана. Нажмите 'Teleport' для телепортации.`, "info");
        } else {
            alert(`Клетка (${cell.col}, ${cell.row}) выбрана. Нажмите 'Teleport' для телепортации.`);
        }
        
        // Включаем кнопку телепортации
        const teleportButton = document.getElementById('teleportButton');
        if (teleportButton) {
            teleportButton.classList.remove('hidden');
        }
        
        return; // Прерываем обработку
    }
    
    // Оставшийся код для движения
    // Новая проверка - можно ли двигаться
    if (playerSpeed <= 0) {
        return;  // No more movement left
    }
    
    let rect = canvas.getBoundingClientRect();
    let x = e.clientX - rect.left;
    let y = e.clientY - rect.top;
    let cell = getCellFromPixel(x, y);
    
    // Only start drawing if clicking on player position
    if (cell && cell.col === playerPos.col && cell.row === playerPos.row) {
        drawingPath = true;
        currentPath = [playerPos];
        drawHexGrid();
    }
});

canvas.addEventListener("mousemove", function(e) {
    if (!drawingPath) return;
    
    let rect = canvas.getBoundingClientRect();
    let x = e.clientX - rect.left;
    let y = e.clientY - rect.top;
    let cell = getCellFromPixel(x, y);
    
    if (cell) {
        // Don't allow moving to enemy position
        if (cell.col === enemyPos.col && cell.row === enemyPos.row) {
            return;
        }
        
        // Calculate path to current cell
        currentPath = computePath(playerPos, cell);
        drawHexGrid();
    }
});

canvas.addEventListener("mouseup", function() {
    drawingPath = false;
});

canvas.addEventListener("mouseleave", function() {
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
    
    // Сбрасываем состояние Misty Step и Hold Person
    awaitingMistyStepTarget = false;
    selectedTeleportCell = null;
    holdPersonActive = false;
    window.holdPersonTarget = null;
    
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

// Исправляем обработчик клика для правильного выбора клетки
canvas.onclick = function(e) {
    // Если активен режим Hold Person
    if (holdPersonActive) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const cell = getCellFromPixel(x, y);
        
        if (!cell) return; // Защита от клика вне поля
        
        // Проверяем, что клетка находится в диапазоне заклинания
        const isInRange = highlightedCells.some(c => c.col === cell.col && c.row === cell.row);
        if (!isInRange) {
            if (window.showNotification) {
                window.showNotification("Эта клетка вне диапазона Hold Person", "warning");
            }
            return;
        }
        
        // Проверяем, есть ли враг на этой клетке
        if (cell.col === enemyPos.col && cell.row === enemyPos.row) {
            // Выбираем или обновляем выбор цели
            window.holdPersonTarget = {col: cell.col, row: cell.row};
            
            // Перерисовываем поле с новой выделенной клеткой
            drawHexGrid();
            
            if (window.showNotification) {
                window.showNotification("Враг выбран для Hold Person. Нажмите 'Cast Spell'", "success");
            }
        } else {
            if (window.showNotification) {
                window.showNotification("В этой клетке нет врага для Hold Person", "warning");
            }
        }
        
        return; // Предотвращаем дальнейшую обработку
    }
    
    // Обработка для Misty Step и других случаев
    // ...остальной код обработчика клика...
};

/* Expose functions and variables to the global window object */
window.playerPos = playerPos;
window.enemyPos = enemyPos;
window.playerSpeed = playerSpeed;
window.currentPath = currentPath;
window.drawHexGrid = drawHexGrid;
window.initializeHexColors = initializeHexColors;
window.getCellsInRange = getCellsInRange;
window.checkAdjacent = checkAdjacent;
window.applyMove = applyMove;
window.activateMistyStep = activateMistyStep;
window.teleportToSelectedCell = teleportToSelectedCell;
window.activateHoldPerson = activateHoldPerson; 