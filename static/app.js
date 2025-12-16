// API Base URL
const API_BASE = '';

// State
let currentStore = null;
let stores = [];

// DOM Elements
const storesList = document.getElementById('storesList');
const createStoreBtn = document.getElementById('createStoreBtn');
const createStoreModal = document.getElementById('createStoreModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const confirmCreateBtn = document.getElementById('confirmCreateBtn');
const storeName = document.getElementById('storeName');
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const uploadStatus = document.getElementById('uploadStatus');
const messagesContainer = document.getElementById('messagesContainer');
const queryInput = document.getElementById('queryInput');
const sendBtn = document.getElementById('sendBtn');
const selectedStoreSpan = document.getElementById('selectedStore');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStores();
    setupEventListeners();
    autoResizeTextarea();
});

// Event Listeners
function setupEventListeners() {
    createStoreBtn.addEventListener('click', () => openModal());
    closeModalBtn.addEventListener('click', () => closeModal());
    cancelModalBtn.addEventListener('click', () => closeModal());
    confirmCreateBtn.addEventListener('click', () => createStore());
    
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    sendBtn.addEventListener('click', () => sendQuery());
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuery();
        }
    });
    queryInput.addEventListener('input', () => {
        sendBtn.disabled = !queryInput.value.trim() || !currentStore;
    });
}

// Auto-resize textarea
function autoResizeTextarea() {
    queryInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

// Modal Functions
function openModal() {
    createStoreModal.classList.add('active');
    storeName.value = '';
    storeName.focus();
}

function closeModal() {
    createStoreModal.classList.remove('active');
}

// Store Management
async function loadStores() {
    try {
        const response = await fetch(`${API_BASE}/api/stores/list`);
        const data = await response.json();
        
        if (data.success) {
            stores = data.stores;
            renderStores();
        }
    } catch (error) {
        console.error('Failed to load stores:', error);
        showError('Failed to load stores');
    }
}

function renderStores() {
    if (stores.length === 0) {
        storesList.innerHTML = '<p style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 20px;">No stores yet. Create one to get started!</p>';
        return;
    }
    
    storesList.innerHTML = stores.map(store => {
        const storeId = store.name.split('/')[1];
        return `
            <div class="store-item ${currentStore?.name === store.name ? 'active' : ''}" data-store-name="${store.name}">
                <div class="store-name">${store.display_name}</div>
                <div class="store-id">${storeId}</div>
                <button class="delete-btn" data-store-name="${store.name}" onclick="deleteStore(event, '${store.name}')">Delete</button>
            </div>
        `;
    }).join('');
    
    // Add click listeners
    document.querySelectorAll('.store-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (!e.target.classList.contains('delete-btn')) {
                selectStore(item.dataset.storeName);
            }
        });
    });
}

function selectStore(storeName) {
    currentStore = stores.find(s => s.name === storeName);
    if (currentStore) {
        selectedStoreSpan.textContent = currentStore.display_name;
        sendBtn.disabled = !queryInput.value.trim();
        renderStores();
    }
}

async function createStore() {
    const name = storeName.value.trim();
    if (!name) {
        alert('Please enter a store name');
        return;
    }
    
    try {
        confirmCreateBtn.disabled = true;
        confirmCreateBtn.textContent = 'Creating...';
        
        const response = await fetch(`${API_BASE}/api/stores/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ display_name: name })
        });
        
        const data = await response.json();
        
        if (data.success) {
            closeModal();
            await loadStores();
            showSuccess('Store created successfully!');
        } else {
            showError('Failed to create store');
        }
    } catch (error) {
        console.error('Failed to create store:', error);
        showError('Failed to create store');
    } finally {
        confirmCreateBtn.disabled = false;
        confirmCreateBtn.textContent = 'Create';
    }
}

async function deleteStore(event, storeName) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this store?')) {
        return;
    }
    
    try {
        const storeId = storeName.split('/')[1];
        const response = await fetch(`${API_BASE}/api/stores/${storeId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (currentStore?.name === storeName) {
                currentStore = null;
                selectedStoreSpan.textContent = 'No store selected';
                sendBtn.disabled = true;
            }
            await loadStores();
            showSuccess('Store deleted successfully!');
        } else {
            showError('Failed to delete store');
        }
    } catch (error) {
        console.error('Failed to delete store:', error);
        showError('Failed to delete store');
    }
}

// File Upload
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
}

