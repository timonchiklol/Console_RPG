// Get translations
const translations = getTranslations();

// Translate the page based on saved language
translatePage();

// Create Vue app
const app = Vue.createApp({
    data() {
        return {
            selectedRace: null,
            selectedClass: null,
            races: {},
            classes: {},
            submitted: false,
            settingsVisible: false,
            language: document.documentElement.lang || 'en',
            loading: true,
            error: null
        };
    },
    methods: {
        translate(key) {
            return translations[this.language]?.[key] || key;
        },
        toggleSettings() {
            this.settingsVisible = !this.settingsVisible;
            console.log('Settings visibility toggled:', this.settingsVisible);
        },
        closeSettings() {
            this.settingsVisible = false;
            console.log('Settings closed');
        },
        selectRace(race) {
            this.selectedRace = race;
            console.log('Selected race:', race);
        },
        selectClass(className) {
            this.selectedClass = className;
            console.log('Selected class:', className);
        },
        async createCharacter() {
            if (!this.selectedRace || !this.selectedClass) return;
            this.submitted = true;
            
            try {
                console.log('Submitting character:', this.selectedRace, this.selectedClass);
                const response = await fetch('/choose_character', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        race: this.selectedRace,
                        class: this.selectedClass
                    }),
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    console.error('Error creating character:', data.error);
                    this.error = data.error || 'Failed to create character';
                    this.submitted = false;
                    return;
                }
                
                console.log('Character created successfully, redirecting to game');
                // Redirect to game page
                window.location.href = '/game';
            } catch (error) {
                console.error('Error creating character:', error);
                this.error = 'Network error while creating character';
                this.submitted = false;
            }
        },
        async fetchRacesAndClasses() {
            this.loading = true;
            this.error = null;
            
            try {
                console.log('Fetching races and classes...');
                
                // Fetch races
                const racesResponse = await fetch('/get_races');
                if (!racesResponse.ok) {
                    throw new Error(`Failed to fetch races: ${racesResponse.status} ${racesResponse.statusText}`);
                }
                
                this.races = await racesResponse.json();
                console.log('Races fetched:', Object.keys(this.races).length);
                
                // Fetch classes
                const classesResponse = await fetch('/get_classes');
                if (!classesResponse.ok) {
                    throw new Error(`Failed to fetch classes: ${classesResponse.status} ${classesResponse.statusText}`);
                }
                
                this.classes = await classesResponse.json();
                console.log('Classes fetched:', Object.keys(this.classes).length);
                
                // If we have no races or classes, something is wrong
                if (Object.keys(this.races).length === 0 || Object.keys(this.classes).length === 0) {
                    throw new Error('Received empty data for races or classes');
                }
                
            } catch (error) {
                console.error('Error fetching races and classes:', error);
                this.error = error.message || 'Failed to load character data';
                // Add fallback data in case the fetch fails
                if (Object.keys(this.races).length === 0) {
                    this.races = {
                        "Human": { "hp": 30, "damage": "1d6", "gold": 100, "ability_scores": { "strength": 1, "dexterity": 1, "constitution": 1, "intelligence": 1, "wisdom": 1, "charisma": 1 } },
                        "Elf": { "hp": 25, "damage": "1d4", "gold": 80, "ability_scores": { "strength": 0, "dexterity": 2, "constitution": -1, "intelligence": 1, "wisdom": 1, "charisma": 2 } }
                    };
                }
                if (Object.keys(this.classes).length === 0) {
                    this.classes = {
                        "Warrior": { "hp_bonus": 5, "gold_bonus": 10, "magic": "no", "primary_ability": "strength", "saving_throws": ["strength", "constitution"] },
                        "Wizard": { "hp_bonus": 0, "gold_bonus": 5, "magic": "yes", "primary_ability": "intelligence", "saving_throws": ["intelligence", "wisdom"] }
                    };
                }
            } finally {
                this.loading = false;
            }
        },
        async changeLanguage() {
            try {
                // Save language to server
                await fetch('/start_game', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ language: this.language }),
                });
                
                // Update page language
                document.documentElement.lang = this.language;
                translatePage(this.language);
                this.closeSettings();
                
                // Reload translations
                Object.assign(translations, getTranslations());
                
                // Reload races and classes to get translated names
                await this.fetchRacesAndClasses();
            } catch (error) {
                console.error('Error changing language:', error);
                this.error = 'Failed to change language';
            }
        }
    },
    mounted() {
        console.log('Character app mounted');
        
        // Ensure settings are closed on initial load
        this.settingsVisible = false;
        
        // Add escape key listener
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.settingsVisible) {
                this.closeSettings();
            }
        });
        
        // Fetch races and classes on mount
        this.fetchRacesAndClasses();
        
        // Translate the page on load
        translatePage(this.language);
    }
});

// Mount the app
app.mount('#character-app'); 