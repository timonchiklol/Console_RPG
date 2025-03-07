/**
 * Battle Combat - Handles combat logic, dice rolling, and enemy AI
 */

// Track game state
let playerHealth = GAME_CONFIG.player.stats.hp;
let playerMaxHealth = GAME_CONFIG.player.stats.max_hp;
let playerMana = GAME_CONFIG.player.stats.mana;
let playerMaxMana = GAME_CONFIG.player.stats.max_mana;

let enemyHealth = GAME_CONFIG.enemy.stats.hp;
let enemyMaxHealth = GAME_CONFIG.enemy.stats.max_hp;

let isPlayerTurn = true;
let gameEnded = false;

// Dice rolling modal
const diceModal = document.getElementById('diceModal');
const diceGraphic = document.getElementById('diceGraphic');
const diceNotation = document.getElementById('diceNotation');
const diceResult = document.getElementById('diceResult');

/**
 * Perform an attack on the enemy
 */
function performAttack() {
    if (gameEnded) return;
    if (!currentAttack) return;
    
    // Check if player has enough mana for spells
    if (currentAttack.type === 'spell') {
        const manaCost = currentAttack.manaCost;
        if (playerMana < manaCost) {
            addBattleLog(`Not enough mana to cast ${currentAttack.name}!`);
            return;
        }
    }
    
    // Check if we have a target
    if (!selectedTargetCell) {
        addBattleLog('No target selected.');
        return;
    }
    
    addBattleLog(`Using ${currentAttack.name}...`);
    
    // Roll for hit check
    rollToHit().then(hitResult => {
        if (hitResult.hit) {
            // Hit successful - roll for damage
            const damageNotation = currentAttack.damage;
            
            // Handle healing spells differently
            if (currentAttack.hasOwnProperty('healing')) {
                rollDice(currentAttack.healing).then(result => {
                    applyHealing(result.total);
                });
            } else {
                if (damageNotation === '0') {
                    // No damage spell - might be a utility spell
                    addBattleLog(`${currentAttack.name} cast successfully!`);
                } else {
                    // Roll for damage
                    rollDice(damageNotation).then(result => {
                        applyDamage(result.total);
                    });
                }
            }
            
            // Deduct mana cost for spells
            if (currentAttack.type === 'spell') {
                playerMana -= currentAttack.manaCost;
                updatePlayerMana();
            }
            
        } else {
            // Attack missed
            addBattleLog(`${currentAttack.name} missed!`);
            
            // Still deduct mana for spells even on miss
            if (currentAttack.type === 'spell') {
                playerMana -= currentAttack.manaCost;
                updatePlayerMana();
            }
        }
        
        // Reset attack state
        resetAttackState();
    });
}

/**
 * Roll to determine if an attack hits
 */
function rollToHit() {
    return new Promise(resolve => {
        showDiceModal('1d20');
        
        // Simulate API call for hit check
        fetch('/api/check_hit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ attack: currentAttack.name })
        })
        .then(response => response.json())
        .then(data => {
            // Update dice modal with result
            diceResult.textContent = data.roll;
            
            // Close modal after delay
            setTimeout(() => {
                hideDiceModal();
                
                if (data.hit) {
                    if (data.critical) {
                        addBattleLog(`Critical hit! (Rolled ${data.roll})`);
                    } else {
                        addBattleLog(`Hit! (Rolled ${data.roll})`);
                    }
                } else {
                    addBattleLog(`Miss! (Rolled ${data.roll})`);
                }
                
                resolve(data);
            }, 1500);
        })
        .catch(error => {
            console.error('Error checking hit:', error);
            hideDiceModal();
            resolve({ hit: Math.random() > 0.3, roll: Math.floor(Math.random() * 20) + 1 });
        });
    });
}

/**
 * Roll dice with given notation (e.g., "2d6+3")
 */
