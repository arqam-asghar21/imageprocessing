// Dashboard JavaScript - User Authentication & Activity Monitoring
const API_BASE_URL = 'http://localhost:8000';

// User data and authentication
let currentUser = null;
let userToken = null;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Dashboard loaded!');
    checkAuthentication();
    setupEventListeners();
});

function setupEventListeners() {
    // Upload form
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUpload);
    }

    // Profile form
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        const dropdown = document.getElementById('userDropdown');
        const avatar = document.getElementById('userAvatar');
        
        if (!avatar.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.classList.remove('show');
        }
    });
    
    // Initialize upload fields display
    console.log('🔄 Setting up upload fields...');
    toggleUploadFields();
}

// Authentication check
function checkAuthentication() {
    const token = localStorage.getItem('userToken');
    const userData = localStorage.getItem('userData');
    
    console.log('🔍 Checking authentication...');
    console.log('🔍 Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'null');
    console.log('🔍 User data from localStorage:', userData ? 'exists' : 'null');
    
    if (!token || !userData) {
        console.log('❌ No token or user data found, redirecting to login');
        // Redirect to login if not authenticated
        window.location.href = '/login';
        return;
    }
    
    try {
        userToken = token;
        currentUser = JSON.parse(userData);
        console.log('✅ User authenticated:', currentUser);
        console.log('✅ Token set to userToken variable:', userToken ? `${userToken.substring(0, 20)}...` : 'null');
        
        // Update UI with user info
        updateUserInterface();
        
        // Load dashboard data
        loadDashboardData();
        
    } catch (error) {
        console.error('❌ Error parsing user data:', error);
        logout();
    }
}

function updateUserInterface() {
    if (!currentUser) return;
    
    // Update welcome message
    const welcomeTitle = document.getElementById('welcomeTitle');
    const welcomeSubtitle = document.getElementById('welcomeSubtitle');
    
    if (welcomeTitle) {
        welcomeTitle.textContent = `Welcome back, ${currentUser.first_name}!`;
    }
    
    if (welcomeSubtitle) {
        const userType = currentUser.user_type === 'business' ? 'Business User' : 'Regular User';
        welcomeSubtitle.textContent = `You're logged in as a ${userType}. Manage your content and track your activity.`;
    }
    
    // Update user avatar
    const userAvatar = document.getElementById('userAvatar');
    if (userAvatar) {
        userAvatar.textContent = currentUser.first_name.charAt(0).toUpperCase();
    }
    
    // Update profile form
    const profileFirstName = document.getElementById('profileFirstName');
    const profileLastName = document.getElementById('profileLastName');
    const profileEmail = document.getElementById('profileEmail');
    
    if (profileFirstName) profileFirstName.value = currentUser.first_name || '';
    if (profileLastName) profileLastName.value = currentUser.last_name || '';
    if (profileEmail) profileEmail.value = currentUser.email || '';
}

async function loadDashboardData() {
    try {
        console.log('📊 Loading dashboard data...');
        
        // Load user statistics
        await loadUserStatistics();
        
        // Load user uploads
        await loadUserUploads();
        
        // Load user activity
        await loadUserActivity();
        
    } catch (error) {
        console.error('❌ Error loading dashboard data:', error);
        showMessage('Error loading dashboard data', 'error');
    }
}

async function loadUserStatistics() {
    try {
        console.log('🔑 Token being used:', userToken);
        console.log('🔑 Token type:', typeof userToken);
        console.log('🔑 Token length:', userToken ? userToken.length : 'undefined');
        
        if (!userToken) {
            console.error('❌ No user token available');
            throw new Error('No authentication token');
        }
        
        const response = await fetch(`${API_BASE_URL}/api/auth/statistics`, {
            headers: {
                'Authorization': `Bearer ${userToken}`
            }
        });
        
        if (response.ok) {
            const stats = await response.json();
            updateStatistics(stats);
        } else {
            // Use placeholder data for now
            updateStatistics({
                total_uploads: 0,
                total_pdfs: 0,
                total_matches: 0,
                days_active: 1
            });
        }
    } catch (error) {
        console.error('❌ Error loading statistics:', error);
        // Use placeholder data
        updateStatistics({
            total_uploads: 0,
            total_pdfs: 0,
            total_matches: 0,
            days_active: 1
        });
    }
}

function updateStatistics(stats) {
    document.getElementById('totalUploads').textContent = stats.total_uploads || 0;
    document.getElementById('totalPdfs').textContent = stats.total_pdfs || 0;
    document.getElementById('totalMatches').textContent = stats.total_matches || 0;
    document.getElementById('lastActivity').textContent = stats.days_active || 1;
}

async function loadUserUploads() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/uploads`, {
            headers: {
                'Authorization': `Bearer ${userToken}`
            }
        });
        
        if (response.ok) {
            const uploads = await response.json();
            displayUploads(uploads);
        } else {
            displayUploads([]);
        }
    } catch (error) {
        console.error('❌ Error loading uploads:', error);
        displayUploads([]);
    }
}

function displayUploads(uploads) {
    const uploadsGrid = document.getElementById('uploadsGrid');
    
    if (!uploads || uploads.length === 0) {
        uploadsGrid.innerHTML = `
            <div class="no-data">
                <i class="fas fa-images"></i>
                <p>No uploads yet</p>
                <p>Start by uploading an image or PDF above</p>
            </div>
        `;
        return;
    }
    
    uploadsGrid.innerHTML = uploads.map(upload => {
        let fileUrl, contentDisplay;
        
        if (upload.content_type === 'image') {
            // Check if this is an extracted image from PDF (stored in extracted_images folder)
            if (upload.file_path.includes('extracted_images/')) {
                // This is an extracted image, use the extracted_images route
                fileUrl = `/images/${upload.file_path.split('extracted_images/')[1]}`;
            } else {
                // This is a regular user upload
                const userMatch = upload.file_path.match(/user_uploads\/(\d+)\/(.+)/);
                const userId = userMatch ? userMatch[1] : '1';
                const filename = userMatch ? userMatch[2] : upload.filename;
                fileUrl = `/user_uploads/${userId}/${filename}`;
            }
            
            contentDisplay = `<img src="${fileUrl}" alt="Uploaded Content" class="image-preview">`;
        } else {
            // For PDFs, show a PDF icon
            contentDisplay = `<div class="pdf-preview"><i class="fas fa-file-pdf fa-3x"></i><p>${upload.filename}</p></div>`;
        }
        
        return `
            <div class="image-card">
                ${contentDisplay}
                <div class="image-info">
                    <h4 class="image-title">${upload.filename || 'Uploaded File'}</h4>
                    <div class="image-details">
                        <p><strong>Type:</strong> ${upload.content_type || 'Unknown'}</p>
                        <p><strong>Uploaded:</strong> ${formatDate(upload.uploaded_at)}</p>
                        <p><strong>Tags:</strong> ${upload.tags || 'None'}</p>
                    </div>
                    <div class="image-actions">
                        <button class="btn btn-secondary" onclick="viewUpload('${upload.id}')">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <button class="btn btn-danger" onclick="deleteUpload('${upload.id}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function loadUserActivity() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/activity`, {
            headers: {
                'Authorization': `Bearer ${userToken}`
            }
        });
        
        if (response.ok) {
            const activities = await response.json();
            displayActivity(activities);
        } else {
            displayActivity([]);
        }
    } catch (error) {
        console.error('❌ Error loading activity:', error);
        displayActivity([]);
    }
}

