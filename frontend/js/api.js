/**
 * API Communication Layer
 * Handles all HTTP requests to the Ollama API backend
 */

const API_CONFIG = {
    BASE_URL: 'http://localhost:3000',
    ENDPOINTS: {
        // Health
        HEALTH: '/',
        
        // Authentication
        LOGIN: '/api/auth/login',
        REGISTER: '/api/auth/register',
        ME: '/api/auth/me',
        
        // API Keys
        API_KEYS: '/api/auth/api-keys',
        
        // Generation
        GENERATE: '/api/generate',
        CHAT: '/api/chat',
        MODELS: '/api/models',
        
        // Admin
        USERS: '/api/auth/users',
        USAGE_STATS: '/api/auth/usage/stats'
    }
};

class ApiClient {
    constructor() {
        this.baseURL = API_CONFIG.BASE_URL;
        this.token = localStorage.getItem('authToken');
    }

    /**
     * Set authentication token
     */
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('authToken', token);
        } else {
            localStorage.removeItem('authToken');
        }
    }

    /**
     * Get authentication headers
     */
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    /**
     * Make HTTP request with error handling
     */
    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            headers: this.getAuthHeaders(),
            ...options
        };

        try {
            console.log(`Making ${config.method || 'GET'} request to:`, url);
            
            const response = await fetch(url, config);
            
            // Handle different response types
            let data;
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                throw new ApiError(
                    data?.detail || data?.message || 'Request failed',
                    response.status,
                    data
                );
            }

            console.log('API Response:', data);
            return data;
            
        } catch (error) {
            console.error('API Error:', error);
            
            if (error instanceof ApiError) {
                throw error;
            }
            
            // Handle network errors
            throw new ApiError(
                'Network error: Unable to connect to the server',
                0,
                { originalError: error.message }
            );
        }
    }

    // Health Check
    async checkHealth() {
        return this.makeRequest(API_CONFIG.ENDPOINTS.HEALTH);
    }

    // Authentication APIs
    async login(credentials) {
        // Use form data for OAuth2PasswordRequestForm
        const formData = new URLSearchParams();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        return this.makeRequest(API_CONFIG.ENDPOINTS.LOGIN, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });
    }

    async register(userData) {
        return this.makeRequest(API_CONFIG.ENDPOINTS.REGISTER, {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    async getCurrentUser() {
        return this.makeRequest(API_CONFIG.ENDPOINTS.ME);
    }

    // API Key Management
    async getApiKeys() {
        return this.makeRequest(API_CONFIG.ENDPOINTS.API_KEYS);
    }

    async createApiKey(keyData) {
        return this.makeRequest(API_CONFIG.ENDPOINTS.API_KEYS, {
            method: 'POST',
            body: JSON.stringify(keyData)
        });
    }

    async deleteApiKey(keyId) {
        return this.makeRequest(`${API_CONFIG.ENDPOINTS.API_KEYS}/${keyId}`, {
            method: 'DELETE'
        });
    }

    // Text Generation
    async generateText(prompt, options = {}) {
        const payload = {
            prompt: prompt,
            model: options.model || 'llama3:8b',
            temperature: options.temperature || 0.7,
            stream: options.stream || false,
            ...options
        };

        return this.makeRequest(API_CONFIG.ENDPOINTS.GENERATE, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    // Chat
    async sendChatMessage(messages, options = {}) {
        const payload = {
            messages: messages,
            model: options.model || 'llama3:8b',
            temperature: options.temperature || 0.7,
            stream: options.stream || false,
            ...options
        };

        return this.makeRequest(API_CONFIG.ENDPOINTS.CHAT, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    // Models
    async getModels() {
        return this.makeRequest(API_CONFIG.ENDPOINTS.MODELS);
    }

    // Admin APIs
    async getAllUsers() {
        return this.makeRequest(API_CONFIG.ENDPOINTS.USERS);
    }

    async getUsageStats() {
        return this.makeRequest(API_CONFIG.ENDPOINTS.USAGE_STATS);
    }

    async deleteUser(userId) {
        return this.makeRequest(`${API_CONFIG.ENDPOINTS.USERS}/${userId}`, {
            method: 'DELETE'
        });
    }
}

/**
 * Custom API Error class
 */
class ApiError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }

    isNetworkError() {
        return this.status === 0;
    }

    isAuthError() {
        return this.status === 401 || this.status === 403;
    }

    isValidationError() {
        return this.status === 422;
    }

    isNotFound() {
        return this.status === 404;
    }
}

/**
 * Global API client instance
 */
const apiClient = new ApiClient();

/**
 * Utility functions for common API patterns
 */
const ApiUtils = {
    /**
     * Handle API errors with user-friendly messages
     */
    handleError(error, fallbackMessage = 'An unexpected error occurred') {
        console.error('Handling API error:', error);
        
        if (error instanceof ApiError) {
            if (error.isNetworkError()) {
                return 'Unable to connect to the server. Please check your connection.';
            }
            
            if (error.isAuthError()) {
                return 'Authentication failed. Please log in again.';
            }
            
            if (error.isValidationError()) {
                return error.message || 'Please check your input and try again.';
            }
            
            if (error.isNotFound()) {
                return 'The requested resource was not found.';
            }
            
            return error.message || fallbackMessage;
        }
        
        return error.message || fallbackMessage;
    },

    /**
     * Format API response data for display
     */
    formatResponse(data) {
        if (typeof data === 'object') {
            return JSON.stringify(data, null, 2);
        }
        return String(data);
    },

    /**
     * Extract error message from various error formats
     */
    extractErrorMessage(error) {
        if (error?.detail) return error.detail;
        if (error?.message) return error.message;
        if (error?.error) return error.error;
        if (typeof error === 'string') return error;
        return 'Unknown error occurred';
    }
};

// Export for global use
window.apiClient = apiClient;
window.ApiError = ApiError;
window.ApiUtils = ApiUtils;