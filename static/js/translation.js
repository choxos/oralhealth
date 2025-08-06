/**
 * Translation functionality for OralHealth
 * Provides real-time translation of content using multiple APIs
 */

class OralHealthTranslator {
    constructor() {
        this.currentLanguage = 'en';
        this.originalContent = new Map();
        this.translationCache = new Map();
        this.isTranslating = false;
        this.init();
    }
    
    init() {
        this.createTranslationWidget();
        this.bindEvents();
        
        // Check if language is set in URL
        const urlParams = new URLSearchParams(window.location.search);
        const lang = urlParams.get('lang');
        if (lang && lang !== 'en') {
            this.translatePage(lang);
        }
    }
    
    createTranslationWidget() {
        const widget = document.createElement('div');
        widget.className = 'oralhealth-translation-widget';
        widget.innerHTML = `
            <div class="translation-toggle">
                <button class="xera-btn xera-btn-outline translation-btn" id="translationToggle">
                    <i class="fas fa-globe me-1"></i>
                    <span class="current-lang">English</span>
                    <i class="fas fa-chevron-down ms-1"></i>
                </button>
                <div class="translation-dropdown" id="translationDropdown">
                    <div class="translation-header">
                        <h6><i class="fas fa-language me-2"></i>Choose Language</h6>
                    </div>
                    <div class="translation-search">
                        <input type="text" placeholder="Search languages..." id="languageSearch" class="xera-input">
                    </div>
                    <div class="translation-languages" id="translationLanguages">
                        <!-- Languages will be populated here -->
                    </div>
                    <div class="translation-footer">
                        <small class="text-muted">
                            <i class="fas fa-info-circle me-1"></i>
                            Powered by LibreTranslate & Google Translate
                        </small>
                    </div>
                </div>
            </div>
        `;
        
        // Add to top-right of page
        document.body.appendChild(widget);
        
        // Populate languages
        this.populateLanguages();
    }
    
    populateLanguages() {
        const languagesContainer = document.getElementById('translationLanguages');
        const supportedLanguages = window.supportedLanguages || {};
        
        const languagesList = Object.entries(supportedLanguages).map(([code, info]) => {
            return `
                <div class="translation-language-item ${code === this.currentLanguage ? 'active' : ''}" 
                     data-lang="${code}">
                    <span class="flag">${info.flag}</span>
                    <span class="name">${info.name}</span>
                    ${code === this.currentLanguage ? '<i class="fas fa-check ms-auto"></i>' : ''}
                </div>
            `;
        }).join('');
        
        languagesContainer.innerHTML = languagesList;
    }
    
