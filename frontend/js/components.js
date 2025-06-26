/**
 * UI Components and Dashboard Functions
 * Handles dashboard navigation, API keys, text generation, chat, and admin functions
 */

/**
 * Dashboard Navigation
 */
function switchDashboardTab(tabName) {
    // Remove active class from all nav buttons and tab contents
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to selected nav button and tab content
    const navBtn = event?.target || document.querySelector(`[onclick="switchDashboardTab('${tabName}')"]`);
    if (navBtn) {
        navBtn.classList.add('active');
    }
    
    const tabContent = document.getElementById(tabName + 'Tab');
    if (tabContent) {
        tabContent.classList.add('active');
    }
    
    // Load data for specific tabs
    switch (tabName) {
        case 'overview':
            loadOverviewData();
            break;
        case 'apikeys':
            loadApiKeys();
            break;
        case 'models':
            loadModels();
            break;
        case 'admin':
            if (authManager.isAdmin()) {
                loadAdminData();
            }
            break;
    }
}

/**
 * Overview Tab Functions
 */
async function loadOverviewData() {
    try {
        // Update API key count
        const apiKeys = await apiClient.getApiKeys();
        const apiKeyCount = document.getElementById('apiKeyCount');
        if (apiKeyCount) {
            apiKeyCount.textContent = apiKeys.length || 0;
        }
    } catch (error) {
        console.error('Error loading overview data:', error);
    }
}

/**
 * API Keys Management
 */
