/**
 * Progressive Web App (PWA) functionality for OralHealth
 */

class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.init();
    }

    init() {
        // Register service worker
        this.registerServiceWorker();
        
        // Handle install prompt
        this.handleInstallPrompt();
        
        // Add install button
        this.createInstallButton();
        
        // Handle app updates
        this.handleAppUpdates();
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/sw.js');
                console.log('Service Worker registered successfully:', registration);
                
                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();
                        }
                    });
                });
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    handleInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            // Prevent the mini-infobar from appearing on mobile
            e.preventDefault();
            
            // Store the event so it can be triggered later
            this.deferredPrompt = e;
            
            // Show install button
            this.showInstallButton();
        });

        // Handle successful installation
        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed');
            this.hideInstallButton();
            this.deferredPrompt = null;
        });
    }

    createInstallButton() {
        const installButton = document.createElement('button');
        installButton.id = 'install-button';
        installButton.className = 'btn btn-primary install-btn';
        installButton.innerHTML = '📱 Install App';
        installButton.style.display = 'none';
        installButton.style.position = 'fixed';
        installButton.style.bottom = '20px';
        installButton.style.right = '20px';
        installButton.style.zIndex = '1000';
        installButton.style.borderRadius = '25px';
        installButton.style.padding = '10px 20px';
        installButton.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        
        installButton.addEventListener('click', () => this.installApp());
        document.body.appendChild(installButton);
    }

    showInstallButton() {
        const installButton = document.getElementById('install-button');
        if (installButton) {
            installButton.style.display = 'block';
            installButton.style.animation = 'slideInUp 0.3s ease-out';
        }
    }

    hideInstallButton() {
        const installButton = document.getElementById('install-button');
        if (installButton) {
            installButton.style.display = 'none';
        }
    }

    async installApp() {
        if (!this.deferredPrompt) return;

        // Show the install prompt
        this.deferredPrompt.prompt();
        
        // Wait for the user to respond to the prompt
        const { outcome } = await this.deferredPrompt.userChoice;
        console.log(`User response to the install prompt: ${outcome}`);
        
        // Clear the deferredPrompt
        this.deferredPrompt = null;
        this.hideInstallButton();
    }

    showUpdateNotification() {
        // Create update notification
        const notification = document.createElement('div');
        notification.className = 'update-notification';
        notification.innerHTML = `
            <div class="alert alert-info alert-dismissible fade show" role="alert">
                <strong>App Update Available!</strong> 
                A new version of OralHealth is ready. 
                <button type="button" class="btn btn-sm btn-outline-primary ms-2" onclick="window.location.reload()">
                    Update Now
                </button>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.left = '50%';
        notification.style.transform = 'translateX(-50%)';
        notification.style.zIndex = '1050';
        notification.style.width = '90%';
        notification.style.maxWidth = '500px';
        
        document.body.appendChild(notification);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 10000);
    }

    handleAppUpdates() {
        // Listen for messages from service worker
        navigator.serviceWorker.addEventListener('message', (event) => {
            if (event.data && event.data.type === 'UPDATE_AVAILABLE') {
                this.showUpdateNotification();
            }
        });
    }

    // Check if app is in standalone mode (installed)
    isStandalone() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone ||
               document.referrer.includes('android-app://');
    }

    // Add app shortcuts for better navigation
    addAppShortcuts() {
        if (this.isStandalone()) {
            // Add keyboard shortcuts for standalone app
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey || e.metaKey) {
                    switch (e.key) {
                        case 'k':
                            e.preventDefault();
                            // Focus search input
                            const searchInput = document.querySelector('input[type="search"]');
                            if (searchInput) searchInput.focus();
                            break;
                        case 'h':
                            e.preventDefault();
                            window.location.href = '/';
                            break;
                    }
                }
            });
        }
    }
}

// Initialize PWA manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const pwaManager = new PWAManager();
    pwaManager.addAppShortcuts();
});

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(50px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .install-btn {
        transition: all 0.3s ease;
    }
    
    .install-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2) !important;
    }
    
    @media (max-width: 768px) {
        .install-btn {
            bottom: 10px !important;
            right: 10px !important;
            padding: 8px 16px !important;
            font-size: 0.9rem !important;
        }
    }
`;
document.head.appendChild(style);