/**
 * Main Application Script
 * Initializes the application and handles global functionality
 */

/**
 * Application state
 */
const AppState = {
    isLoading: false,
    apiStatus: 'checking',
    initialized: false,
    currentTab: 'overview',
    healthCheckErrorShown: false
};

/**
 * Initialize the application - FIXED VERSION
 */
async function initializeApp() {
    try {
        console.log('🚀 Initializing Ollama API Dashboard...');
        
        // Show loading overlay
        showLoading('Initializing application...');
        
        // Check API health first
        await checkApiHealth();
        
        // Set up event listeners
        setupEventListeners();
        
        // IMPORTANT: Wait a bit to ensure DOM is fully ready
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Initialize authentication state - FIXED
        if (authManager.token && !authManager.isInitializing) {
            console.log('Found stored token, attempting to restore session...');
            // Don't await this to prevent blocking
            authManager.initializeFromToken().catch(error => {
                console.log('Session restoration failed:', error.message);
                authManager.showAuth();
            });
        } else {
            console.log('No stored token found, showing authentication form');
            authManager.showAuth();
        }
        
        // Mark as initialized
        AppState.initialized = true;
        console.log('✅ Application initialized successfully');
        
    } catch (error) {
        console.error('❌ Failed to initialize application:', error);
        showMessage('Failed to initialize application. Please refresh the page.', 'error');
        // Show auth form as fallback
        authManager.showAuth();
    } finally {
        hideLoading();
    }
}

/**
 * Check API health and update status indicators
 */
async function checkApiHealth() {
    const statusDot = document.getElementById('apiStatus');
    const statusText = document.getElementById('apiStatusText');
    
    try {
        const health = await apiClient.checkHealth();
        
        // Update status indicators
        if (statusDot) {
            statusDot.className = 'status-dot online';
        }
        
        if (statusText) {
            statusText.textContent = `API Online - ${health.version || 'Unknown version'}`;
        }
        
        AppState.apiStatus = 'online';
        console.log('✅ API is healthy:', health);
        
    } catch (error) {
        // Update status indicators for offline state
        if (statusDot) {
            statusDot.className = 'status-dot offline';
        }
        
        if (statusText) {
            statusText.textContent = 'API Offline';
        }
        
        AppState.apiStatus = 'offline';
        console.error('❌ API health check failed:', error);
        
        // Show user-friendly error message only once
        if (!AppState.healthCheckErrorShown) {
            showMessage('Unable to connect to the API. Please check if the server is running.', 'warning');
            AppState.healthCheckErrorShown = true;
        }
    }
}

/**
 * Set up global event listeners
 */
function setupEventListeners() {
    // Handle modal clicks (click outside to close)
    document.addEventListener('click', (event) => {
        const modal = document.getElementById('createKeyModal');
        if (modal && event.target === modal) {
            hideCreateKeyModal();
        }
    });
    
    // Handle escape key for modals
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const modal = document.getElementById('createKeyModal');
            if (modal && modal.style.display === 'flex') {
                hideCreateKeyModal();
            }
        }
        
        // Ctrl+Enter in chat to send message
        if (event.ctrlKey && event.key === 'Enter') {
            const chatMessage = document.getElementById('chatMessage');
            if (document.activeElement === chatMessage) {
                event.preventDefault();
                const chatBtn = document.getElementById('chatBtn');
                if (chatBtn && !chatBtn.disabled) {
                    handleChatMessage(event);
                }
            }
        }
        
        // Enter in login form
        if (event.key === 'Enter') {
            const activeElement = document.activeElement;
            if (activeElement && (activeElement.id === 'loginUsername' || activeElement.id === 'loginPassword')) {
                const loginBtn = document.getElementById('loginBtn');
                if (loginBtn && !loginBtn.disabled) {
                    handleLogin(event);
                }
            }
        }
    });
    
    // Auto-resize chat textarea
    const chatMessage = document.getElementById('chatMessage');
    if (chatMessage) {
        chatMessage.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Handle Enter key in chat (without Ctrl = send message)
        chatMessage.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.ctrlKey && !event.shiftKey) {
                event.preventDefault();
                const chatBtn = document.getElementById('chatBtn');
                if (chatBtn && !chatBtn.disabled && this.value.trim()) {
                    handleChatMessage(event);
                }
            }
        });
    }
    
    // Handle window resize for responsive behavior
    window.addEventListener('resize', debounce(() => {
        console.log('Window resized');
    }, 250));
    
    // Handle online/offline status
    window.addEventListener('online', () => {
        showMessage('Connection restored', 'success');
        checkApiHealth();
    });
    
    window.addEventListener('offline', () => {
        showMessage('Connection lost', 'warning');
    });
    
    console.log('✅ Event listeners set up');
}

/**
 * Loading overlay functions
 */
function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        const loadingText = overlay.querySelector('p');
        if (loadingText) {
            loadingText.textContent = message;
        }
        overlay.style.display = 'flex';
    }
    AppState.isLoading = true;
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
    AppState.isLoading = false;
}

/**
 * Message/Toast system
 */
