/**
 * Authentication Functions - FIXED VERSION
 * Handles user login, registration, and authentication state
 */

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.isAuthenticated = false;
        this.token = localStorage.getItem('authToken');
        this.isInitializing = false; // Prevent race conditions
        
        console.log('🔧 AuthManager initialized');
        console.log('Token from storage:', this.token ? 'Present' : 'None');
    }

    /**
     * Initialize user session from stored token - FIXED
     */
    async initializeFromToken() {
        if (this.isInitializing) {
            console.log('⏳ Already initializing, skipping...');
            return;
        }
        
        if (!this.token) {
            console.log('❌ No token to initialize from');
            this.showAuth();
            return;
        }
        
        try {
            this.isInitializing = true;
            console.log('🔄 Initializing from stored token...');
            
            apiClient.setToken(this.token);
            
            const response = await fetch('http://localhost:3000/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                },
            });
            
            if (response.ok) {
                const user = await response.json();
                console.log('✅ Token valid, user restored:', user.username);
                
                this.setCurrentUser(user);
                this.showDashboard();
            } else {
                console.log('❌ Token invalid, clearing session');
                this.logout();
            }
        } catch (error) {
            console.error('❌ Token initialization failed:', error);
            this.logout();
        } finally {
            this.isInitializing = false;
        }
    }

    /**
     * Handle user login - FIXED VERSION
     */
    async login(credentials) {
        try {
            console.log('🔐 Login attempt for:', credentials.username);
            
            // Create form data for OAuth2PasswordRequestForm
            const formData = new URLSearchParams();
            formData.append('username', credentials.username);
            formData.append('password', credentials.password);

            const response = await fetch('http://localhost:3000/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData,
            });
            
            console.log('📡 Login response status:', response.status);
            
            const data = await response.json();
            
            if (response.ok && data.access_token) {
                console.log('✅ Login successful!');
                
                // Store token
                this.token = data.access_token;
                localStorage.setItem('authToken', this.token);
                apiClient.setToken(this.token);
                
                console.log('💾 Token stored');
                
                // Get user info
                const userResponse = await fetch('http://localhost:3000/api/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                    },
                });
                
                if (userResponse.ok) {
                    const user = await userResponse.json();
                    console.log('👤 User info received:', user.username);
                    
                    this.setCurrentUser(user);
                    this.showDashboard();
                    
                    return { success: true, user };
                } else {
                    throw new Error('Failed to get user info');
                }
            } else {
                throw new Error(data.detail || 'Login failed');
            }
            
        } catch (error) {
            console.error('❌ Login error:', error);
            const message = ApiUtils?.handleError(error, 'Login failed') || error.message;
            showMessage(message, 'error');
            return { success: false, error: message };
        }
    }

    /**
     * Handle user registration
     */
    async register(userData) {
        try {
            showLoading('Creating account...');
            
            const response = await fetch('http://localhost:3000/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showMessage('Registration successful! You can now log in.', 'success');
                switchAuthTab('login');
                return { success: true, user: data };
            } else {
                throw new Error(data.detail || 'Registration failed');
            }
            
        } catch (error) {
            const message = ApiUtils?.handleError(error, 'Registration failed') || error.message;
            showMessage(message, 'error');
            return { success: false, error: message };
        } finally {
            hideLoading();
        }
    }

    /**
     * Handle user logout
     */
    logout() {
        console.log('🚪 Logging out...');
        
        // Clear all data
        this.currentUser = null;
        this.isAuthenticated = false;
        this.token = null;
        this.isInitializing = false;
        
        // Clear storage
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        
        // Clear API client token
        apiClient.setToken(null);
        
        // Update UI
        this.showAuth();
        showMessage('Logged out successfully', 'info');
    }

    /**
     * Set current user and update UI - FIXED
     */
    setCurrentUser(user) {
        this.currentUser = user;
        this.isAuthenticated = true;
        
        // Store user data
        localStorage.setItem('currentUser', JSON.stringify(user));
        
        // Update UI elements
        this.updateUserDisplay();
        
        console.log('✅ Current user set:', user.username, user.role);
    }

    /**
     * Update user display in header
     */
    updateUserDisplay() {
        const userInfo = document.getElementById('userInfo');
        const userName = document.getElementById('userName');
        
        if (this.currentUser && userInfo && userName) {
            userName.textContent = `${this.currentUser.username} (${this.currentUser.role})`;
            userInfo.style.display = 'flex';
            console.log('✅ User display updated');
        }
    }

    /**
     * Show authentication section - FIXED
     */
    showAuth() {
        console.log('🔄 Showing auth section');
        
        const authSection = document.getElementById('authSection');
        const dashboardSection = document.getElementById('dashboardSection');
        const userInfo = document.getElementById('userInfo');
        
        if (authSection) {
            authSection.style.display = 'flex';
            console.log('✅ Auth section visible');
        }
        
        if (dashboardSection) {
            dashboardSection.style.display = 'none';
            console.log('✅ Dashboard section hidden');
        }
        
        if (userInfo) {
            userInfo.style.display = 'none';
        }
    }

    /**
     * Show dashboard section - FIXED
     */
    showDashboard() {
        console.log('🔄 Showing dashboard section');
        
        const authSection = document.getElementById('authSection');
        const dashboardSection = document.getElementById('dashboardSection');
        
        if (authSection) {
            authSection.style.display = 'none';
            console.log('✅ Auth section hidden');
        }
        
        if (dashboardSection) {
            dashboardSection.style.display = 'block';
            console.log('✅ Dashboard section visible');
        }
        
        // Show admin tab if user is admin
        const adminTabBtn = document.querySelector('[onclick="switchDashboardTab(\'admin\')"]');
        if (adminTabBtn && this.currentUser?.role === 'admin') {
            adminTabBtn.style.display = 'block';
            console.log('✅ Admin tab shown');
        }
        
        // Load initial dashboard data
        this.loadDashboardData();
    }

    /**
     * Load initial dashboard data
     */
    async loadDashboardData() {
        try {
            console.log('📊 Loading dashboard data...');
            // Only load basic stats to prevent errors
            await this.loadUserStats();
        } catch (error) {
            console.log('⚠️ Dashboard data loading failed (non-critical):', error.message);
        }
    }

    /**
     * Load user statistics
     */
    async loadUserStats() {
        try {
            // Update account info
            const statsUsername = document.getElementById('statsUsername');
            const statsRole = document.getElementById('statsRole');
            const statsEmail = document.getElementById('statsEmail');
            const statsMemberSince = document.getElementById('statsMemberSince');
            
            if (this.currentUser) {
                if (statsUsername) statsUsername.textContent = this.currentUser.username;
                if (statsRole) statsRole.textContent = this.currentUser.role;
                if (statsEmail) statsEmail.textContent = this.currentUser.email;
                if (statsMemberSince) {
                    const date = new Date(this.currentUser.created_at);
                    statsMemberSince.textContent = date.toLocaleDateString();
                }
                console.log('✅ User stats loaded');
            }
        } catch (error) {
            console.log('⚠️ Error loading user stats:', error.message);
        }
    }

    /**
     * Check if user has required role
     */
    hasRole(requiredRole) {
        if (!this.currentUser) return false;
        
        const roles = ['user', 'developer', 'admin'];
        const userRoleIndex = roles.indexOf(this.currentUser.role);
        const requiredRoleIndex = roles.indexOf(requiredRole);
        
        return userRoleIndex >= requiredRoleIndex;
    }

    /**
     * Check if user is admin
     */
    isAdmin() {
        return this.currentUser?.role === 'admin';
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Check if authenticated
     */
    isLoggedIn() {
        return this.isAuthenticated && this.currentUser;
    }
}

