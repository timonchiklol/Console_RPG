// Combat-related functionality
class CombatManager {
    constructor(config) {
        this.config = config;
        this.currentAttack = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Attack button handlers
        document.querySelectorAll('.attack-button').forEach(btn => {
            btn.addEventListener('click', (event) => this.handleAttackButtonClick(btn, event));
        });

        // Attack and cast buttons
        document.getElementById('attackButton').addEventListener('click', (event) => this.performAttack(event.target));
        document.getElementById('castSpellButton').addEventListener('click', (event) => this.castSpell(event.target));

        // Dice roll handlers
        document.getElementById('rollHitButton').addEventListener('click', (event) => this.rollHit(event.target));
        document.getElementById('rollDamageButton').addEventListener('click', (event) => this.rollDamage(event.target));
    }

    handleAttackButtonClick(button, event) {
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
        window.gameUI.clearHighlight();

        // Show range for spells/attacks
        if (range) {
            window.gameUI.highlightRange(range, aoe);
        }

        // Show notification for selected attack or spell
        if (spellName) {
            window.showNotification(`Selected spell: ${spellName}`, 'info', button);
        } else if (attackType) {
            window.showNotification(`Selected attack: ${attackType}`, 'info', button);
        }

        this.selectAttack(attackType, range, spellName);
    }

    selectAttack(attackType, range, spellName) {
        const attackButton = document.getElementById('attackButton');
        const castSpellButton = document.getElementById('castSpellButton');
        const diceControls = document.getElementById('diceControls');

        // Enable appropriate button based on attack type
        if (spellName) {
            attackButton.disabled = true;
            castSpellButton.disabled = false;
        } else {
            attackButton.disabled = false;
            castSpellButton.disabled = true;
        }

        diceControls.classList.remove('hidden');
    }

    async rollHit(buttonElement) {
        try {
            const response = await fetch('/api/roll_dice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: 'sides=20'
            });
            const data = await response.json();
            const hitRoll = data.result;

            // Show dice result popup
            window.showDiceResult(hitRoll, 'Hit Roll');
            
            if (hitRoll >= 10) {
                window.showNotification(`Hit roll: ${hitRoll} - Success!`, 'success', buttonElement);
                document.getElementById('rollDamageButton').classList.remove('hidden');
            } else {
                window.showNotification(`Hit roll: ${hitRoll} - Miss!`, 'error', buttonElement);
                document.getElementById('rollDamageButton').classList.add('hidden');
            }

            return hitRoll;
        } catch (error) {
            console.error('Error rolling hit:', error);
            window.showNotification('Error rolling hit: ' + error.message, 'error', buttonElement);
        }
    }

    async rollDamage(buttonElement) {
        try {
            const response = await fetch('/api/roll_dice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: 'sides=6'
            });
            const data = await response.json();
            const damageRoll = data.result;
            
            // Show dice result popup
            window.showDiceResult(damageRoll, 'Damage Roll');
            
            window.showNotification(`Damage roll: ${damageRoll}`, 'info', buttonElement);
            
            return damageRoll;
        } catch (error) {
            console.error('Error rolling damage:', error);
            window.showNotification('Error rolling damage: ' + error.message, 'error', buttonElement);
        }
    }

    async performAttack(buttonElement) {
        if (!window.gameUI.checkAdjacent()) {
            window.showNotification("Must be adjacent to enemy to attack!", 'error', buttonElement);
            return;
        }

        const hitRoll = await this.rollHit(buttonElement);
        if (hitRoll >= 10) {
            const damageRoll = await this.rollDamage(buttonElement);
            await this.performAttackWithRolls(this.currentAttack.type, hitRoll, damageRoll, buttonElement);
        }
    }

    async performAttackWithRolls(attackType, hitRoll, damageRoll, buttonElement) {
        try {
            const response = await fetch('/api/attack', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `attack_type=${attackType}&hit_roll=${hitRoll}&damage_roll=${damageRoll}`
            });

            const data = await response.json();

            if (data.error) {
                window.showNotification(data.error, 'error', buttonElement);
                return;
            }

            // Update UI
            document.getElementById('char_speed').textContent = data.movement_left;
            document.getElementById('enemy_hp').textContent = data.enemy_hp;
            
            // Show notification with combat result
            window.showNotification(data.combat_log, 'success', buttonElement);

            // Hide dice controls after attack
            document.getElementById('diceControls').classList.add('hidden');

        } catch (error) {
            console.error('Error performing attack:', error);
            window.showNotification('Error performing attack: ' + error.message, 'error', buttonElement);
        }
    }

    async castSpell(buttonElement) {
        if (!this.currentAttack?.spellName) {
            window.showNotification("No spell selected!", 'error', buttonElement);
            return;
        }

        if (!window.gameUI.checkAdjacent() && !window.gameUI.isInRange(window.enemyPos.col, window.enemyPos.row, this.currentAttack.range)) {
            window.showNotification("Target is not in range!", 'error', buttonElement);
            return;
        }

        try {
            const response = await fetch('/api/cast_spell', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    spell_name: this.currentAttack.spellName,
                    target: window.enemyPos
                })
            });

            const data = await response.json();

            if (data.error) {
                window.showNotification(data.error, 'error', buttonElement);
                return;
            }

            // Update UI
            document.getElementById('char_hp').textContent = data.character_hp;
            document.getElementById('enemy_hp').textContent = data.enemy_hp;
            document.getElementById('spell_slots_1').textContent = data.spell_slots['1'];
            document.getElementById('spell_slots_2').textContent = data.spell_slots['2'];

            // Show spell effect notification
            window.showNotification(data.combat_log, 'success', buttonElement);

            // Clear range highlight after casting
            window.gameUI.clearHighlight();
            window.drawHexGrid();

        } catch (error) {
            console.error('Error casting spell:', error);
            window.showNotification('Error casting spell: ' + error.message, 'error', buttonElement);
        }
    }
}

// Initialize combat manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.combatManager = new CombatManager(window.GAME_CONFIG);
}); 