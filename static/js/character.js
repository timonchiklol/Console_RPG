const characterApp = Vue.createApp({
    data() {
        return {
            races: {},
            classes: {},
            selectedRace: null,
            selectedClass: null,
            submitted: false
        };
    },
    methods: {
        translate(key) {
            return translationManager.translate(key);
        },
        async loadOptions() {
            try {
                const racesResponse = await fetch('/get_races');
                const classesResponse = await fetch('/get_classes');
                this.races = await racesResponse.json();
                this.classes = await classesResponse.json();
            } catch(e) {
                console.error(e);
            }
        },
        selectRace(race) {
            this.selectedRace = race;
        },
        selectClass(className) {
            this.selectedClass = className;
        },
        async createCharacter() {
            if (!this.selectedRace || !this.selectedClass) return;
            this.submitted = true;
            try {
                const response = await fetch('/choose_character', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ race: this.selectedRace, class: this.selectedClass })
                });
                const data = await response.json();
                if (data.status === 'success') {
                    window.location.href = '/game';
                } else {
                    alert(this.translate('character_creation_error'));
                    this.submitted = false;
                }
            } catch(e) {
                console.error(e);
                this.submitted = false;
            }
        }
    }
});

// Initialize the app after translations are loaded
document.addEventListener('DOMContentLoaded', async () => {
    await translationManager.loadTranslations();
    
    // Update all elements with data-trans attribute
    document.querySelectorAll('[data-trans]').forEach(el => {
        const key = el.getAttribute('data-trans');
        el.textContent = translationManager.translate(key);
    });
    
    const app = characterApp.mount('#character-app');
    app.loadOptions();
}); 