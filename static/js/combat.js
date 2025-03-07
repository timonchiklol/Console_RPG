// Combat-related functionality
class CombatManager {
    constructor(config) {
        this.config = config;
        this.currentAttack = null;
        this.attackUsedThisTurn = false; // Flag to track if attack was used this turn
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Attack button handlers
        document.querySelectorAll('.attack-button').forEach(btn => {
            btn.addEventListener('click', (event) => this.handleAttackButtonClick(btn, event));
        });

        // Attack and cast buttons
        const attackButton = document.getElementById('attackButton');
        const castSpellButton = document.getElementById('castSpellButton');
        
        if (attackButton) {
            attackButton.addEventListener('click', (event) => this.performAttack(event));
        }
        
        if (castSpellButton) {
            castSpellButton.addEventListener('click', (event) => this.castSpell(event));
        }
        
        // End turn button
        const endTurnButton = document.getElementById('endTurnButton');
        if (endTurnButton) {
            endTurnButton.addEventListener('click', () => this.endTurn());
        }
    }
    
    // Method to end turn
    endTurn() {
        // Reset attack flag
        this.attackUsedThisTurn = false;
        
        // Enable attack buttons
        const attackButton = document.getElementById('attackButton');
        const castSpellButton = document.getElementById('castSpellButton');
        
        if (attackButton) {
            attackButton.disabled = false;
        }
        if (castSpellButton) {
            castSpellButton.disabled = true; // Spell button disabled by default
        }
        
        // Send request to server to end turn
        fetch('/api/end_turn', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (window.showNotification) {
                window.showNotification("Your turn ended", 'info');
            }
            
            // Handle enemy response
            handleEnemyTurnResponse(data);
        })
        .catch(error => {
            console.error('Error ending turn:', error);
        });
    }

    handleAttackButtonClick(button, event) {
        // If attack already used this turn, prevent selecting a new one
        if (this.attackUsedThisTurn) {
            if (window.showNotification) {
                window.showNotification("You've already attacked this turn", 'warning');
            }
            return;
        }
        
        // Remove selected class from all attack buttons
        document.querySelectorAll('.attack-button').forEach(btn => {
            btn.classList.remove('selected');
        });
        
        // Add selected class to the clicked button
        button.classList.add('selected');
        
        const attackType = button.dataset.attackType;
        const spellName = button.dataset.spellName;
        const range = parseInt(button.dataset.range);
        const aoe = parseInt(button.dataset.aoe) || 0;

        this.currentAttack = {
            type: attackType,
            spellName: spellName,
            range: range,
            aoe: aoe
        };

        // Clear any previous highlights
        if (window.clearHighlight) {
            window.clearHighlight();
        }

        // Show range for spells/attacks
        if (range && window.highlightRange) {
            window.highlightRange(window.playerPos, range, aoe);
        }

        // Show notification for selected attack or spell
        if (spellName) {
            if (window.showNotification) {
                window.showNotification(`Selected spell: ${spellName}`, 'info', button);
            }
        } else if (attackType) {
            if (window.showNotification) {
                window.showNotification(`Selected attack: ${attackType}`, 'info', button);
            }
        }

        // Call window.selectAttack and switch to attack mode
        if (window.selectAttack) {
            window.selectAttack(attackType, range, spellName);
            
            // Also switch to attack mode if we have that function
            if (window.setInteractionMode) {
                window.setInteractionMode('attack');
            }
            
            // Update the attack preview
            const previewElement = document.getElementById('attackPreview');
            if (previewElement) {
                previewElement.classList.remove('hidden');
                previewElement.textContent = spellName 
                    ? `Selected spell: ${spellName} (Range: ${range})`
                    : `Selected attack: ${attackType} (Range: ${range})`;
            }
        }

        // Handle special spells
        if (spellName === "Misty Step") {
            if (window.activateMistyStep) {
                window.activateMistyStep();
                document.getElementById('teleport-button-container').classList.remove('hidden');
            }
        } else if (spellName === "Hold Person") {
            if (window.activateHoldPerson) {
                window.activateHoldPerson();
            } else {
                console.error("Function activateHoldPerson not found");
            }
        }
    }

    selectAttack(attackType, range, spellName) {
        const attackButton = document.getElementById('attackButton');
        const castSpellButton = document.getElementById('castSpellButton');

        // Enable appropriate button based on attack type
        if (spellName) {
            attackButton.disabled = true;
            castSpellButton.disabled = false;
        } else {
            attackButton.disabled = false;
            castSpellButton.disabled = true;
        }
        
        // Clear current path when selecting an attack
        if (window.currentPath) {
            window.currentPath = [];
        }
    }

    async performAttack(event) {
        // Check if attack was already used this turn
        if (this.attackUsedThisTurn) {
            if (window.showNotification) {
                window.showNotification("You've already attacked this turn", 'warning');
            }
            return;
        }
        
        try {
            const selectedAttack = document.querySelector('.attack-button.selected');
            
            // Get selected target cell if available
            const targetCell = window.selectedTargetCell;
            
            // If no target is selected, show a notification
            if (!targetCell) {
                if (window.showNotification) {
                    window.showNotification("Please select a target within range", 'warning');
                }
                return;
            }
            
            // Check if target is in range
            if (!window.isInRange(targetCell.col, targetCell.row, this.currentAttack?.range)) {
                if (window.showNotification) {
                    window.showNotification("Target is out of range", 'warning');
                }
                return;
            }
            
            // If no attack is selected, use basic attack
            const attackType = selectedAttack ? selectedAttack.dataset.attackType : "melee_attack";
            
            // Send attack request
            const response = await fetch('/api/attack', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    attack_type: attackType,
                    target: targetCell
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                if (window.showNotification) {
                    window.showNotification(data.error, 'error');
                } else {
                    alert(data.error);
                }
            } else {
                // Mark attack as used this turn
                this.attackUsedThisTurn = true;
                
                // Disable attack buttons until next turn
                const attackButton = document.getElementById('attackButton');
                const castSpellButton = document.getElementById('castSpellButton');
                
                if (attackButton) {
                    attackButton.disabled = true;
                }
                if (castSpellButton) {
                    castSpellButton.disabled = true;
                }
                
                // Update UI
                updateInterfaceAfterAction(data);
                
                // Clear highlightings and selections
                window.clearHighlight();
            }
        } catch (error) {
            console.error('Attack error:', error);
            if (window.showNotification) {
                window.showNotification("Error performing attack: " + error.message, 'error');
            }
        }
    }

    async castSpell(event) {
        try {
            const selectedSpell = document.querySelector('.spell-btn.selected');
            
            if (!selectedSpell) {
                if (window.showNotification) {
                    window.showNotification("Please select a spell first", 'warning');
                }
                return;
            }
            
            const spellName = selectedSpell.dataset.spellName;
            const spellLevel = selectedSpell.dataset.spellLevel;
            const spellType = selectedSpell.dataset.type;
            
            // Special handling for Misty Step - already handled by teleportToSelectedCell
            if (spellName === "Misty Step") {
                // This is handled by the teleport button directly
                return;
            }
            
            // Special handling for Hold Person - check if target is selected
            if (spellName === "Hold Person") {
                if (!window.holdPersonTarget) {
            if (window.showNotification) {
                        window.showNotification("Please select an enemy target for Hold Person", 'warning');
            }
            return;
        }
        
                // Send request to cast Hold Person
                const response = await fetch('/api/cast_spell', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        spell_name: spellName,
                        target: window.holdPersonTarget,
                        spell_level: spellLevel
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
            if (window.showNotification) {
                        window.showNotification(data.error, 'error');
                    }
                } else {
                    // Mark spell as cast this turn
                    this.attackUsedThisTurn = true;
                    
                    // Disable buttons
                    const attackButton = document.getElementById('attackButton');
                    const castSpellButton = document.getElementById('castSpellButton');
                    
                    if (attackButton) attackButton.disabled = true;
                    if (castSpellButton) castSpellButton.disabled = true;
                    
                    // Update UI
                    updateInterfaceAfterAction(data);
                    
                    // Apply Hold Person effect visually
                    applyHoldPersonEffect(window.holdPersonTarget);
                    
                    // Reset Hold Person state
                    window.holdPersonActive = false;
                    window.holdPersonTarget = null;
                }
                
                // Clear highlights
                window.clearHighlight();
            return;
        }

            // For regular spells, check target
            const targetCell = window.selectedTargetCell;
            
            if (!targetCell) {
                if (window.showNotification) {
                    window.showNotification("Please select a target for your spell", 'warning');
                }
                return;
            }
            
            // Send request to cast spell
            const response = await fetch('/api/cast_spell', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    spell_name: spellName,
                    target: targetCell,
                    spell_level: spellLevel
                })
            });

            const data = await response.json();

            if (data.error) {
                if (window.showNotification) {
                    window.showNotification(data.error, 'error');
                }
            } else {
                // Mark spell as cast this turn
            this.attackUsedThisTurn = true;
            
                // Disable buttons
            const attackButton = document.getElementById('attackButton');
            const castSpellButton = document.getElementById('castSpellButton');
            
                if (attackButton) attackButton.disabled = true;
                if (castSpellButton) castSpellButton.disabled = true;

            // Update UI
                updateInterfaceAfterAction(data);
                
                // Update spell slots
                if (data.spell_slots) {
                    const level1Element = document.getElementById('spell_slots_1');
                    const level2Element = document.getElementById('spell_slots_2');
                    
                    if (level1Element && data.spell_slots['1'] !== undefined) {
                        level1Element.textContent = data.spell_slots['1'];
                    }
                    
                    if (level2Element && data.spell_slots['2'] !== undefined) {
                        level2Element.textContent = data.spell_slots['2'];
                    }
                }
            }
            
            // Clear highlights
                window.clearHighlight();

        } catch (error) {
            console.error('Spell casting error:', error);
            if (window.showNotification) {
                window.showNotification("Error casting spell: " + error.message, 'error');
            }
        }
    }
}

