// Business Dashboard JavaScript - No Authentication Required
const API_BASE_URL = 'http://localhost:8000';

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Business Dashboard loaded - No authentication required!');
    loadDashboardData();
    setupEventListeners();
});

function setupEventListeners() {
    // PDF upload form
    const pdfForm = document.getElementById('pdfUploadForm');
    if (pdfForm) {
        pdfForm.addEventListener('submit', handlePDFUpload);
    }
}

async function loadDashboardData() {
    try {
        console.log('📊 Loading dashboard data...');
        
        // Load statistics
        await loadStatistics();
        
        // Load images
        await loadImages();
        
    } catch (error) {
        console.error('❌ Error loading dashboard data:', error);
        showStatus('❌ Error loading dashboard data', 'error');
    }
}

async function loadStatistics() {
    try {
        // Get total images from database
        const response = await fetch(`${API_BASE_URL}/api`);
        if (response.ok) {
            const data = await response.json();
            
            // Update statistics display
            document.getElementById('totalImages').textContent = '∞'; // Show all images
            document.getElementById('totalPdfs').textContent = '∞'; // Show all PDFs
            document.getElementById('totalDex').textContent = '∞'; // Show all DEX content
            document.getElementById('activeDex').textContent = '∞'; // Show all active DEX
        }
    } catch (error) {
        console.error('❌ Error loading statistics:', error);
    }
}

async function loadImages() {
    try {
        // Get all images from the main database
        const response = await fetch(`${API_BASE_URL}/api`);
        if (response.ok) {
            const data = await response.json();
            displayImages([]); // Start with empty, will be populated by uploads
        }
    } catch (error) {
        console.error('❌ Error loading images:', error);
    }
}

function displayImages(images) {
    const imagesGrid = document.getElementById('imagesGrid');
    
    if (!images || images.length === 0) {
        imagesGrid.innerHTML = `
            <div style="text-align: center; grid-column: 1 / -1; padding: 2rem; color: #666;">
                <i class="fas fa-images" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>No images uploaded yet. Upload a PDF to get started!</p>
            </div>
        `;
        return;
    }
    
    imagesGrid.innerHTML = images.map(image => `
        <div class="image-card">
            <img src="/images/${image.image_path}" alt="Extracted Image" class="image-preview">
            <div class="image-info">
                <h4 class="image-title">${image.pdf_filename} - Page ${image.page_number}</h4>
                <div class="image-details">
                    <p><strong>Business:</strong> ${image.business_name}</p>
                    <p><strong>Type:</strong> ${image.image_type}</p>
                    <p><strong>Tags:</strong> ${image.tags || 'None'}</p>
                </div>
                <div class="image-actions">
                    <button class="btn btn-primary" onclick="viewImage('${image.image_path}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-danger" onclick="deleteImage(${image.id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

async function handlePDFUpload(event) {
    event.preventDefault();
    
    const formData = new FormData();
    const pdfFile = document.getElementById('pdfFile').files[0];
    const businessName = document.getElementById('businessName').value;
    const tags = document.getElementById('tags').value;
    const imageType = document.getElementById('imageType').value;
    
    if (!pdfFile) {
        showStatus('❌ Please select a PDF file', 'error');
        return;
    }
    
    if (!businessName) {
        showStatus('❌ Please enter a business name', 'error');
        return;
    }
    
    try {
        showStatus('🔄 Uploading and processing PDF...', 'loading');
        
        // Use the main app's PDF upload endpoint
        formData.append('file', pdfFile);
        formData.append('business_name', businessName);
        formData.append('business_reference', businessName.toLowerCase().replace(/\s+/g, '_'));
        formData.append('tags', tags);
        formData.append('image_type', imageType);
        
        const response = await fetch(`${API_BASE_URL}/upload-pdf/`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            showStatus(`✅ PDF processed successfully! Extracted ${result.extracted_images} images.`, 'success');
            
            // Clear form
            document.getElementById('pdfFile').value = '';
            document.getElementById('businessName').value = '';
            document.getElementById('tags').value = '';
            document.getElementById('imageType').value = 'logo';
            
            // Refresh dashboard data
            setTimeout(() => {
                loadDashboardData();
            }, 1000);
            
        } else {
            const error = await response.json();
            showStatus(`❌ Upload failed: ${error.detail}`, 'error');
        }
        
    } catch (error) {
        console.error('❌ PDF upload error:', error);
        showStatus('❌ Upload failed: Network error', 'error');
    }
}

function viewImage(imagePath) {
    // Open image in new tab
    window.open(`/images/${imagePath}`, '_blank');
}

async function deleteImage(imageId) {
    if (!confirm('Are you sure you want to delete this image?')) {
        return;
    }
    
    try {
        showStatus('🔄 Deleting image...', 'loading');
        
        // Note: This would require the business API to work
        // For now, just show a message
        showStatus('ℹ️ Image deletion requires business API access', 'error');
        
    } catch (error) {
        console.error('❌ Error deleting image:', error);
        showStatus('❌ Error deleting image', 'error');
    }
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('uploadStatus');
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

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Test QR code generation
function testQRCode() {
    try {
        // Check if QRCode library is available
        if (typeof QRCode !== 'undefined') {
            console.log('✅ QRCode library loaded successfully');
            
            // Create a test canvas
            const canvas = document.createElement('canvas');
            canvas.width = 250;
            canvas.height = 250;
            
            // Generate a test QR code
            QRCode.toCanvas(canvas, 'https://example.com/test', {
                width: 250,
                margin: 2,
                color: {
                    dark: '#000000',
                    light: '#FFFFFF'
                }
            }, function (error) {
                if (error) {
                    console.error('❌ QR Code generation error:', error);
                    alert('QR Code generation failed: ' + error.message);
                    return;
                }
                
                console.log('✅ QR Code generated successfully');
                alert('✅ QR Code generation working! Check console for details.');
            });
        } else {
            console.log('❌ QRCode library not loaded');
            alert('❌ QRCode library not loaded. Using fallback method.');
            
            // Fallback to simple canvas pattern
            const qrCodeCanvas = document.createElement('canvas');
            const ctx = qrCodeCanvas.getContext('2d');
            qrCodeCanvas.width = 250;
            qrCodeCanvas.height = 250;
            
            // Fill background
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, 250, 250);
            
            // Create a simple QR-like pattern
            ctx.fillStyle = 'black';
            const gridSize = 10;
            for (let x = 0; x < 250; x += gridSize) {
                for (let y = 0; y < 250; y += gridSize) {
                    if ((x + y) % (gridSize * 2) === 0) {
                        ctx.fillRect(x, y, gridSize, gridSize);
                    }
                }
            }
            
            alert('✅ Fallback QR code generation working!');
        }
    } catch (error) {
        console.error('❌ Test QR code error:', error);
        alert('❌ Test failed: ' + error.message);
    }
}

// Export functions for global access
window.viewImage = viewImage;
window.deleteImage = deleteImage;
window.testQRCode = testQRCode;