function rollDice(notation) {
    return new Promise(resolve => {
        showDiceModal(notation);
        
        // Simulate API call for dice roll
        fetch('/api/roll_dice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dice: notation })
        })
        .then(response => response.json())
        .then(data => {
            // Update dice modal with result
            diceResult.textContent = `${data.total} (${data.rolls.join(', ')})`;
            
            // Close modal after delay
            setTimeout(() => {
                hideDiceModal();
                
                // Log the roll result
                if (data.modifier) {
                    addBattleLog(`Rolled ${notation}: ${data.rolls.join(', ')} + ${data.modifier} = ${data.total}`);
                } else {
                    addBattleLog(`Rolled ${notation}: ${data.rolls.join(', ')} = ${data.total}`);
                }
                
                resolve(data);
            }, 1500);
        })
        .catch(error => {
            console.error('Error rolling dice:', error);
            hideDiceModal();
            
            // Fallback dice rolling if API fails
            const result = simulateDiceRoll(notation);
            resolve(result);
        });
    });
}

/**
 * Show the dice rolling modal
 */
function showDiceModal(notation) {
    diceNotation.textContent = notation;
    diceResult.textContent = '-';
    diceModal.style.display = 'flex';
    
    // Animate dice roll
    diceGraphic.style.animation = 'none';
    setTimeout(() => {
        diceGraphic.style.animation = 'roll 1s ease-out';
    }, 10);
}

/**
 * Hide the dice rolling modal
 */
function hideDiceModal() {
    diceModal.style.display = 'none';
}

/**
 * Apply damage to the enemy
 */
function applyDamage(amount) {
    // Calculate actual damage after any resistances
    const actualDamage = amount;
    
    // Apply damage to enemy
    enemyHealth = Math.max(0, enemyHealth - actualDamage);
    
    // Update enemy health display
    document.getElementById('enemyHealth').textContent = `${enemyHealth}/${enemyMaxHealth}`;
    
    // Update enemy health bar
    const healthPercentage = (enemyHealth / enemyMaxHealth) * 100;
    document.querySelector('.enemy-health-fill').style.width = `${healthPercentage}%`;
    
    addBattleLog(`Dealt ${actualDamage} damage to enemy!`);
    
    // Check if enemy is defeated
    if (enemyHealth <= 0) {
        gameEnded = true;
        addBattleLog('Enemy defeated! Victory!');
        
        // Disable actions
        document.getElementById('confirmMoveBtn').disabled = true;
        document.getElementById('attackBtn').disabled = true;
        document.getElementById('endTurnBtn').disabled = true;
    }
}

/**
 * Apply healing to the player
 */
function applyHealing(amount) {
    // Calculate actual healing
    const actualHealing = amount;
    
    // Apply healing to player
    playerHealth = Math.min(playerMaxHealth, playerHealth + actualHealing);
    
    // Update player health display
    document.getElementById('playerHealth').textContent = `${playerHealth}/${playerMaxHealth}`;
    
    // Update player health bar
    const healthPercentage = (playerHealth / playerMaxHealth) * 100;
    document.querySelector('.health-fill').style.width = `${healthPercentage}%`;
    
    addBattleLog(`Healed for ${actualHealing} health!`);
}

/**
 * Reset the attack state after an attack
 */
function resetAttackState() {
    // Reset attack UI state
    selectedTargetCell = null;
    currentAOECells = [];
    highlightedCells = [];
    
    // Return to move mode
    setInteractionMode('move');
    
    // Update button states
    document.getElementById('attackBtn').disabled = true;
    
    // Redraw battlefield
    drawBattlefield();
}

/**
 * Update the player mana display
 */
function updatePlayerMana() {
    document.getElementById('playerMana').textContent = `${playerMana}/${playerMaxMana}`;
    
    // Update mana bar
    const manaPercentage = (playerMana / playerMaxMana) * 100;
    document.querySelector('.mana-fill').style.width = `${manaPercentage}%`;
}

/**
 * Execute the enemy's turn
 */
