/**
 * Battle Index - Character Selection Page JS
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get all selection cards
    const raceCards = document.querySelectorAll('.race-card');
    const classCards = document.querySelectorAll('.class-card');
    const battlefieldCards = document.querySelectorAll('.battlefield-card');
    
    // Get form input elements
    const raceInput = document.getElementById('raceInput');
    const classInput = document.getElementById('classInput');
    const battlefieldInput = document.getElementById('battlefieldInput');
    
    // Get summary span elements
    const selectedRaceSpan = document.getElementById('selectedRace');
    const selectedClassSpan = document.getElementById('selectedClass');
    const selectedBattlefieldSpan = document.getElementById('selectedBattlefield');
    
    // Initialize default selections
    let selectedRace = raceInput.value;
    let selectedClass = classInput.value;
    let selectedBattlefield = battlefieldInput.value;
    
    // Mark default selections as selected
    markDefaultSelections();
    
    // Add click event listeners to race cards
    raceCards.forEach(card => {
        card.addEventListener('click', function() {
            // Get race from data attribute
            const race = this.getAttribute('data-race');
            
            // Update form input
            raceInput.value = race;
            selectedRace = race;
            
            // Update summary display
            selectedRaceSpan.textContent = race;
            
            // Visual selection
            raceCards.forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
    
    // Add click event listeners to class cards
    classCards.forEach(card => {
        card.addEventListener('click', function() {
            // Get class from data attribute
            const charClass = this.getAttribute('data-class');
            
            // Update form input
            classInput.value = charClass;
            selectedClass = charClass;
            
            // Update summary display
            selectedClassSpan.textContent = charClass;
            
            // Visual selection
            classCards.forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
    
    // Add click event listeners to battlefield cards
    battlefieldCards.forEach(card => {
        card.addEventListener('click', function() {
            // Get battlefield from data attribute
            const battlefield = this.getAttribute('data-battlefield');
            
            // Update form input
            battlefieldInput.value = battlefield;
            selectedBattlefield = battlefield;
            
            // Get the name from the card's heading
            const battlefieldName = this.querySelector('h4').textContent;
            
            // Update summary display
            selectedBattlefieldSpan.textContent = battlefieldName;
            
            // Visual selection
            battlefieldCards.forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
    
    /**
     * Marks the default selections on page load
     */
    function markDefaultSelections() {
        // Mark default race card as selected
        const defaultRaceCard = document.querySelector(`.race-card[data-race="${selectedRace}"]`);
        if (defaultRaceCard) {
            defaultRaceCard.classList.add('selected');
        }
        
        // Mark default class card as selected
        const defaultClassCard = document.querySelector(`.class-card[data-class="${selectedClass}"]`);
        if (defaultClassCard) {
            defaultClassCard.classList.add('selected');
        }
        
        // Mark default battlefield card as selected
        const defaultBattlefieldCard = document.querySelector(`.battlefield-card[data-battlefield="${selectedBattlefield}"]`);
        if (defaultBattlefieldCard) {
            defaultBattlefieldCard.classList.add('selected');
            
            // Update the battlefield name in the summary
            if (defaultBattlefieldCard) {
                const battlefieldName = defaultBattlefieldCard.querySelector('h4').textContent;
                selectedBattlefieldSpan.textContent = battlefieldName;
            }
        }
    }
    
    // Form validation
    document.getElementById('characterForm').addEventListener('submit', function(event) {
        // If any required field is missing, prevent form submission
        if (!selectedRace || !selectedClass || !selectedBattlefield) {
            event.preventDefault();
            alert('Please select a race, class, and battlefield before starting.');
        }
    });
}); 