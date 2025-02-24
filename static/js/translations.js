// Translation Manager for D&D Console Adventure
const translationManager = {
    translations: {
        en: {},
        ru: {}
    },
    
    currentLanguage: 'en',
    
    loadTranslations: async function() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const langParam = urlParams.get('lang');
            
            // Try to get language from URL param, cookie, or browser language
            this.currentLanguage = langParam || 
                                  this.getCookie('language') || 
                                  (navigator.language && navigator.language.split('-')[0]) || 
                                  'en';
            
            // Only allow supported languages
            if (!['en', 'ru'].includes(this.currentLanguage)) {
                this.currentLanguage = 'en';
            }
            
            // Set default translations for English
            this.translations.en = {
                // Common
                'title': 'D&D Console Adventure',
                'settings': 'Settings',
                'language': 'Language',
                'save_changes': 'Save Changes',
                
                // Index page
                'welcome_message': 'Welcome to D&D Console Adventure',
                'your_name': 'Your Name',
                'enter_name': 'Enter your name',
                'create_room': 'Create New Game',
                'or_join': 'OR JOIN EXISTING GAME',
                'room_code': 'Room Code',
                'enter_room_code': 'Enter room code',
                'join_room': 'Join Game',
                'room_creation_error': 'Error creating room, please try again',
                'room_join_error': 'Error joining room, please check the code and try again',
                'feedback': 'Feedback',
                'feedback_email': 'Send your feedback to: feedback@dndconsole.com',
                
                // Character Creation
                'character_creation': 'Character Creation',
                'select_race': 'Select Your Race',
                'select_class': 'Select Your Class',
                'begin_adventure': 'Begin Adventure',
                'hp': 'HP',
                'damage': 'Damage',
                'gold': 'Gold',
                'ability_scores': 'Ability Scores',
                'hp_bonus': 'HP Bonus',
                'gold_bonus': 'Gold Bonus',
                'magic': 'Magic',
                'primary_ability': 'Primary Ability',
                'saving_throws': 'Saving Throws',
                'strength': 'Strength',
                'dexterity': 'Dexterity',
                'constitution': 'Constitution',
                'intelligence': 'Intelligence',
                'wisdom': 'Wisdom',
                'charisma': 'Charisma',
                
                // Game page
                'game': 'Game',
                'room_code_label': 'Room:',
                'click_to_copy': 'Click to copy',
                'copied': 'Copied!',
                'my_stats': 'My Stats',
                'players': 'Players',
                'save_game': 'Save',
                'load_game': 'Load',
                'leave_room': 'Leave',
                'system': 'System:',
                'dm_thinking': 'DM thinking...',
                'enter_action': 'Enter your action...',
                'character_stats': 'Character Stats',
                'level': 'Level',
                'race': 'Race',
                'class': 'Class',
                'magic_1lvl': '1st Level',
                'magic_2lvl': '2nd Level',
                'no_character_stats': 'No character stats available. Please choose your character.',
                'leave_confirm': 'Are you sure you want to leave this game? Your progress may be lost if not saved.',
                'load_game_error': 'Error loading game'
            };
            
            // Russian translations - basic
            this.translations.ru = {
                // Common
                'title': 'D&D Консольное Приключение',
                'settings': 'Настройки',
                'language': 'Язык',
                'save_changes': 'Сохранить Изменения',
                
                // Index page
                'welcome_message': 'Добро пожаловать в D&D Консольное Приключение',
                'your_name': 'Ваше Имя',
                'enter_name': 'Введите ваше имя',
                'create_room': 'Создать Новую Игру',
                'or_join': 'ИЛИ ПРИСОЕДИНИТЬСЯ К СУЩЕСТВУЮЩЕЙ ИГРЕ',
                'room_code': 'Код Комнаты',
                'enter_room_code': 'Введите код комнаты',
                'join_room': 'Присоединиться',
                'room_creation_error': 'Ошибка создания комнаты, попробуйте снова',
                'room_join_error': 'Ошибка входа в комнату, проверьте код и попробуйте снова',
                'feedback': 'Обратная связь',
                'feedback_email': 'Отправьте ваши отзывы на: feedback@dndconsole.com',
                
                // Basic game terms
                'hp': 'ЖС',
                'damage': 'Урон',
                'gold': 'Золото',
                'level': 'Уровень'
                
                // More translations can be added as needed
            };
            
            // If using server-side translations, load them
            try {
                const response = await fetch(`/translations/${this.currentLanguage}.json`);
                if (response.ok) {
                    const serverTranslations = await response.json();
                    // Merge server translations with client defaults
                    this.translations[this.currentLanguage] = {
                        ...this.translations[this.currentLanguage],
                        ...serverTranslations
                    };
                }
            } catch (e) {
                console.warn('Could not load server translations, using defaults', e);
            }
            
            // Store the language in a cookie
            this.setCookie('language', this.currentLanguage, 30);
            
            return true;
        } catch (e) {
            console.error('Error loading translations:', e);
            return false;
        }
    },
    
    translate: function(key) {
        // First try current language
        if (this.translations[this.currentLanguage] && 
            this.translations[this.currentLanguage][key]) {
            return this.translations[this.currentLanguage][key];
        }
        
        // Fall back to English
        if (this.translations.en && this.translations.en[key]) {
            return this.translations.en[key];
        }
        
        // If all else fails, return the key itself
        return key;
    },
    
    setCookie: function(name, value, days) {
        let expires = '';
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = '; expires=' + date.toUTCString();
        }
        document.cookie = name + '=' + (value || '') + expires + '; path=/';
    },
    
    getCookie: function(name) {
        const nameEQ = name + '=';
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }
}; 

// Function to get translations (used in index.js and character.js)
function getTranslations() {
    return translationManager.translations[translationManager.currentLanguage] || translationManager.translations.en || {};
}

// Function to translate the page elements based on data-trans attributes
function translatePage(language) {
    if (language) {
        translationManager.currentLanguage = language;
    }
    
    // Update all elements with data-trans attribute
    document.querySelectorAll('[data-trans]').forEach(element => {
        const key = element.getAttribute('data-trans');
        const translation = translationManager.translate(key);
        if (translation && translation !== key) {
            element.textContent = translation;
        }
    });
    
    // Update document language
    document.documentElement.lang = translationManager.currentLanguage;
}

// Initialize translations when the script loads
(async function initTranslations() {
    await translationManager.loadTranslations();
    translatePage();
})(); 