async function loadApiKeys() {
    const apiKeysList = document.getElementById('apiKeysList');
    if (!apiKeysList) return;
    
    try {
        apiKeysList.innerHTML = '<div class="loading-placeholder">Loading API keys...</div>';
        
        const apiKeys = await apiClient.getApiKeys();
        
        if (apiKeys.length === 0) {
            apiKeysList.innerHTML = `
                <div class="loading-placeholder">
                    <p>No API keys found</p>
                    <button onclick="showCreateKeyModal()" class="btn btn-primary">Create Your First API Key</button>
                </div>
            `;
            return;
        }
        
        apiKeysList.innerHTML = apiKeys.map(key => `
            <div class="api-key-item">
                <div class="api-key-info">
                    <h4>${escapeHtml(key.name)}</h4>
                    <p>${escapeHtml(key.description || 'No description')}</p>
                    <p><strong>Created:</strong> ${new Date(key.created_at).toLocaleDateString()}</p>
                    ${key.last_used_at ? `<p><strong>Last used:</strong> ${new Date(key.last_used_at).toLocaleDateString()}</p>` : ''}
                    <div class="key-preview">Key ID: ${key.key_id}</div>
                </div>
                <div class="api-key-actions">
                    <button onclick="deleteApiKey(${key.id})" class="btn btn-danger btn-sm">Delete</button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        apiKeysList.innerHTML = `
            <div class="loading-placeholder">
                <p style="color: #dc3545;">Error loading API keys: ${ApiUtils.handleError(error)}</p>
                <button onclick="loadApiKeys()" class="btn btn-secondary">Retry</button>
            </div>
        `;
    }
}

function showCreateKeyModal() {
    const modal = document.getElementById('createKeyModal');
    if (modal) {
        modal.style.display = 'flex';
        // Focus on the first input
        const firstInput = modal.querySelector('input');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
}

function hideCreateKeyModal() {
    const modal = document.getElementById('createKeyModal');
    if (modal) {
        modal.style.display = 'none';
        // Clear form
        document.getElementById('newKeyName').value = '';
        document.getElementById('newKeyDescription').value = '';
    }
}

async function handleCreateApiKey(event) {
    event.preventDefault();
    
    const name = document.getElementById('newKeyName').value.trim();
    const description = document.getElementById('newKeyDescription').value.trim();
    
    if (!name) {
        showMessage('Please enter a key name', 'error');
        return;
    }
    
    const createBtn = document.getElementById('createKeyModalBtn');
    const originalText = createBtn.textContent;
    
    try {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Creating...';
        
        const result = await apiClient.createApiKey({ name, description });
        
        showMessage('API key created successfully!', 'success');
        hideCreateKeyModal();
        
        // Show the new key in a special modal or alert
        if (result.key) {
            showNewApiKeyModal(result);
        }
        
        // Refresh the list
        await loadApiKeys();
        
    } catch (error) {
        showMessage(ApiUtils.handleError(error, 'Failed to create API key'), 'error');
    } finally {
        createBtn.disabled = false;
        createBtn.textContent = originalText;
    }
}

function showNewApiKeyModal(keyData) {
    const message = `
        <strong>API Key Created Successfully!</strong><br><br>
        <strong>Name:</strong> ${escapeHtml(keyData.name)}<br>
        <strong>Key:</strong> <code style="background: #f8f9fa; padding: 4px 8px; border-radius: 4px; word-break: break-all;">${keyData.key}</code><br><br>
        <em style="color: #dc3545;">⚠️ This is the only time you'll see the full key. Save it securely!</em>
    `;
    
    showMessage(message, 'success', 10000); // Show for 10 seconds
    
    // Also copy to clipboard
    navigator.clipboard.writeText(keyData.key).then(() => {
        console.log('API key copied to clipboard');
    }).catch(err => {
        console.error('Failed to copy to clipboard:', err);
    });
}

async function deleteApiKey(keyId) {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
        return;
    }
    
    try {
        showLoading('Deleting API key...');
        await apiClient.deleteApiKey(keyId);
        showMessage('API key deleted successfully', 'success');
        await loadApiKeys();
    } catch (error) {
        showMessage(ApiUtils.handleError(error, 'Failed to delete API key'), 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Text Generation Functions
 */
async function handleGenerate(event) {
    event.preventDefault();
    
    const prompt = document.getElementById('prompt').value.trim();
    const model = document.getElementById('generateModel').value;
    const temperature = parseFloat(document.getElementById('temperature').value);
    
    if (!prompt) {
        showMessage('Please enter a prompt', 'error');
        return;
    }
    
    const generateBtn = document.getElementById('generateBtn');
    const originalText = generateBtn.textContent;
    const resultContainer = document.getElementById('generateResult');
    const resultOutput = document.getElementById('generateOutput');
    
    try {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<span class="loading-spinner"></span> Generating...';
        
        resultContainer.style.display = 'block';
        resultOutput.textContent = 'Generating response...';
        
        const result = await apiClient.generateText(prompt, { model, temperature });
        
        // Display the result
        if (result.response) {
            resultOutput.textContent = result.response;
        } else if (result.text) {
            resultOutput.textContent = result.text;
        } else {
            resultOutput.textContent = JSON.stringify(result, null, 2);
        }
        
        showMessage('Text generated successfully!', 'success');
        
    } catch (error) {
        resultOutput.textContent = `Error: ${ApiUtils.handleError(error)}`;
        resultOutput.style.color = '#dc3545';
        showMessage(ApiUtils.handleError(error, 'Failed to generate text'), 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = originalText;
    }
}

/**
 * Chat Functions
 */
let chatMessages = [
    { role: "system", content: "You are a helpful assistant." }
];

async function handleChatMessage(event) {
    event.preventDefault();
    
    const messageInput = document.getElementById('chatMessage');
    const message = messageInput.value.trim();
    const model = document.getElementById('chatModel').value;
    
    if (!message) {
        showMessage('Please enter a message', 'error');
        return;
    }
    
    const chatBtn = document.getElementById('chatBtn');
    const originalText = chatBtn.textContent;
    
    try {
        // Add user message to chat
        addChatMessage('user', message);
        chatMessages.push({ role: "user", content: message });
        
        // Clear input
        messageInput.value = '';
        
        // Disable button and show loading
        chatBtn.disabled = true;
        chatBtn.innerHTML = '<span class="loading-spinner"></span> Sending...';
        
        // Send to API
        const result = await apiClient.sendChatMessage(chatMessages, { model });
        
        // Add assistant response
        let assistantMessage = '';
        if (result.message?.content) {
            assistantMessage = result.message.content;
        } else if (result.response) {
            assistantMessage = result.response;
        } else if (result.text) {
            assistantMessage = result.text;
        } else {
            assistantMessage = 'No response received';
        }
        
        addChatMessage('assistant', assistantMessage);
        chatMessages.push({ role: "assistant", content: assistantMessage });
        
    } catch (error) {
        addChatMessage('assistant', `Error: ${ApiUtils.handleError(error)}`);
        showMessage(ApiUtils.handleError(error, 'Failed to send message'), 'error');
    } finally {
        chatBtn.disabled = false;
        chatBtn.textContent = originalText;
    }
}

function addChatMessage(role, content) {
    const chatHistory = document.getElementById('chatHistory');
    if (!chatHistory) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = `<strong>${role === 'user' ? 'You' : 'Assistant'}:</strong> ${escapeHtml(content)}`;
    
    messageDiv.appendChild(messageContent);
    chatHistory.appendChild(messageDiv);
    
    // Scroll to bottom
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function clearChat() {
    const chatHistory = document.getElementById('chatHistory');
    if (chatHistory) {
        chatHistory.innerHTML = `
            <div class="chat-message assistant">
                <div class="message-content">
                    <strong>Assistant:</strong> Hello! I'm ready to help you. What would you like to talk about?
                </div>
            </div>
        `;
    }
    
    // Reset chat messages
    chatMessages = [
        { role: "system", content: "You are a helpful assistant." }
    ];
}

/**
 * Models Management
 */
async function loadModels() {
    const modelsList = document.getElementById('modelsList');
    if (!modelsList) return;
    
    try {
        modelsList.innerHTML = '<div class="loading-placeholder">Loading models...</div>';
        
        const result = await apiClient.getModels();
        const models = result.models || result;
        
        if (!models || models.length === 0) {
            modelsList.innerHTML = `
                <div class="loading-placeholder">
                    <p>No models found</p>
                    <p style="font-size: 0.9rem; color: #666;">Make sure Ollama is running and has models installed</p>
                </div>
            `;
            return;
        }
        
        modelsList.innerHTML = models.map(model => `
            <div class="model-item">
                <h4>${escapeHtml(model.name)}</h4>
                <p><strong>Size:</strong> ${formatBytes(model.size || 0)}</p>
                <p><strong>Modified:</strong> ${model.modified_at ? new Date(model.modified_at).toLocaleDateString() : 'Unknown'}</p>
                ${model.digest ? `<p><strong>Digest:</strong> <code>${model.digest.substring(0, 16)}...</code></p>` : ''}
            </div>
        `).join('');
        
    } catch (error) {
        modelsList.innerHTML = `
            <div class="loading-placeholder">
                <p style="color: #dc3545;">Error loading models: ${ApiUtils.handleError(error)}</p>
                <p style="font-size: 0.9rem; color: #666;">Make sure Ollama is running and accessible</p>
                <button onclick="loadModels()" class="btn btn-secondary">Retry</button>
            </div>
        `;
    }
}

async function refreshModels() {
    await loadModels();
    showMessage('Models list refreshed', 'success');
}

/**
 * Admin Functions
 */
async function loadAdminData() {
    if (!authManager.isAdmin()) {
        showMessage('Access denied: Admin role required', 'error');
        return;
    }
    
    // Load users and stats when admin tab is opened
    await loadAllUsers();
    await loadSystemStats();
}

async function loadAllUsers() {
    const usersList = document.getElementById('usersList');
    if (!usersList) return;
    
    try {
        usersList.innerHTML = '<div class="loading-placeholder">Loading users...</div>';
        
        const users = await apiClient.getAllUsers();
        
        usersList.innerHTML = users.map(user => `
            <div class="user-item">
                <div class="user-info">
                    <h5>${escapeHtml(user.username)}</h5>
                    <p><strong>Email:</strong> ${escapeHtml(user.email)}</p>
                    <p><strong>Role:</strong> ${user.role} | <strong>Status:</strong> ${user.is_active ? 'Active' : 'Inactive'}</p>
                    <p><strong>Created:</strong> ${new Date(user.created_at).toLocaleDateString()}</p>
                </div>
                <div class="user-actions">
                    ${user.username !== authManager.getCurrentUser()?.username ? 
                        `<button onclick="deleteUser(${user.id})" class="btn btn-danger btn-sm">Delete</button>` : 
                        '<span style="color: #666; font-size: 0.8rem;">Current User</span>'
                    }
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        usersList.innerHTML = `
            <div class="loading-placeholder">
                <p style="color: #dc3545;">Error loading users: ${ApiUtils.handleError(error)}</p>
                <button onclick="loadAllUsers()" class="btn btn-secondary">Retry</button>
            </div>
        `;
    }
}

async function loadSystemStats() {
    const statsList = document.getElementById('systemStatsList');
    if (!statsList) return;
    
    try {
        statsList.innerHTML = '<div class="loading-placeholder">Loading statistics...</div>';
        
        const stats = await apiClient.getUsageStats();
        
        statsList.innerHTML = `
            <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h5>Total Requests</h5>
                    <p style="font-size: 1.5rem; font-weight: bold; color: #667eea;">${stats.total_requests || 0}</p>
                </div>
                <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h5>Active Users</h5>
                    <p style="font-size: 1.5rem; font-weight: bold; color: #28a745;">${stats.active_users || 0}</p>
                </div>
                <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h5>API Keys</h5>
                    <p style="font-size: 1.5rem; font-weight: bold; color: #ffc107;">${stats.total_api_keys || 0}</p>
                </div>
                <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h5>This Month</h5>
                    <p style="font-size: 1.5rem; font-weight: bold; color: #17a2b8;">${stats.monthly_requests || 0}</p>
                </div>
            </div>
        `;
        
    } catch (error) {
        statsList.innerHTML = `
            <div class="loading-placeholder">
                <p style="color: #dc3545;">Error loading statistics: ${ApiUtils.handleError(error)}</p>
                <button onclick="loadSystemStats()" class="btn btn-secondary">Retry</button>
            </div>
        `;
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
        return;
    }
    
    try {
        showLoading('Deleting user...');
        await apiClient.deleteUser(userId);
        showMessage('User deleted successfully', 'success');
        await loadAllUsers();
    } catch (error) {
        showMessage(ApiUtils.handleError(error, 'Failed to delete user'), 'error');
    } finally {
        hideLoading();
    }
}

/**
 * Utility Functions
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const text = element.textContent;
    navigator.clipboard.writeText(text).then(() => {
        showMessage('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showMessage('Failed to copy to clipboard', 'error');
    });
}

// Export functions for global use
window.switchDashboardTab = switchDashboardTab;
window.loadApiKeys = loadApiKeys;
window.showCreateKeyModal = showCreateKeyModal;
window.hideCreateKeyModal = hideCreateKeyModal;
window.handleCreateApiKey = handleCreateApiKey;
window.deleteApiKey = deleteApiKey;
window.handleGenerate = handleGenerate;
window.handleChatMessage = handleChatMessage;
window.clearChat = clearChat;
window.loadModels = loadModels;
window.refreshModels = refreshModels;
window.loadAllUsers = loadAllUsers;
window.loadSystemStats = loadSystemStats;
window.deleteUser = deleteUser;
window.copyToClipboard = copyToClipboard;