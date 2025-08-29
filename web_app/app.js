// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global variables
let uploadedImage = null;
let databaseImages = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadDatabase();
});

// Setup event listeners
function setupEventListeners() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // File input change
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);

    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());
}

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processFile(file);
    }
}

// Handle drag over
function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

// Handle drag leave
function handleDragLeave(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
}

// Handle drop
function handleDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

// Process uploaded file
function processFile(file) {
    if (!file.type.startsWith('image/')) {
        showStatus('Please select an image file.', 'error');
        return;
    }

    uploadedImage = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewImage = document.getElementById('previewImage');
        previewImage.src = e.target.result;
        document.getElementById('previewSection').style.display = 'flex';
        document.getElementById('matchBtn').disabled = false;
    };
    reader.readAsDataURL(file);

    showStatus('Image uploaded successfully!', 'success');
}

// Match image with database
async function matchImage() {
    if (!uploadedImage) {
        showStatus('Please upload an image first.', 'error');
        return;
    }

    showStatus('🔍 Finding matches...', 'info');
    document.getElementById('matchBtn').disabled = true;

    try {
        const formData = new FormData();
        formData.append('image', uploadedImage);

        const response = await fetch(`${API_BASE_URL}/match-image/`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            displayResults(result);
            showStatus('✅ Match found!', 'success');
        } else {
            const errorText = await response.text();
            showStatus(`❌ No match found: ${errorText}`, 'error');
            displayNoResults();
        }
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`, 'error');
        displayNoResults();
    } finally {
        document.getElementById('matchBtn').disabled = false;
    }
}

// Display match results
function displayResults(match) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContainer = document.getElementById('resultsContainer');
    
    const confidence = Math.round((match.match_confidence || 0) * 100);
    
    // Fix image URL construction
    const imageFileName = match.image_path.split('/').pop();
    const imageUrl = `${API_BASE_URL}/images/${imageFileName}`;
    
    resultsContainer.innerHTML = `
        <div class="match-card">
            <img src="${imageUrl}" 
                 alt="Matched Image" class="match-image">
            <div class="match-info">
                <div class="match-title">${match.business_name || 'Unknown'}</div>
                <div class="match-details">
                    <strong>PDF:</strong> ${match.pdf_filename}<br>
                    <strong>Page:</strong> ${match.page_number}<br>
                    <strong>Type:</strong> ${match.image_type || 'Unknown'}<br>
                    <strong>Reference:</strong> ${match.business_reference || 'N/A'}
                </div>
            </div>
            <div class="confidence">${confidence}% Match</div>
        </div>
    `;
    
    resultsSection.style.display = 'block';
}

// Display no results
function displayNoResults() {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContainer = document.getElementById('resultsContainer');
    
    resultsContainer.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <h3>❌ No Match Found</h3>
            <p>The uploaded image doesn't match any images in our database.</p>
            <p>Try uploading a different image or check our database below.</p>
        </div>
    `;
    
    resultsSection.style.display = 'block';
}

// Load database images
async function loadDatabase() {
    showStatus('📚 Loading database...', 'info');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/images/`);
        
        if (response.ok) {
            databaseImages = await response.json();
            displayDatabase();
            showStatus(`✅ Loaded ${databaseImages.length} images from database`, 'success');
        } else {
            showStatus('❌ Error loading database', 'error');
        }
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`, 'error');
    }
}

// Display database images
function displayDatabase() {
    const databaseGrid = document.getElementById('databaseGrid');
    
    databaseGrid.innerHTML = databaseImages.map(image => {
        const imageFileName = image.image_path.split('/').pop();
        const imageUrl = `${API_BASE_URL}/images/${imageFileName}`;
        
        return `
            <div class="database-item">
                <img src="${imageUrl}" alt="${image.business_name}" class="database-image">
                <div class="match-title">${image.business_name || 'Unknown'}</div>
                <div class="match-details">
                    ${image.pdf_filename}<br>
                    Page ${image.page_number}
                </div>
            </div>
        `;
    }).join('');
}

// Show status message
function showStatus(message, type = 'info') {
    const statusSection = document.getElementById('statusSection');
    
    statusSection.innerHTML = `
        <div class="status ${type}">
            ${message}
        </div>
    `;
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            statusSection.innerHTML = '';
        }, 5000);
    }
}

// Test API connection
async function testConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/api`);
        if (response.ok) {
            console.log('✅ Backend connected successfully');
            return true;
        } else {
            console.log('❌ Backend connection failed');
            return false;
        }
    } catch (error) {
        console.log('❌ Backend connection error:', error);
        return false;
    }
}

// Initialize connection test
testConnection(); 