async function uploadFile(file) {
    if (!currentStore) {
        alert('Please select a store first');
        return;
    }
    
    try {
        uploadArea.style.display = 'none';
        uploadProgress.style.display = 'block';
        progressFill.style.width = '0%';
        uploadStatus.textContent = 'Uploading...';
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('store_name', currentStore.name);
        formData.append('display_name', file.name);
        
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
            }
        }, 200);
        
        const response = await fetch(`${API_BASE}/api/files/upload`, {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        
        const data = await response.json();
        
        if (data.success) {
            progressFill.style.width = '100%';
            uploadStatus.textContent = 'File uploaded and indexed successfully!';
            uploadStatus.style.color = 'var(--success)';
            
            setTimeout(() => {
                uploadArea.style.display = 'block';
                uploadProgress.style.display = 'none';
                uploadStatus.style.color = 'var(--text-secondary)';
                fileInput.value = '';
            }, 2000);
            
            showSuccess('File uploaded successfully!');
        } else {
            throw new Error(data.detail || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload failed:', error);
        uploadStatus.textContent = 'Upload failed: ' + error.message;
        uploadStatus.style.color = 'var(--error)';
        
        setTimeout(() => {
            uploadArea.style.display = 'block';
            uploadProgress.style.display = 'none';
            uploadStatus.style.color = 'var(--text-secondary)';
        }, 3000);
        
        showError('Upload failed');
    }
}

// Chat Functions
async function sendQuery() {
    const query = queryInput.value.trim();
    if (!query || !currentStore) return;
    
    // Clear welcome message if present
    const welcomeMsg = messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    // Add user message
    addMessage('user', query);
    queryInput.value = '';
    queryInput.style.height = 'auto';
    sendBtn.disabled = true;
    
    // Add loading message
    const loadingId = 'loading-' + Date.now();
    addMessage('assistant', 'Thinking...', null, loadingId);
    
    try {
        const response = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                store_name: currentStore.name
            })
        });
        
        const data = await response.json();
        
        // Remove loading message
        document.getElementById(loadingId)?.remove();
        
        if (data.success) {
            addMessage('assistant', data.response, data.grounding_metadata);
        } else {
            addMessage('assistant', 'Sorry, I encountered an error: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Query failed:', error);
        document.getElementById(loadingId)?.remove();
        addMessage('assistant', 'Sorry, I encountered an error processing your request.');
    }
    
    sendBtn.disabled = !queryInput.value.trim();
}

function addMessage(role, text, groundingMetadata = null, id = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    if (id) messageDiv.id = id;
    
    let citationsHtml = '';
    if (groundingMetadata && groundingMetadata.grounding_chunks && groundingMetadata.grounding_chunks.length > 0) {
        const chunks = groundingMetadata.grounding_chunks;
        citationsHtml = `
            <div class="citations">
                <div class="citations-title">📚 Sources</div>
                ${chunks.map((chunk, idx) => {
                    if (chunk.retrieved_context) {
                        return `
                            <div class="citation-item">
                                <div class="citation-source">${chunk.retrieved_context.title || 'Document ' + (idx + 1)}</div>
                                ${chunk.retrieved_context.text ? `<div class="citation-text">${chunk.retrieved_context.text.substring(0, 150)}...</div>` : ''}
                            </div>
                        `;
                    }
                    return '';
                }).join('')}
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text">${escapeHtml(text)}</div>
            ${citationsHtml}
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showSuccess(message) {
    // Simple console log for now - could be enhanced with toast notifications
    console.log('✅', message);
}

function showError(message) {
    // Simple console log for now - could be enhanced with toast notifications
    console.error('❌', message);
}