function executeEnemyTurn() {
    if (gameEnded) return;
    
    // Delay for better UX
    setTimeout(() => {
        addBattleLog("Enemy's turn...");
        
        // Get enemy position and abilities
        const enemy = GAME_CONFIG.enemy;
        
        // Send current game state to server for enemy AI
        fetch('/api/enemy_turn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                player_position: playerPos,
                enemy_position: enemyPos,
                enemy_type: enemy.name.toLowerCase(),
                player_health: playerHealth,
                enemy_health: enemyHealth
            })
        })
        .then(response => response.json())
        .then(data => {
            // Process enemy action
            if (data.action === 'move') {
                // Enemy moves
                enemyPos = data.new_position;
                addBattleLog(data.message);
                drawBattlefield();
                
                // After moving, check if enemy can now attack
                setTimeout(() => {
                    checkEnemyAttack();
                }, 1000);
            } else if (data.action === 'attack') {
                // Enemy attacks
                processEnemyAttack(data.attack_result);
            }
        })
        .catch(error => {
            console.error('Error during enemy turn:', error);
            
            // Fallback AI behavior if API fails
            executeLocalEnemyAI();
        });
    }, 1000);
}

/**
 * Check if enemy can attack after moving
 */
function checkEnemyAttack() {
    // Get enemy abilities
    const enemy = GAME_CONFIG.enemy;
    
    // Calculate distance to player
    const distance = getDistance(enemyPos.col, enemyPos.row, playerPos.col, playerPos.row);
    
    // Find an ability within range
    let attackAbility = null;
    
    for (const key in enemy.abilities) {
        const ability = enemy.abilities[key];
        if (distance <= ability.range) {
            attackAbility = { ...ability, name: key };
            break;
        }
    }
    
    // If an ability is in range, use it
    if (attackAbility) {
        // Enemy attacks
        addBattleLog(`Enemy prepares to attack with ${attackAbility.name}!`);
        
        // Roll to hit
        setTimeout(() => {
            const hitRoll = Math.floor(Math.random() * 20) + 1;
            const hit = hitRoll > 10;
            
            if (hit) {
                addBattleLog(`Enemy hit! (Rolled ${hitRoll})`);
                
                // Roll for damage
                const damageNotation = attackAbility.damage;
                const damageResult = simulateDiceRoll(damageNotation);
                
                // Apply damage to player
                applyDamageToPlayer(damageResult.total);
            } else {
                addBattleLog(`Enemy missed! (Rolled ${hitRoll})`);
            }
            
            // End enemy turn
            finishEnemyTurn();
        }, 1000);
    } else {
        // End enemy turn if no attack possible
        finishEnemyTurn();
    }
}

/**
 * Process enemy attack data from server
 */
function processEnemyAttack(attackResult) {
    addBattleLog(`Enemy attacks with ${attackResult.ability_name}!`);
    
    if (attackResult.hit) {
        addBattleLog(`Enemy hit! (Rolled ${attackResult.roll})`);
        
        // Display damage roll result
        const damageRolls = attackResult.damage_rolls.join(', ');
        addBattleLog(`Damage roll: ${damageRolls} = ${attackResult.damage}`);
        
        // Apply damage to player
        applyDamageToPlayer(attackResult.damage);
    } else {
        addBattleLog(`Enemy missed! (Rolled ${attackResult.roll})`);
    }
    
    // End enemy turn
    finishEnemyTurn();
}

/**
 * Apply damage to the player
 */
