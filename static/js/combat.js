// Combat-related functionality
class CombatManager {
    constructor(config) {
        this.config = config;
        this.currentAttack = null;
        this.attackUsedThisTurn = false; // Флаг для отслеживания использования атаки в текущем ходу
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Attack button handlers
        document.querySelectorAll('.attack-button').forEach(btn => {
            btn.addEventListener('click', (event) => this.handleAttackButtonClick(btn, event));
        });

        // Attack and cast buttons
        document.getElementById('attackButton').addEventListener('click', (event) => this.performAttack(event));
        document.getElementById('castSpellButton').addEventListener('click', (event) => this.castSpell(event));
        
        // End turn button
        const endTurnButton = document.getElementById('endTurnButton');
        if (endTurnButton) {
            endTurnButton.addEventListener('click', () => this.endTurn());
        }
    }
    
    // Метод для завершения хода
    endTurn() {
        // Сбрасываем флаг использования атаки
        this.attackUsedThisTurn = false;
        
        // Активируем кнопки атак
        const attackButton = document.getElementById('attackButton');
        const castSpellButton = document.getElementById('castSpellButton');
        
        if (attackButton) {
            attackButton.disabled = false;
        }
        if (castSpellButton) {
            castSpellButton.disabled = true; // По умолчанию кнопка заклинаний отключена
        }
        
        // Здесь могут быть другие действия при завершении хода
        
        // Отправляем запрос на сервер для завершения хода
        fetch('/api/end_turn', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            // Обработка ответа сервера
            if (window.showNotification) {
                window.showNotification("Your turn ended", 'info');
            }
            
            // Здесь может быть обновление интерфейса или другие действия
        })
        .catch(error => {
            console.error('Error ending turn:', error);
        });
    }

    handleAttackButtonClick(button, event) {
        // Если атака уже использована в этом ходу, не позволяем выбирать новую
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
        if (window.gameUI) {
            window.gameUI.clearHighlight();
        }

        // Show range for spells/attacks
        if (range && window.gameUI) {
            window.gameUI.highlightRange(range, aoe);
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

        this.selectAttack(attackType, range, spellName);

        // В handleAttackButtonClick добавляем обработку Misty Step
        if (spellName === "Misty Step") {
            if (window.activateMistyStep) {
                window.activateMistyStep();
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
    }

    async performAttack(event) {
        // Проверяем, не использована ли атака в этом ходу
        if (this.attackUsedThisTurn) {
            if (window.showNotification) {
                window.showNotification("You've already attacked this turn", 'warning');
            }
            return;
        }
        
        try {
            const selectedAttack = document.querySelector('.attack-button.selected');
            
            // Если нет выбранной атаки, просто используем базовую атаку
            const attackType = selectedAttack ? selectedAttack.dataset.attackType : "melee_attack";
            
            // Отправляем запрос на атаку
            const response = await fetch('/api/attack', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `attack_type=${attackType}`
            });
            
            const data = await response.json();
            
            if (data.error) {
                if (window.showNotification) {
                    window.showNotification(data.error, 'error');
                } else {
                    alert(data.error);
                }
            } else {
                // Помечаем, что атака использована в этом ходу
                this.attackUsedThisTurn = true;
                
                // Отключаем кнопки атак до следующего хода
                const attackButton = document.getElementById('attackButton');
                const castSpellButton = document.getElementById('castSpellButton');
                
                if (attackButton) {
                    attackButton.disabled = true;
                }
                if (castSpellButton) {
                    castSpellButton.disabled = true;
                }
                
                // Обновление интерфейса
                const charHpElement = document.getElementById('char_hp');
                const enemyHpElement = document.getElementById('enemy_hp');
                const charSpeedElement = document.getElementById('char_speed');
                
                if (charHpElement) {
                    charHpElement.textContent = `${data.character_hp}/${this.config.player.max_hp}`;
                }
                
                if (enemyHpElement) {
                    enemyHpElement.textContent = `${data.enemy_hp}/${this.config.enemy.max_hp}`;
                }
                
                if (charSpeedElement) {
                    charSpeedElement.textContent = `${data.movement_left}/${this.config.player.speed}`;
                }
                
                if (window.showNotification) {
                    window.showNotification(data.combat_log, 'info');
                    
                    // Проверка победы
                    if (data.enemy_defeated) {
                        window.showNotification("You defeated the enemy!", 'success');
                    }
                } else {
                    alert(data.combat_log);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            if (window.showNotification) {
                window.showNotification('An error occurred while attacking', 'error');
            } else {
                alert('An error occurred while attacking');
            }
        }
    }

    async castSpell(event) {
        // Если текущая атака - Misty Step и выбрана клетка
        if (this.currentAttack.spellName === "Misty Step" && window.selectedTeleportCell) {
            // Вызываем телепортацию напрямую
            window.teleportToSelectedCell();
            
            // Отмечаем атаку как использованную, если нужно
            this.attackUsedThisTurn = true;
            
            // Обновляем UI
            this.updateUIAfterAction();
            
            return; // Прерываем выполнение, не отправляя запрос на сервер
        }
        
        // Проверяем, не использована ли атака в этом ходу
        if (this.attackUsedThisTurn) {
            if (window.showNotification) {
                window.showNotification("You've already attacked this turn", 'warning');
            }
            return;
        }
        
        if (!this.currentAttack?.spellName) {
            if (window.showNotification) {
                window.showNotification("No spell selected!", 'error');
            }
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
                    target: window.enemyPos || {}
                })
            });

            const data = await response.json();

            if (data.error) {
                if (window.showNotification) {
                    window.showNotification(data.error, 'error');
                }
                return;
            }

            // Помечаем, что атака использована в этом ходу
            this.attackUsedThisTurn = true;
            
            // Отключаем кнопки атак до следующего хода
            const attackButton = document.getElementById('attackButton');
            const castSpellButton = document.getElementById('castSpellButton');
            
            if (attackButton) {
                attackButton.disabled = true;
            }
            if (castSpellButton) {
                castSpellButton.disabled = true;
            }

            // Update UI
            const charHpElement = document.getElementById('char_hp');
            const enemyHpElement = document.getElementById('enemy_hp');
            const spellSlots1Element = document.getElementById('spell_slots_1');
            const spellSlots2Element = document.getElementById('spell_slots_2');
            
            if (charHpElement) {
                charHpElement.textContent = data.character_hp;
            }
            
            if (enemyHpElement) {
                enemyHpElement.textContent = data.enemy_hp;
            }
            
            if (spellSlots1Element) {
                spellSlots1Element.textContent = data.spell_slots['1'];
            }
            
            if (spellSlots2Element) {
                spellSlots2Element.textContent = data.spell_slots['2'];
            }

            // Специальная обработка для промахов
            if (data.spell_missed) {
                if (window.showNotification) {
                    window.showNotification(data.combat_log, 'warning');
                }
            } else {
                // Show spell effect notification
                if (window.showNotification) {
                    window.showNotification(data.combat_log, 'success');
                }
            }

            // Clear range highlight after casting
            if (window.gameUI) {
                window.gameUI.clearHighlight();
            }
            if (window.drawHexGrid) {
                window.drawHexGrid();
            }

            // В castSpell добавляем обработку телепортации
            if (this.currentAttack && this.currentAttack.spellName === "Misty Step") {
                // Телепортируем игрока на выбранную клетку
                if (window.teleportToSelectedCell) {
                    window.teleportToSelectedCell();
                    
                    // Расходуем слот заклинания
                    if (spellSlots2Element) {
                        const current = parseInt(spellSlots2Element.textContent);
                        spellSlots2Element.textContent = Math.max(0, current - 1);
                    }
                    
                    // Не помечаем атаку как использованную, чтобы можно было ходить
                    return;
                }
            }

        } catch (error) {
            console.error('Error casting spell:', error);
            if (window.showNotification) {
                window.showNotification('Error casting spell: ' + error.message, 'error');
            }
        }
    }
}

// Initialize combat manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.combatManager = new CombatManager(window.GAME_CONFIG);
});

// Находим и исправляем функцию, которая обрабатывает ответ после хода врага
function handleEnemyTurnResponse(response) {
    // ... существующий код ...
    
    // Проверяем, действительно ли враг переместился, сравнивая старую и новую позиции
    const oldEnemyPos = JSON.stringify(window.enemyPos || {});
    const newEnemyPos = JSON.stringify(response.enemy_pos || {});
    
    // Обновляем позицию врага
    window.enemyPos = response.enemy_pos;
    
    // Перерисовываем поле
    if (window.drawHexGrid) {
        window.drawHexGrid();
    }
    
    // Показываем сообщение о перемещении только если позиция действительно изменилась
    if (oldEnemyPos !== newEnemyPos) {
        if (window.showNotification) {
            window.showNotification("Enemy has moved!", "info");
        }
    }
    
    // ... остальной код ...
} 