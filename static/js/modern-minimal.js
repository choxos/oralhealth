/**
 * Modern Minimal JavaScript for OralHealth
 * Ultra-fast, vanilla JS implementation with modern ES6+ features
 * No external dependencies - optimized for speed and simplicity
 */

class OralHealthApp {
  constructor() {
    this.currentLanguage = 'en';
    this.cache = new Map();
    this.debounceTimers = new Map();
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.setupTranslation();
    this.setupSearch();
    this.setupIntersectionObserver();
  }

  // Event Listeners
  setupEventListeners() {
    // Debounced resize handler
    window.addEventListener('resize', this.debounce(() => {
      this.handleResize();
    }, 150));

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
          case 'k':
            e.preventDefault();
            this.focusSearch();
            break;
          case '/':
            e.preventDefault();
            this.toggleTranslation();
            break;
        }
      }
    });

    // Click outside handler
    document.addEventListener('click', (e) => {
      this.handleOutsideClick(e);
    });
  }

  // Translation System
  setupTranslation() {
    const widget = this.createTranslationWidget();
    document.body.appendChild(widget);
    
    // Check URL for language parameter
    const urlParams = new URLSearchParams(window.location.search);
    const lang = urlParams.get('lang');
    if (lang && this.isValidLanguage(lang)) {
      this.setLanguage(lang);
    }
  }

  createTranslationWidget() {
    const languages = {
      'en': { name: 'English', flag: '🇬🇧' },
      'es': { name: 'Español', flag: '🇪🇸' },
      'fr': { name: 'Français', flag: '🇫🇷' },
      'de': { name: 'Deutsch', flag: '🇩🇪' },
      'it': { name: 'Italiano', flag: '🇮🇹' },
      'pt': { name: 'Português', flag: '🇵🇹' },
      'zh': { name: '中文', flag: '🇨🇳' },
      'ja': { name: '日本語', flag: '🇯🇵' },
      'ko': { name: '한국어', flag: '🇰🇷' },
      'ar': { name: 'العربية', flag: '🇸🇦' },
      'hi': { name: 'हिन्दी', flag: '🇮🇳' },
      'ru': { name: 'Русский', flag: '🇷🇺' }
    };

    const widget = document.createElement('div');
    widget.className = 'translation-widget';
    widget.innerHTML = `
      <button class="translation-btn" id="translationBtn">
        <span class="current-flag">🇬🇧</span>
        <span class="current-lang">English</span>
        <i class="fas fa-chevron-down"></i>
      </button>
      <div class="translation-dropdown" id="translationDropdown">
        <div class="translation-header">
          <h6>Choose Language</h6>
          <input type="text" placeholder="Search..." class="form-input" id="langSearch">
        </div>
        <div class="translation-languages" id="translationLanguages">
          ${Object.entries(languages).map(([code, lang]) => `
            <div class="language-item" data-lang="${code}">
              <span class="flag">${lang.flag}</span>
              <span class="name">${lang.name}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // Event listeners
    const btn = widget.querySelector('#translationBtn');
    const dropdown = widget.querySelector('#translationDropdown');
    const search = widget.querySelector('#langSearch');
    const languages_el = widget.querySelector('#translationLanguages');

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('show');
    });

    search.addEventListener('input', (e) => {
      this.filterLanguages(e.target.value, languages_el);
    });

    languages_el.addEventListener('click', (e) => {
      const item = e.target.closest('.language-item');
      if (item) {
        const lang = item.dataset.lang;
        this.setLanguage(lang);
        dropdown.classList.remove('show');
      }
    });

    return widget;
  }

  filterLanguages(query, container) {
    const items = container.querySelectorAll('.language-item');
    const searchTerm = query.toLowerCase();

    items.forEach(item => {
      const name = item.querySelector('.name').textContent.toLowerCase();
      item.style.display = name.includes(searchTerm) ? 'flex' : 'none';
    });
  }

  async setLanguage(langCode) {
    if (langCode === this.currentLanguage) return;

    this.currentLanguage = langCode;
    this.updateLanguageUI(langCode);

    if (langCode === 'en') {
      this.restoreOriginalContent();
    } else {
      await this.translatePage(langCode);
    }

    this.updateURL(langCode);
  }

  updateLanguageUI(langCode) {
    const languages = {
      'en': { name: 'English', flag: '🇬🇧' },
      'es': { name: 'Español', flag: '🇪🇸' },
      'fr': { name: 'Français', flag: '🇫🇷' },
      'de': { name: 'Deutsch', flag: '🇩🇪' },
      'it': { name: 'Italiano', flag: '🇮🇹' },
      'pt': { name: 'Português', flag: '🇵🇹' },
      'zh': { name: '中文', flag: '🇨🇳' },
      'ja': { name: '日本語', flag: '🇯🇵' },
      'ko': { name: '한국어', flag: '🇰🇷' },
      'ar': { name: 'العربية', flag: '🇸🇦' },
      'hi': { name: 'हिन्दी', flag: '🇮🇳' },
      'ru': { name: 'Русский', flag: '🇷🇺' }
    };

    const lang = languages[langCode];
    if (lang) {
      document.querySelector('.current-flag').textContent = lang.flag;
      document.querySelector('.current-lang').textContent = lang.name;
    }

    // Update active state
    document.querySelectorAll('.language-item').forEach(item => {
      item.classList.toggle('active', item.dataset.lang === langCode);
    });
  }

  async translatePage(langCode) {
    const elements = this.getTranslatableElements();
    if (elements.length === 0) return;

    // Store original content
    if (!this.cache.has('original')) {
      const original = new Map();
      elements.forEach(el => {
        original.set(el, el.textContent);
      });
      this.cache.set('original', original);
    }

    // Show loading state
    this.showLoadingState();

    try {
      // Translate in batches for better performance
      const batchSize = 5;
      for (let i = 0; i < elements.length; i += batchSize) {
        const batch = elements.slice(i, i + batchSize);
        await this.translateBatch(batch, langCode);
      }
    } catch (error) {
      console.error('Translation failed:', error);
      this.showError('Translation failed. Please try again.');
    } finally {
      this.hideLoadingState();
    }
  }

  getTranslatableElements() {
    const selectors = [
      'h1, h2, h3, h4, h5, h6',
      'p:not([data-no-translate])',
      '.card-title',
      '.stat-label',
      '.btn:not(.translation-btn)',
      '.nav-link'
    ];

    const elements = [];
    selectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(el => {
        const text = el.textContent.trim();
        if (text && text.length > 2 && !el.dataset.translated) {
          elements.push(el);
        }
      });
    });

    return elements;
  }

  async translateBatch(elements, langCode) {
    const promises = elements.map(el => this.translateElement(el, langCode));
    await Promise.allSettled(promises);
  }

  async translateElement(element, langCode) {
    const original = this.cache.get('original')?.get(element) || element.textContent;
    const cacheKey = `${original}:${langCode}`;

    // Check cache
    if (this.cache.has(cacheKey)) {
      element.textContent = this.cache.get(cacheKey);
      element.dataset.translated = 'true';
      return;
    }

    try {
      const response = await this.fetchWithTimeout(
        `/api/translate/?text=${encodeURIComponent(original)}&target=${langCode}`,
        5000
      );
      
      if (!response.ok) throw new Error('Translation API error');
      
      const data = await response.json();
      if (data.translated) {
        this.cache.set(cacheKey, data.translated);
        element.textContent = data.translated;
        element.dataset.translated = 'true';
      }
    } catch (error) {
      console.warn('Translation failed for element:', error);
    }
  }

  restoreOriginalContent() {
    const original = this.cache.get('original');
    if (original) {
      original.forEach((text, element) => {
        element.textContent = text;
        element.dataset.translated = 'false';
      });
    }
  }

  // Search System
  setupSearch() {
    const searchInput = document.querySelector('#searchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', this.debounce((e) => {
      this.performSearch(e.target.value);
    }, 300));

    // Search suggestions
    const suggestions = document.createElement('div');
    suggestions.className = 'search-suggestions hidden';
    searchInput.parentNode.appendChild(suggestions);
  }

  async performSearch(query) {
    if (query.length < 2) {
      this.hideSuggestions();
      return;
    }

    try {
      const response = await this.fetchWithTimeout(`/api/search/?q=${encodeURIComponent(query)}`, 3000);
      const data = await response.json();
      this.showSuggestions(data.results);
    } catch (error) {
      console.warn('Search failed:', error);
    }
  }

  showSuggestions(results) {
    const suggestions = document.querySelector('.search-suggestions');
    if (!suggestions) return;

    if (results.length === 0) {
      this.hideSuggestions();
      return;
    }

    suggestions.innerHTML = results.map(item => `
      <div class="suggestion-item" data-url="${item.url}">
        <div class="suggestion-title">${item.title}</div>
        <div class="suggestion-meta">${item.country}</div>
      </div>
    `).join('');

    suggestions.classList.remove('hidden');

    // Add click handlers
    suggestions.addEventListener('click', (e) => {
      const item = e.target.closest('.suggestion-item');
      if (item) {
        window.location.href = item.dataset.url;
      }
    });
  }

  hideSuggestions() {
    const suggestions = document.querySelector('.search-suggestions');
    if (suggestions) {
      suggestions.classList.add('hidden');
    }
  }

  // Performance Optimizations
  setupIntersectionObserver() {
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      }, { threshold: 0.1 });

      // Observe elements that can be lazily loaded
      document.querySelectorAll('.card, .stat').forEach(el => {
        observer.observe(el);
      });
    }
  }

  // Utility Functions
  debounce(func, wait) {
    return (...args) => {
      const key = func.toString();
      clearTimeout(this.debounceTimers.get(key));
      this.debounceTimers.set(key, setTimeout(() => func.apply(this, args), wait));
    };
  }

  async fetchWithTimeout(url, timeout = 5000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  isValidLanguage(langCode) {
    const supportedLangs = ['en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'ar', 'hi', 'ru'];
    return supportedLangs.includes(langCode);
  }

  updateURL(langCode) {
    const url = new URL(window.location);
    if (langCode === 'en') {
      url.searchParams.delete('lang');
    } else {
      url.searchParams.set('lang', langCode);
    }
    history.replaceState({}, '', url);
  }

  // UI State Management
  showLoadingState() {
    document.body.classList.add('loading');
  }

  hideLoadingState() {
    document.body.classList.remove('loading');
  }

  showError(message) {
    const error = document.createElement('div');
    error.className = 'error-toast';
    error.textContent = message;
    document.body.appendChild(error);
    
    setTimeout(() => error.remove(), 5000);
  }

  focusSearch() {
    const search = document.querySelector('#searchInput');
    if (search) search.focus();
  }

  toggleTranslation() {
    const dropdown = document.querySelector('#translationDropdown');
    if (dropdown) {
      dropdown.classList.toggle('show');
    }
  }

  handleOutsideClick(e) {
    const translation = e.target.closest('.translation-widget');
    if (!translation) {
      document.querySelector('#translationDropdown')?.classList.remove('show');
    }

    const search = e.target.closest('.search-suggestions');
    if (!search) {
      this.hideSuggestions();
    }
  }

  handleResize() {
    // Handle responsive behavior
    const nav = document.querySelector('.nav');
    if (nav && window.innerWidth < 768) {
      nav.classList.add('mobile');
    } else if (nav) {
      nav.classList.remove('mobile');
    }
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new OralHealthApp());
} else {
  new OralHealthApp();
}

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = OralHealthApp;
}