// Function to handle enemy turn response
function handleEnemyTurnResponse(data) {
    if (!data) return;
    
    // Update UI elements
    const charHpElement = document.getElementById('char_hp');
    const enemyHpElement = document.getElementById('enemy_hp');
    
    if (charHpElement && data.character_hp !== undefined) {
        charHpElement.textContent = data.character_hp;
    }
    
    if (enemyHpElement && data.enemy_hp !== undefined) {
        enemyHpElement.textContent = data.enemy_hp;
    }
    
    // Update enemy position if provided
    if (data.enemy_pos && window.enemyPos) {
        window.enemyPos = data.enemy_pos;
        if (window.drawHexGrid) {
            window.drawHexGrid();
        }
    }
    
    // Show combat log if provided
    if (data.combat_log && window.addToBattleLog) {
        window.addToBattleLog(data.combat_log);
    }
    
    // Handle special status
    if (data.enemy_status === "frozen") {
        if (window.showNotification) {
            window.showNotification("Enemy is frozen and skips their turn!", "success");
        }
    }
}

// Helper function to update interface after an action
function updateInterfaceAfterAction(data) {
    if (!data) return;
    
    // Update HP displays
    const charHpElement = document.getElementById('char_hp');
    const enemyHpElement = document.getElementById('enemy_hp');
    const charSpeedElement = document.getElementById('char_speed');
    
    if (charHpElement && data.character_hp !== undefined) {
        charHpElement.textContent = data.character_hp;
    }
    
    if (enemyHpElement && data.enemy_hp !== undefined) {
        enemyHpElement.textContent = data.enemy_hp;
    }
    
    if (charSpeedElement && data.movement_left !== undefined) {
        charSpeedElement.textContent = data.movement_left;
    }
    
    // Display combat log
    if (data.combat_log) {
        if (window.showNotification) {
            window.showNotification(data.combat_log, 'info');
        }
        
        if (window.addToBattleLog) {
            window.addToBattleLog(data.combat_log);
        }
    }
}

// Function to apply Hold Person effect visually
function applyHoldPersonEffect(targetCell) {
    if (!targetCell) return;
    
    // Add visual indicator
    const enemyPos = window.enemyPos;
    if (enemyPos && enemyPos.col === targetCell.col && enemyPos.row === targetCell.row) {
        // Here you could add a visual effect to the enemy
        if (window.showNotification) {
            window.showNotification("Enemy is held in place!", "success");
        }
    }
}

// Initialize combat manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.combatManager = new CombatManager(window.GAME_CONFIG);
    
    // If we don't have addToBattleLog defined, create a simple version
    if (typeof window.addToBattleLog !== 'function') {
        window.addToBattleLog = function(message) {
            console.log('Battle Log:', message);
        };
    }
});