/**
 * Global authentication manager instance
 */
const authManager = new AuthManager();

/**
 * Handle login form submission - FIXED
 */
async function handleLogin(event) {
    event.preventDefault();
    
    console.log('📝 Login form submitted');
    
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showMessage('Please enter both username and password', 'error');
        return;
    }
    
    const loginBtn = document.getElementById('loginBtn');
    const originalText = loginBtn.textContent;
    
    try {
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span class="loading-spinner"></span> Logging in...';
        
        const result = await authManager.login({ username, password });
        
        if (result.success) {
            console.log('🎉 Login form handler completed successfully');
            // Clear form
            document.getElementById('loginUsername').value = '';
            document.getElementById('loginPassword').value = '';
            showMessage('Welcome back!', 'success');
        }
        
    } catch (error) {
        console.error('❌ Login form error:', error);
        showMessage('Login failed. Please try again.', 'error');
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = originalText;
    }
}

/**
 * Handle registration form submission
 */
async function handleRegister(event) {
    event.preventDefault();
    
    const userData = {
        username: document.getElementById('regUsername').value.trim(),
        email: document.getElementById('regEmail').value.trim(),
        password: document.getElementById('regPassword').value,
        full_name: document.getElementById('regFullName').value.trim(),
        role: document.getElementById('regRole').value
    };
    
    // Basic validation
    if (!userData.username || !userData.email || !userData.password || !userData.full_name) {
        showMessage('Please fill in all required fields', 'error');
        return;
    }
    
    if (userData.password.length < 8) {
        showMessage('Password must be at least 8 characters long', 'error');
        return;
    }
    
    const registerBtn = document.getElementById('registerBtn');
    const originalText = registerBtn.textContent;
    
    try {
        registerBtn.disabled = true;
        registerBtn.innerHTML = '<span class="loading-spinner"></span> Creating Account...';
        
        const result = await authManager.register(userData);
        
        if (result.success) {
            // Clear form
            document.getElementById('regUsername').value = '';
            document.getElementById('regEmail').value = '';
            document.getElementById('regPassword').value = '';
            document.getElementById('regFullName').value = '';
            document.getElementById('regRole').value = 'user';
        }
        
    } catch (error) {
        console.error('❌ Registration error:', error);
        showMessage('Registration failed. Please try again.', 'error');
    } finally {
        registerBtn.disabled = false;
        registerBtn.textContent = originalText;
    }
}