function applyDamageToPlayer(amount) {
    // Calculate actual damage after any resistances
    const actualDamage = amount;
    
    // Apply damage to player
    playerHealth = Math.max(0, playerHealth - actualDamage);
    
    // Update player health display
    document.getElementById('playerHealth').textContent = `${playerHealth}/${playerMaxHealth}`;
    
    // Update player health bar
    const healthPercentage = (playerHealth / playerMaxHealth) * 100;
    document.querySelector('.health-fill').style.width = `${healthPercentage}%`;
    
    addBattleLog(`You took ${actualDamage} damage!`);
    
    // Check if player is defeated
    if (playerHealth <= 0) {
        gameEnded = true;
        addBattleLog('You have been defeated!');
        
        // Disable actions
        document.getElementById('confirmMoveBtn').disabled = true;
        document.getElementById('attackBtn').disabled = true;
        document.getElementById('endTurnBtn').disabled = true;
    }
}

/**
 * Finish the enemy turn and return control to player
 */
function finishEnemyTurn() {
    setTimeout(() => {
        if (!gameEnded) {
            isPlayerTurn = true;
            addBattleLog('Your turn.');
            setInteractionMode('move');
        }
    }, 1000);
}

/**
 * Fallback enemy AI if server is unavailable
 */
function executeLocalEnemyAI() {
    // Calculate distance to player
    const distance = getDistance(enemyPos.col, enemyPos.row, playerPos.col, playerPos.row);
    
    // Get enemy abilities
    const enemy = GAME_CONFIG.enemy;
    
    // Find an ability within range
    let attackAbility = null;
    
    for (const key in enemy.abilities) {
        const ability = enemy.abilities[key];
        if (distance <= ability.range) {
            attackAbility = { ...ability, name: key };
            break;
        }
    }
    
    if (attackAbility) {
        // Enemy attacks
        addBattleLog(`Enemy prepares to attack with ${attackAbility.name}!`);
        
        // Roll to hit
        setTimeout(() => {
            const hitRoll = Math.floor(Math.random() * 20) + 1;
            const hit = hitRoll > 10;
            
            if (hit) {
                addBattleLog(`Enemy hit! (Rolled ${hitRoll})`);
                
                // Roll for damage
                const damageNotation = attackAbility.damage;
                const damageResult = simulateDiceRoll(damageNotation);
                
                // Apply damage to player
                applyDamageToPlayer(damageResult.total);
            } else {
                addBattleLog(`Enemy missed! (Rolled ${hitRoll})`);
            }
            
            // End enemy turn
            finishEnemyTurn();
        }, 1000);
    } else {
        // Enemy moves toward player
        addBattleLog("Enemy moves towards you...");
        
        // Simple move toward logic
        if (enemyPos.col < playerPos.col) {
            enemyPos.col += 1;
        } else if (enemyPos.col > playerPos.col) {
            enemyPos.col -= 1;
        }
        
        if (enemyPos.row < playerPos.row) {
            enemyPos.row += 1;
        } else if (enemyPos.row > playerPos.row) {
            enemyPos.row -= 1;
        }
        
        // Redraw battlefield
        drawBattlefield();
        
        // Check if enemy can now attack
        setTimeout(() => {
            checkEnemyAttack();
        }, 1000);
    }
}

/**
 * Simulate a dice roll locally (fallback if API is unavailable)
 */
function simulateDiceRoll(notation) {
    // Parse dice notation: "2d6+3"
    const parts = notation.toLowerCase().replace(/\s/g, '').split('d');
    
    let count = 1;
    let sides = 6;
    let modifier = 0;
    
    if (parts.length === 2) {
        // Parse number of dice
        if (parts[0]) {
            count = parseInt(parts[0]);
        }
        
        // Parse sides and modifier
        if (parts[1].includes('+')) {
            const modParts = parts[1].split('+');
            sides = parseInt(modParts[0]);
            modifier = parseInt(modParts[1]);
        } else {
            sides = parseInt(parts[1]);
        }
    }
    
    // Roll the dice
    const rolls = [];
    for (let i = 0; i < count; i++) {
        rolls.push(Math.floor(Math.random() * sides) + 1);
    }
    
    // Calculate total
    const total = rolls.reduce((sum, roll) => sum + roll, 0) + modifier;
    
    return { rolls, total, modifier };
} 