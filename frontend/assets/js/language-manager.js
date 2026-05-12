// language-manager.js
class LanguageManager {
  constructor() {
    this.currentLanguage = localStorage.getItem('appLang') || 'en';
    // Let's add the selector to the DOM
    document.addEventListener('DOMContentLoaded', () => {
      this.initLanguageSelector();
      this.applyTranslations();
    });
  }

  initLanguageSelector() {
    if (!document.getElementById('lang-selector')) {
      const wrapper = document.createElement('div');
      wrapper.style.cssText = 'position: absolute; top: 15px; right: 150px; z-index: 1000;';
      wrapper.className = 'lang-selector-wrapper';
      
      const selectHtml = `
        <select id="lang-selector" style="padding: 8px; border-radius: 5px; border: 1px solid #ccc; background: white; font-weight: bold; color: #333;">
          <option value="en">English</option>
          <option value="hi">हिंदी (Hindi)</option>
          <option value="ta">தமிழ் (Tamil)</option>
          <option value="kn">ಕನ್ನಡ (Kannada)</option>
          <option value="te">తెలుగు (Telugu)</option>
          <option value="bn">বাংলা (Bengali)</option>
          <option value="mr">मराठी (Marathi)</option>
        </select>
      `;
      wrapper.innerHTML = selectHtml;
      document.body.appendChild(wrapper);
    }

    const selectEl = document.getElementById('lang-selector');
    if(selectEl) {
      selectEl.value = this.currentLanguage;
      
      selectEl.addEventListener('change', (e) => {
        this.currentLanguage = e.target.value;
        localStorage.setItem('appLang', this.currentLanguage);
        this.applyTranslations();
        
        // Dispatch event for other components (like Chatbot) to update their system prompts
        window.dispatchEvent(new CustomEvent('languageChanged', { 
          detail: { language: this.currentLanguage } 
        }));
      });
    }
  }

  applyTranslations() {
    const d = window.translations[this.currentLanguage] || window.translations['en'];
    
    // We can translate everything that has a specific data attribute
    // data-i18n="key_name"
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const text = d[key] || window.translations['en'][key] || key;
      
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = text;
      } else {
        el.innerHTML = text; // or textContent depending if we have HTML in translations
      }
    });

    document.documentElement.lang = this.currentLanguage;
  }
}

// Initialize when translations are ready
if (typeof window.translations !== 'undefined') {
  window.languageManager = new LanguageManager();
} else {
  console.error("translations.js must be loaded before language-manager.js");
}