function displayActivity(activities) {
    const activityTimeline = document.getElementById('activityTimeline');
    
    if (!activities || activities.length === 0) {
        activityTimeline.innerHTML = `
            <div class="no-data">
                <i class="fas fa-chart-line"></i>
                <p>No activity yet</p>
                <p>Your activity will appear here as you use the system</p>
            </div>
        `;
        return;
    }
    
    activityTimeline.innerHTML = activities.map(activity => `
        <div class="timeline-item">
            <div class="timeline-icon">
                <i class="fas ${getActivityIcon(activity.type)}"></i>
            </div>
            <div class="timeline-content">
                <div class="timeline-title">${activity.title}</div>
                <div class="timeline-time">${formatDate(activity.timestamp)}</div>
                <div class="timeline-description">${activity.description}</div>
            </div>
        </div>
    `).join('');
}

function getActivityIcon(activityType) {
    const icons = {
        'upload': 'fa-upload',
        'match': 'fa-search',
        'login': 'fa-sign-in-alt',
        'profile': 'fa-user-edit',
        'delete': 'fa-trash'
    };
    return icons[activityType] || 'fa-circle';
}

// Upload handling
async function handleUpload(event) {
    event.preventDefault();
    
    const uploadType = document.getElementById('uploadType').value;
    const imageFile = document.getElementById('imageFile').files[0];
    const pdfFile = document.getElementById('pdfFile').files[0];
    const tags = document.getElementById('uploadTags').value;
    
    console.log('🔄 Upload attempt:', { uploadType, imageFile, pdfFile, tags });
    
    let file = null;
    if (uploadType === 'image' && imageFile) {
        file = imageFile;
        console.log('✅ Selected image file:', imageFile.name, imageFile.type);
    } else if (uploadType === 'pdf' && pdfFile) {
        file = pdfFile;
        console.log('✅ Selected PDF file:', pdfFile.name, pdfFile.type);
    }
    
    if (!file) {
        console.log('❌ No file selected for upload type:', uploadType);
        showMessage('Please select a file to upload', 'error');
        return;
    }
    
    try {
        showMessage('🔄 Uploading content...', 'loading');
        
        // For PDFs, we need to extract images first, then upload them
        if (uploadType === 'pdf') {
            try {
                showMessage('🔄 Processing PDF and extracting images...', 'loading');
                
                // First, upload the PDF to get images extracted
                const pdfFormData = new FormData();
                pdfFormData.append('file', file);
                pdfFormData.append('business_name', currentUser.company_name || currentUser.first_name);
                pdfFormData.append('business_reference', currentUser.company_name || currentUser.first_name);
                pdfFormData.append('tags', tags);
                pdfFormData.append('image_type', 'document');
                
                const pdfResponse = await fetch(`${API_BASE_URL}/upload-pdf/`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${userToken}`
                    },
                    body: pdfFormData
                });
                
                if (pdfResponse.ok) {
                    const pdfResult = await pdfResponse.json();
                    console.log('✅ PDF processed successfully:', pdfResult);
                    showMessage(`✅ PDF processed! ${pdfResult.extracted_images} images extracted.`, 'success');
                    
                    // Clear form
                    document.getElementById('uploadForm').reset();
                    
                    // Refresh dashboard data
                    setTimeout(() => {
                        loadDashboardData();
                    }, 1000);
                    
                    return;
                } else {
                    const error = await pdfResponse.json();
                    const errorMessage = error.detail || error.message || 'PDF processing failed';
                    showMessage(`❌ PDF processing failed: ${errorMessage}`, 'error');
                    return;
                }
            } catch (error) {
                console.error('❌ PDF processing error:', error);
                showMessage('❌ PDF processing failed: Network error', 'error');
                return;
            }
        }
        
        // For regular image uploads, use the normal upload endpoint
        const formData = new FormData();
        formData.append('file', file);
        formData.append('content_type', uploadType);
        formData.append('tags', tags);
        
        console.log('🔄 Sending upload request to:', `${API_BASE_URL}/api/auth/upload`);
        console.log('🔄 Form data contents:', {
            file: file.name,
            content_type: uploadType,
            tags: tags
        });
        
        const response = await fetch(`${API_BASE_URL}/api/auth/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${userToken}`
            },
            body: formData
        });
        
        console.log('🔄 Upload response status:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ Upload successful:', result);
            showMessage(`✅ ${uploadType.toUpperCase()} uploaded successfully!`, 'success');
            
            // Clear form
            document.getElementById('uploadForm').reset();
            
            // Refresh dashboard data
            setTimeout(() => {
                loadDashboardData();
            }, 1000);
            
        } else {
            const error = await response.json();
            console.log('❌ Upload error response:', error);
            const errorMessage = error.detail || error.message || 'Upload failed';
            showMessage(`❌ Upload failed: ${errorMessage}`, 'error');
        }
        
    } catch (error) {
        console.error('❌ Upload error:', error);
        showMessage('❌ Upload failed: Network error', 'error');
    }
}

function toggleUploadFields() {
    const uploadType = document.getElementById('uploadType').value;
    const imageGroup = document.getElementById('imageUploadGroup');
    const pdfGroup = document.getElementById('pdfUploadGroup');
    
    console.log('🔄 Toggling upload fields for type:', uploadType);
    console.log('🔄 Image group element:', imageGroup);
    console.log('🔄 PDF group element:', pdfGroup);
    
    if (uploadType === 'image') {
        imageGroup.style.display = 'block';
        pdfGroup.style.display = 'none';
        console.log('✅ Showing image upload, hiding PDF upload');
    } else if (uploadType === 'pdf') {
        imageGroup.style.display = 'none';
        pdfGroup.style.display = 'block';
        console.log('✅ Showing PDF upload, hiding image upload');
    } else {
        console.log('❌ Unknown upload type:', uploadType);
    }
}

// Profile handling
async function handleProfileUpdate(event) {
    event.preventDefault();
    
    const firstName = document.getElementById('profileFirstName').value;
    const lastName = document.getElementById('profileLastName').value;
    
    if (!firstName || !lastName) {
        showMessage('Please fill in all fields', 'error');
        return;
    }
    
    try {
        showMessage('🔄 Updating profile...', 'loading');
        
        const response = await fetch(`${API_BASE_URL}/api/auth/profile`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${userToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage('✅ Profile updated successfully!', 'success');
            
            // Update local user data
            currentUser.first_name = firstName;
            currentUser.last_name = lastName;
            localStorage.setItem('userData', JSON.stringify(currentUser));
            
            // Update UI
            updateUserInterface();
            
        } else {
            const error = await response.json();
            const errorMessage = error.detail || error.message || 'Update failed';
            showMessage(`❌ Update failed: ${errorMessage}`, 'error');
        }
        
    } catch (error) {
        console.error('❌ Profile update error:', error);
        showMessage('❌ Update failed: Network error', 'error');
    }
}

// Tab switching
function switchTab(tabName) {
    // Update active tab
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // Update active content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}Tab`).classList.add('active');
}

// User menu
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('show');
}

function viewProfile() {
    switchTab('settings');
    toggleUserMenu();
}

function viewSettings() {
    switchTab('settings');
    toggleUserMenu();
}

function logout() {
    // Clear local storage
    localStorage.removeItem('userToken');
    localStorage.removeItem('userData');
    
    // Redirect to login
    window.location.href = '/login';
}

// Utility functions
function showMessage(message, type) {
    const statusDiv = document.getElementById('uploadStatus') || document.getElementById('profileStatus');
    if (!statusDiv) return;
    
    statusDiv.textContent = message;
    statusDiv.className = `status-message status-${type}`;
    statusDiv.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
}

async function viewUpload(uploadId) {
    try {
        // Get the upload details
        const response = await fetch(`${API_BASE_URL}/api/auth/uploads/${uploadId}`, {
            headers: {
                'Authorization': `Bearer ${userToken}`
            }
        });
        
        if (response.ok) {
            const upload = await response.json();
            
            // Create a modal to display the upload details
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${upload.filename}</h3>
                        <span class="close" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <div class="upload-details">
                            <p><strong>Type:</strong> ${upload.content_type}</p>
                            <p><strong>Uploaded:</strong> ${formatDate(upload.uploaded_at)}</p>
                            <p><strong>Tags:</strong> ${upload.tags || 'None'}</p>
                        </div>
                        ${upload.content_type === 'image' ? 
                            `<div class="image-display">
                                <img src="/user_uploads/1/${upload.filename}" alt="${upload.filename}" style="max-width: 100%; height: auto;">
                            </div>` : 
                            `<div class="pdf-display">
                                <i class="fas fa-file-pdf fa-5x" style="color: #e74c3c;"></i>
                                <p>PDF File: ${upload.filename}</p>
                            </div>`
                        }
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Close modal when clicking outside
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
            
        } else {
            showMessage('❌ Failed to load upload details', 'error');
        }
    } catch (error) {
        console.error('❌ Error viewing upload:', error);
        showMessage('❌ Error viewing upload', 'error');
    }
}

async function deleteUpload(uploadId) {
    if (!confirm('Are you sure you want to delete this upload? This action cannot be undone.')) {
        return;
    }
    
    try {
        showMessage('🔄 Deleting upload...', 'loading');
        
        const response = await fetch(`${API_BASE_URL}/api/auth/uploads/${uploadId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${userToken}`
            }
        });
        
        if (response.ok) {
            showMessage('✅ Upload deleted successfully', 'success');
            
            // Refresh the uploads display
            await loadUserUploads();
            
            // Refresh statistics
            await loadUserStatistics();
            
            // Refresh activity
            await loadUserActivity();
            
        } else {
            const error = await response.json();
            const errorMessage = error.detail || error.message || 'Delete failed';
            showMessage(`❌ Delete failed: ${errorMessage}`, 'error');
        }
        
    } catch (error) {
        console.error('❌ Error deleting upload:', error);
        showMessage('❌ Delete failed: Network error', 'error');
    }
}

// Export functions for global access
window.switchTab = switchTab;
window.toggleUserMenu = toggleUserMenu;
window.viewProfile = viewProfile;
window.viewSettings = viewSettings;
window.logout = logout;
window.viewUpload = viewUpload;
window.deleteUpload = deleteUpload;
window.toggleUploadFields = toggleUploadFields;
