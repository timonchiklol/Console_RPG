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
            btn.addEventListener('click', () => this.handleAttackButtonClick(btn));
        });

        // Attack and cast buttons
        document.getElementById('attackButton').addEventListener('click', () => this.performAttack());
        document.getElementById('castSpellButton').addEventListener('click', () => this.castSpell());

        // Dice roll handlers
        document.getElementById('rollHitButton').addEventListener('click', () => this.rollHit());
        document.getElementById('rollDamageButton').addEventListener('click', () => this.rollDamage());
    }

    handleAttackButtonClick(button) {
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

    async rollHit() {
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

            window.gameUI.addToBattleLog(`Hit roll: ${hitRoll}`);

            if (hitRoll >= 10) {
                document.getElementById('rollDamageButton').classList.remove('hidden');
            } else {
                window.gameUI.addToBattleLog("Attack missed!");
                document.getElementById('rollDamageButton').classList.add('hidden');
            }

            return hitRoll;
        } catch (error) {
            console.error('Error rolling hit:', error);
            window.gameUI.addToBattleLog('Error rolling hit: ' + error.message);
        }
    }

    async rollDamage() {
        try {
            const response = await fetch('/api/roll_dice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: 'sides=6'
            });
            const data = await response.json();
            return data.result;
        } catch (error) {
            console.error('Error rolling damage:', error);
            window.gameUI.addToBattleLog('Error rolling damage: ' + error.message);
        }
    }

    async performAttack() {
        if (!window.gameUI.checkAdjacent()) {
            window.gameUI.addToBattleLog("Must be adjacent to enemy to attack!");
            return;
        }

        const hitRoll = await this.rollHit();
        if (hitRoll >= 10) {
            const damageRoll = await this.rollDamage();
            await this.performAttackWithRolls(this.currentAttack.type, hitRoll, damageRoll);
        }
    }

    async performAttackWithRolls(attackType, hitRoll, damageRoll) {
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
                window.gameUI.addToBattleLog(data.error);
                return;
            }

            // Update UI
            document.getElementById('char_speed').textContent = data.movement_left;
            document.getElementById('enemy_hp').textContent = data.enemy_hp;
            window.gameUI.addToBattleLog(data.combat_log);

            // Hide dice controls after attack
            document.getElementById('diceControls').classList.add('hidden');

        } catch (error) {
            console.error('Error performing attack:', error);
            window.gameUI.addToBattleLog('Error performing attack: ' + error.message);
        }
    }

    async castSpell() {
        if (!this.currentAttack?.spellName) {
            window.gameUI.addToBattleLog("No spell selected!");
            return;
        }

        if (!window.gameUI.checkAdjacent() && !window.gameUI.isInRange(window.enemyPos.col, window.enemyPos.row, this.currentAttack.range)) {
            window.gameUI.addToBattleLog("Target is not in range!");
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
                window.gameUI.addToBattleLog(data.error);
                return;
            }

            // Update UI
            document.getElementById('char_hp').textContent = data.character_hp;
            document.getElementById('enemy_hp').textContent = data.enemy_hp;
            document.getElementById('spell_slots_1').textContent = data.spell_slots['1'];
            document.getElementById('spell_slots_2').textContent = data.spell_slots['2'];

            window.gameUI.addToBattleLog(data.combat_log);

            // Clear range highlight after casting
            window.gameUI.clearHighlight();
            window.drawHexGrid();

        } catch (error) {
            console.error('Error casting spell:', error);
            window.gameUI.addToBattleLog('Error casting spell: ' + error.message);
        }
    }
}

// Initialize combat manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.combatManager = new CombatManager(window.GAME_CONFIG);
}); 