/**
 * Handle logout
 */
function logout() {
    authManager.logout();
}

/**
 * Switch between login and register tabs
 */
function switchAuthTab(tab) {
    console.log('🔄 Switching to auth tab:', tab);
    
    // Remove active class from all tabs and forms
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(form => form.classList.remove('active'));
    
    // Add active class to selected tab and form
    const tabBtn = event?.target || document.querySelector(`[onclick="switchAuthTab('${tab}')"]`);
    if (tabBtn) {
        tabBtn.classList.add('active');
    }
    
    const form = document.getElementById(tab + 'Form');
    if (form) {
        form.classList.add('active');
    }
    
    // Clear any existing messages
    hideAuthMessage();
}

/**
 * Show authentication message
 */
function showAuthMessage(message, type = 'info') {
    const authMessage = document.getElementById('authMessage');
    if (authMessage) {
        authMessage.textContent = message;
        authMessage.className = `message ${type}`;
        authMessage.style.display = 'block';
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => hideAuthMessage(), 5000);
        }
    }
}

/**
 * Hide authentication message
 */
function hideAuthMessage() {
    const authMessage = document.getElementById('authMessage');
    if (authMessage) {
        authMessage.style.display = 'none';
    }
}

/**
 * Check system status
 */
async function checkSystemStatus() {
    try {
        // Check API status
        const health = await apiClient.checkHealth();
        const systemApiStatus = document.getElementById('systemApiStatus');
        if (systemApiStatus) {
            systemApiStatus.textContent = '✅ Online';
            systemApiStatus.style.color = '#28a745';
        }
        console.log('✅ System status check completed');
    } catch (error) {
        const systemApiStatus = document.getElementById('systemApiStatus');
        if (systemApiStatus) {
            systemApiStatus.textContent = '❌ Offline';
            systemApiStatus.style.color = '#dc3545';
        }
        console.log('⚠️ System status check failed:', error.message);
    }
}

// Export for global use
window.authManager = authManager;
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.logout = logout;
window.switchAuthTab = switchAuthTab;

console.log('🔧 Fixed authentication system loaded');