/**
 * Dark Theme Toggle for OralHealth
 */

class ThemeManager {
    constructor() {
        this.init();
    }

    init() {
        // Check for saved theme preference or default to 'light'
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
        
        // Create and add theme toggle button
        this.createToggleButton();
        
        // Listen for system theme changes
        this.listenForSystemThemeChanges();
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update meta theme-color for mobile browsers
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', theme === 'dark' ? '#1a1a1a' : '#ffffff');
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
        
        // Track theme change for analytics
        if (window.trackThemeChange) {
            window.trackThemeChange(newTheme);
        }
        
        // Smooth transition animation
        document.body.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    createToggleButton() {
        const toggleButton = document.createElement('button');
        toggleButton.className = 'theme-toggle';
        toggleButton.id = 'themeToggle';
        toggleButton.setAttribute('aria-label', 'Toggle theme');
        toggleButton.innerHTML = `
            <i class="fas fa-sun sun-icon"></i>
            <i class="fas fa-moon moon-icon"></i>
        `;
        
        toggleButton.addEventListener('click', () => this.toggleTheme());
        document.body.appendChild(toggleButton);
    }

    listenForSystemThemeChanges() {
        // Respect system theme preference if no manual preference is set
        if (!localStorage.getItem('theme')) {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
            this.setTheme(prefersDark.matches ? 'dark' : 'light');
            
            prefersDark.addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) {
                    this.setTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager();
});

// Expose for external use
window.ThemeManager = ThemeManager;