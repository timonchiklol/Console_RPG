class TranslationManager {
    constructor() {
        this.translations = {};
        this.currentLang = document.documentElement.lang || 'en';
    }

    async loadTranslations() {
        try {
            const response = await fetch(`/translations/${this.currentLang}.json`);
            this.translations = await response.json();
        } catch (error) {
            console.error('Failed to load translations:', error);
        }
    }

    translate(key) {
        return this.translations[key] || key;
    }
}

const translationManager = new TranslationManager();

const settingsApp = Vue.createApp({
    data() {
        return {
            showSettings: false,
            interfaceLanguage: document.documentElement.lang || 'en'
        };
    },
    methods: {
        openSettings() {
            this.showSettings = true;
        },
        closeSettings() {
            this.showSettings = false;
        },
        async saveSettings() {
            try {
                const response = await fetch("/start_game", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ language: this.interfaceLanguage })
                });
                const data = await response.json();
                if (data.status === "success") {
                    location.reload();
                } else {
                    alert(translationManager.translate("language_update_error"));
                }
            } catch (error) {
                console.error("Error:", error);
            }
        }
    },
    mounted() {
        document.documentElement.lang = this.interfaceLanguage;
    }
});

// Initialize settings
document.addEventListener('DOMContentLoaded', async () => {
    await translationManager.loadTranslations();
    
    // Update all elements with data-trans attribute
    document.querySelectorAll('[data-trans]').forEach(element => {
        const key = element.getAttribute('data-trans');
        element.textContent = translationManager.translate(key);
    });
    
    const settingsAppInstance = settingsApp.mount('#settings-app');
    document.getElementById("settingsButton").addEventListener("click", function() {
        settingsAppInstance.openSettings();
    });
}); 