function showMessage(message, type = 'info', duration = 5000) {
    const messageContainer = document.getElementById('messageContainer');
    if (!messageContainer) {
        console.log(`${type.toUpperCase()}: ${message}`);
        return;
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Handle HTML content safely
    if (message.includes('<')) {
        toast.innerHTML = message;
    } else {
        toast.textContent = message;
    }
    
    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText = `
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        margin-left: auto;
        padding: 0 0 0 10px;
        color: inherit;
        opacity: 0.7;
    `;
    closeBtn.addEventListener('click', () => removeToast(toast));
    
    toast.appendChild(closeBtn);
    
    // Add to container
    messageContainer.appendChild(toast);
    
    // Auto-remove after duration (except for errors)
    if (type !== 'error') {
        setTimeout(() => removeToast(toast), duration);
    }
    
    // Click toast to dismiss
    toast.addEventListener('click', (e) => {
        if (e.target !== closeBtn) {
            removeToast(toast);
        }
    });
}

function removeToast(toast) {
    if (toast.parentNode) {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

/**
 * Utility function for debouncing
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Error handling for unhandled promise rejections
 */
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Don't show messages for certain expected errors
    if (event.reason instanceof ApiError && event.reason.isAuthError()) {
        console.log('Auth error - likely handled elsewhere');
        return;
    }
    
    // Prevent default browser behavior
    event.preventDefault();
    
    showMessage('An unexpected error occurred. Please try again.', 'error');
});

/**
 * Global error handler
 */
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

/**
 * Periodic API health checks
 */
let healthCheckInterval;

function startHealthCheckInterval() {
    // Clear any existing interval
    if (healthCheckInterval) {
        clearInterval(healthCheckInterval);
    }
    
    // Check API health every 30 seconds
    healthCheckInterval = setInterval(async () => {
        if (!AppState.isLoading && document.visibilityState === 'visible') {
            await checkApiHealth();
        }
    }, 30000);
    
    console.log('✅ Health check interval started');
}

function stopHealthCheckInterval() {
    if (healthCheckInterval) {
        clearInterval(healthCheckInterval);
        healthCheckInterval = null;
        console.log('⏹️ Health check interval stopped');
    }
}

/**
 * Handle page visibility changes
 */
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && AppState.initialized) {
        console.log('Page became visible, refreshing status');
        checkApiHealth();
        AppState.healthCheckErrorShown = false;
    }
});

/**
 * Data refresh functions
 */
async function refreshAllData() {
    if (!authManager.isLoggedIn()) return;
    
    try {
        showLoading('Refreshing data...');
        
        // Refresh based on current tab
        switch (AppState.currentTab) {
            case 'overview':
                await authManager.loadUserStats();
                break;
            case 'apikeys':
                await loadApiKeys();
                break;
            case 'models':
                await loadModels();
                break;
            case 'admin':
                if (authManager.isAdmin()) {
                    await loadAllUsers();
                    await loadSystemStats();
                }
                break;
        }
        
        showMessage('Data refreshed successfully', 'success');
        
    } catch (error) {
        console.error('Error refreshing data:', error);
        showMessage('Failed to refresh data', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Local storage management
 */
function clearAppData() {
    try {
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        sessionStorage.clear();
        
        AppState.initialized = false;
        AppState.currentTab = 'overview';
        
        console.log('✅ App data cleared');
        showMessage('Application data cleared', 'info');
        
        setTimeout(() => window.location.reload(), 1000);
        
    } catch (error) {
        console.error('Error clearing app data:', error);
        showMessage('Failed to clear app data', 'error');
    }
}

/**
 * Add required CSS animations
 */
function addRequiredStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        .loading-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: currentColor;
            animation: spin 1s ease-in-out infinite;
            margin-right: 8px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .toast {
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.3s ease;
        }
        
        .toast:hover {
            opacity: 0.9;
            transform: translateX(-5px);
        }
        
        .loading-overlay {
            backdrop-filter: blur(5px);
        }
        
        @media (max-width: 768px) {
            .toast {
                margin: 0 10px;
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Initialize app when DOM is ready
 */
function startApp() {
    console.log('📱 Starting Ollama API Dashboard...');
    
    addRequiredStyles();
    
    initializeApp().then(() => {
        startHealthCheckInterval();
        console.log('🎉 Ollama API Dashboard started successfully!');
    }).catch((error) => {
        console.error('💥 Failed to start application:', error);
        showMessage('Failed to start application. Please refresh the page.', 'error');
    });
}

/**
 * DOM ready check and initialization
 */
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startApp);
} else {
    startApp();
}

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', () => {
    stopHealthCheckInterval();
    console.log('👋 Application cleanup completed');
});

/**
 * Utility functions for debugging
 */
window.DebugUtils = {
    getAppState: () => ({ ...AppState }),
    getAuthState: () => ({
        isAuthenticated: authManager.isAuthenticated,
        currentUser: authManager.currentUser,
        hasToken: !!authManager.token,
        tokenPreview: authManager.token ? authManager.token.substring(0, 20) + '...' : null
    }),
    clearStorage: clearAppData,
    forceReload: () => window.location.reload(),
    refreshData: refreshAllData,
    testApi: async () => {
        try {
            const health = await apiClient.checkHealth();
            console.log('API Test Result:', health);
            return health;
        } catch (error) {
            console.error('API Test Failed:', error);
            throw error;
        }
    }
};

/**
 * Export globals for debugging and external access
 */
window.AppState = AppState;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showMessage = showMessage;
window.checkApiHealth = checkApiHealth;
window.refreshAllData = refreshAllData;
window.clearAppData = clearAppData;

console.log('📱 Main application script loaded and ready');