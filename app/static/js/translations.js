/**
 * Language Translation System for AgroDoc-AI
 * Supports: English (en), Hindi (hi), Kannada (kn)
 */

// Current language
let currentLanguage = 'en';

// Translations object (will be loaded from JSON)
let translations = {};

// Language names for display
const languageNames = {
    'en': 'EN',
    'hi': 'HI',
    'kn': 'KN'
};

// State coordinates for farm map (for translation of state names)
const stateTranslations = {
    'Andhra Pradesh': { hi: 'आंध्र प्रदेश', kn: 'ಆಂಧ್ರ ಪ್ರದೇಶ' },
    'Karnataka': { hi: 'कर्नाटक', kn: 'ಕರ್ನಾಟಕ' },
    'Maharashtra': { hi: 'महाराष्ट्र', kn: 'ಮಹಾರಾಷ್ಟ್ರ' },
    'Tamil Nadu': { hi: 'तमिलनाडु', kn: 'ತಮಿಳುನಾಡು' },
    'Telangana': { hi: 'तेलंगाना', kn: 'ತೆಲಂಗಾಣ' },
    'Kerala': { hi: 'केरल', kn: 'ಕೇರಳ' },
    'Gujarat': { hi: 'गुजरात', kn: 'ಗುಜರಾತ್' },
    'Rajasthan': { hi: 'राजस्थान', kn: 'ರಾಜಸ್ಥಾನ' },
    'Madhya Pradesh': { hi: 'मध्य प्रदेश', kn: 'ಮಧ್ಯ ಪ್ರದೇಶ' },
    'Uttar Pradesh': { hi: 'उत्तर प्रदेश', kn: 'ಉತ್ತರ ಪ್ರದೇಶ' },
    'Bihar': { hi: 'बिहार', kn: 'ಬಿಹಾರ' },
    'West Bengal': { hi: 'पश्चिम बंगाल', kn: 'ಪಶ್ಚಿಮ ಬಂಗಾಳ' },
    'Punjab': { hi: 'पंजाब', kn: 'ಪಂಜಾಬ್' },
    'Haryana': { hi: 'हरियाणा', kn: 'ಹರಿಯಾಣ' },
    'Assam': { hi: 'असम', kn: 'ಅಸ್ಸಾಂ' }
};

/**
 * Load translations from JSON file
 */
async function loadTranslations() {
    try {
        const response = await fetch('/static/js/translations.json');
        translations = await response.json();
        
        // Load saved language preference
        const savedLang = localStorage.getItem('preferredLanguage') || 'en';
        setLanguage(savedLang);
    } catch (error) {
        console.error('Error loading translations:', error);
    }
}

/**
 * Get translated text with variable substitution
 */
function translate(key, variables = {}) {
    if (!translations[currentLanguage] || !translations[currentLanguage][key]) {
        return translations['en'][key] || key;
    }
    
    let text = translations[currentLanguage][key];
    
    // Replace variables like {{ username }}
    Object.keys(variables).forEach(varName => {
        text = text.replace(new RegExp(`\\{\\{\\s*${varName}\\s*\\}\\}`, 'g'), variables[varName]);
    });
    
    return text;
}

/**
 * Apply variables to translation string
 */
function applyVariables(text, variables) {
    let result = text;
    Object.keys(variables).forEach(key => {
        result = result.replace(new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g'), variables[key]);
    });
    return result;
}

/**
 * Translate all elements on the page (including dynamically added ones)
 */
function translatePage() {
    // Update all elements with data-translate attribute
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        const translation = translations[currentLanguage][key];
        
        if (translation) {
            // Check for variables in the element
            const variables = {};
            const varAttrs = Array.from(element.attributes).filter(attr => attr.name.startsWith('data-var-'));
            varAttrs.forEach(attr => {
                const varName = attr.name.replace('data-var-', '');
                variables[varName] = attr.value;
            });
            
            // Apply translation with variables
            element.innerHTML = applyVariables(translation, variables);
        }
    });
    
    // Update placeholders for form inputs
    document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
        const key = element.getAttribute('data-translate-placeholder');
        if (translations[currentLanguage][key]) {
            element.placeholder = translations[currentLanguage][key];
        }
    });
    
    // Translate state/district dropdowns if present
    translateStateDropdowns(currentLanguage);
}

/**
 * Set the current language and update all translated elements
 */
function setLanguage(lang) {
    if (!translations[lang]) {
        console.error('Language not found:', lang);
        return;
    }
    
    currentLanguage = lang;
    localStorage.setItem('preferredLanguage', lang);
    
    // Save to backend session as well
    fetch('/auth/set-language/' + lang, {
        method: 'POST',
        credentials: 'include'
    }).catch(err => console.error('Error saving language preference:', err));
    
    // Update language button display
    const langBtn = document.getElementById('current-lang');
    if (langBtn) {
        langBtn.textContent = languageNames[lang] || 'EN';
    }
    
    // Update HTML lang attribute
    document.documentElement.lang = lang;
    
    // Translate all elements on the page
    translatePage();
    
    // Show success message
    if (lang === 'hi') {
        showLanguageToast('✅ भाषा सफलतापूर्वक बदली गई!');
    } else if (lang === 'kn') {
        showLanguageToast('✅ ಭಾಷೆ ಯಶಸ್ವಿಯಾಗಿ ಬದಲಾಯಿಸಲಾಯಿತು!');
    } else {
        showLanguageToast('✅ Language changed successfully!');
    }
    
    closeLanguageModal();
}

/**
 * Translate state and district dropdowns
 */
function translateStateDropdowns(lang) {
    const stateSelect = document.getElementById('state');
    if (!stateSelect) return;
    
    const options = stateSelect.querySelectorAll('option');
    options.forEach(option => {
        const value = option.value;
        if (value && stateTranslations[value]) {
            // Keep English in parentheses for reference
            if (lang === 'hi') {
                option.textContent = stateTranslations[value].hi + ' (' + value + ')';
            } else if (lang === 'kn') {
                option.textContent = stateTranslations[value].kn + ' (' + value + ')';
            }
        }
    });
}

/**
 * Show toast notification for language change
 */
function showLanguageToast(message) {
    const toast = document.createElement('div');
    toast.className = 'language-toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Open language selector modal
 */
function openLanguageModal() {
    const modal = document.getElementById('language-modal');
    if (modal) {
        modal.classList.add('show');
    }
}

/**
 * Close language selector modal
 */
function closeLanguageModal() {
    const modal = document.getElementById('language-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

/**
 * Initialize language system on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    loadTranslations();
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('language-modal');
        if (event.target === modal) {
            closeLanguageModal();
        }
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeLanguageModal();
        }
    });
});

// Export functions for global access
window.setLanguage = setLanguage;
window.openLanguageModal = openLanguageModal;
window.closeLanguageModal = closeLanguageModal;
window.translate = translate;
window.translatePage = translatePage;

/**
 * Translate yield impact labels dynamically
 * Call this after displaying results
 */
function translateYieldImpact() {
    // Translate labels that were set via JavaScript
    document.querySelectorAll('[data-translate-label]').forEach(element => {
        const key = element.getAttribute('data-translate-label');
        const translation = translations[currentLanguage][key];
        if (translation) {
            element.textContent = translation;
        }
    });
}