    bindEvents() {
        // Toggle dropdown
        document.getElementById('translationToggle').addEventListener('click', (e) => {
            e.stopPropagation();
            const dropdown = document.getElementById('translationDropdown');
            dropdown.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            document.getElementById('translationDropdown').classList.remove('show');
        });
        
        // Language search
        document.getElementById('languageSearch').addEventListener('input', (e) => {
            this.filterLanguages(e.target.value);
        });
        
        // Language selection
        document.getElementById('translationLanguages').addEventListener('click', (e) => {
            const languageItem = e.target.closest('.translation-language-item');
            if (languageItem) {
                const langCode = languageItem.dataset.lang;
                this.selectLanguage(langCode);
            }
        });
        
        // Prevent dropdown close on internal clicks
        document.getElementById('translationDropdown').addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    filterLanguages(searchTerm) {
        const items = document.querySelectorAll('.translation-language-item');
        const term = searchTerm.toLowerCase();
        
        items.forEach(item => {
            const name = item.querySelector('.name').textContent.toLowerCase();
            if (name.includes(term)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    selectLanguage(langCode) {
        if (langCode === this.currentLanguage) return;
        
        const supportedLanguages = window.supportedLanguages || {};
        const languageInfo = supportedLanguages[langCode];
        
        if (!languageInfo) {
            console.error('Unsupported language:', langCode);
            return;
        }
        
        // Update current language
        this.currentLanguage = langCode;
        
        // Update button text
        document.querySelector('.current-lang').textContent = languageInfo.name;
        
        // Update active state
        document.querySelectorAll('.translation-language-item').forEach(item => {
            item.classList.remove('active');
            item.querySelector('.fas')?.remove();
        });
        
        const activeItem = document.querySelector(`[data-lang="${langCode}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
            activeItem.innerHTML += '<i class="fas fa-check ms-auto"></i>';
        }
        
        // Close dropdown
        document.getElementById('translationDropdown').classList.remove('show');
        
        // Translate page
        if (langCode === 'en') {
            this.restoreOriginalContent();
            this.updateURL('en');
        } else {
            this.translatePage(langCode);
        }
    }
    
    async translatePage(targetLang) {
        if (this.isTranslating) return;
        
        this.isTranslating = true;
        this.showTranslationProgress();
        
        try {
            // Store original content if not already stored
            if (this.originalContent.size === 0) {
                this.storeOriginalContent();
            }
            
            // Get translatable elements
            const elements = this.getTranslatableElements();
            
            // Translate in batches to avoid overwhelming the API
            const batchSize = 5;
            for (let i = 0; i < elements.length; i += batchSize) {
                const batch = elements.slice(i, i + batchSize);
                await this.translateBatch(batch, targetLang);
            }
            
            // Update URL
            this.updateURL(targetLang);
            
        } catch (error) {
            console.error('Translation error:', error);
            this.showTranslationError();
        } finally {
            this.isTranslating = false;
            this.hideTranslationProgress();
        }
    }
    
    storeOriginalContent() {
        const elements = this.getTranslatableElements();
        elements.forEach(element => {
            this.originalContent.set(element, element.textContent);
        });
    }
    
    getTranslatableElements() {
        const selectors = [
            '.oralhealth-recommendation-title',
            '.oralhealth-recommendation-text',
            '.xera-card-title',
            '.xera-stat-label',
            'h1, h2, h3, h4, h5, h6',
            'p',
            '.xera-btn:not(.translation-btn)',
            '.breadcrumb-item',
            '.xera-nav-link'
        ];
        
        const elements = [];
        selectors.forEach(selector => {
            const found = document.querySelectorAll(selector);
            found.forEach(el => {
                // Skip if already processed or empty
                if (el.dataset.translated || !el.textContent.trim()) return;
                
                // Skip if contains only icons or numbers
                const text = el.textContent.trim();
                if (/^[\d\s\-+.,]+$/.test(text) || text.length < 3) return;
                
                elements.push(el);
            });
        });
        
        return elements;
    }
    
    async translateBatch(elements, targetLang) {
        const promises = elements.map(element => this.translateElement(element, targetLang));
        await Promise.all(promises);
    }
    
    async translateElement(element, targetLang) {
        const originalText = this.originalContent.get(element) || element.textContent;
        
        // Check cache first
        const cacheKey = `${originalText}:${targetLang}`;
        if (this.translationCache.has(cacheKey)) {
            element.textContent = this.translationCache.get(cacheKey);
            element.dataset.translated = 'true';
            return;
        }
        
        try {
            const response = await fetch(`/api/translate/?text=${encodeURIComponent(originalText)}&target=${targetLang}&source=en`);
            const data = await response.json();
            
            if (data.translated) {
                // Cache the translation
                this.translationCache.set(cacheKey, data.translated);
                
                // Update element
                element.textContent = data.translated;
                element.dataset.translated = 'true';
                
                // Add translation animation
                element.style.transition = 'opacity 0.3s ease';
                element.style.opacity = '0.7';
                setTimeout(() => {
                    element.style.opacity = '1';
                }, 300);
            }
        } catch (error) {
            console.error('Translation error for element:', error);
        }
    }
    
    restoreOriginalContent() {
        this.originalContent.forEach((originalText, element) => {
            element.textContent = originalText;
            element.dataset.translated = 'false';
        });
    }
    
    updateURL(langCode) {
        const url = new URL(window.location);
        if (langCode === 'en') {
            url.searchParams.delete('lang');
        } else {
            url.searchParams.set('lang', langCode);
        }
        
        // Update URL without page reload
        window.history.replaceState({}, '', url);
    }
    
    showTranslationProgress() {
        // Create progress indicator
        if (!document.getElementById('translationProgress')) {
            const progress = document.createElement('div');
            progress.id = 'translationProgress';
            progress.className = 'translation-progress';
            progress.innerHTML = `
                <div class="progress-content">
                    <i class="fas fa-spinner fa-spin me-2"></i>
                    Translating content...
                </div>
            `;
            document.body.appendChild(progress);
        }
    }
    
    hideTranslationProgress() {
        const progress = document.getElementById('translationProgress');
        if (progress) {
            progress.remove();
        }
    }
    
    showTranslationError() {
        // Show error toast
        const errorToast = document.createElement('div');
        errorToast.className = 'translation-error-toast';
        errorToast.innerHTML = `
            <div class="xera-alert xera-alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Translation failed. Please try again later.
            </div>
        `;
        
        document.body.appendChild(errorToast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            errorToast.remove();
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if translation should be enabled
    try {
        if (window.supportedLanguages && Object.keys(window.supportedLanguages).length > 1) {
            console.log('Initializing OralHealth Translator...');
            new OralHealthTranslator();
        } else {
            console.log('Translation disabled: supportedLanguages not found or insufficient languages');
            console.log('supportedLanguages:', window.supportedLanguages);
        }
    } catch (error) {
        console.error('Error initializing translator:', error);
    }
});