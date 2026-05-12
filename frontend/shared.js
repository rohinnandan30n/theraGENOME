/**
 * TheraGENOME – Shared Theme + Language Utilities
 * Include this script in every page.
 * Usage: <script src="shared.js"></script>
 */
(function () {
  'use strict';

  /* ── THEME ── */
  function applyTheme(dark) {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    const btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = dark ? '☀️' : '🌙';
    localStorage.setItem('theme', dark ? 'dark' : 'light');
    // chatbot / other pages that use data-theme on body too
    document.body.setAttribute('data-theme', dark ? 'dark' : 'light');
  }

  window.toggleTheme = function () {
    applyTheme(document.documentElement.getAttribute('data-theme') !== 'dark');
  };

  // Apply on load — default is always dark unless user saved 'light'
  applyTheme(localStorage.getItem('theme') !== 'light');

  /* ── LANGUAGE ── */
  const LANGS = {
    en: { label: '🌐 EN', name: 'English' },
    kn: { label: 'ಕನ್ನಡ', name: 'Kannada' },
    hi: { label: 'हिंदी', name: 'Hindi' },
    ta: { label: 'தமிழ்', name: 'Tamil' },
    te: { label: 'తెలుగు', name: 'Telugu' },
    mr: { label: 'मराठी', name: 'Marathi' },
    bn: { label: 'বাংলা', name: 'Bengali' },
    ml: { label: 'മലയാളം', name: 'Malayalam' },
  };

  window.LANG_LABELS = LANGS;

  window.switchLang = function (lang) {
    localStorage.setItem('lang', lang);
    // Each page defines its own applyTranslations(lang) function
    if (typeof window.applyTranslations === 'function') {
      window.applyTranslations(lang);
    }
  };

  // Auto-apply saved language after DOM is ready
  document.addEventListener('DOMContentLoaded', function () {
    const saved = localStorage.getItem('lang') || 'en';
    const sel = document.getElementById('langSelect');
    if (sel) sel.value = saved;
    if (typeof window.applyTranslations === 'function') {
      window.applyTranslations(saved);
    }
  });
})();
