// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global variables
let cameraStream = null;
let capturedImage = null;
let uploadedImage = null;

// Check camera availability on page load
document.addEventListener('DOMContentLoaded', function() {
    checkCameraAvailability();
    loadDatabaseImages();
    setupImageUpload();
});

// Image upload functionality
function setupImageUpload() {
    const imageFileInput = document.getElementById('imageFile');
    
    imageFileInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file && file.type.startsWith('image/')) {
            uploadedImage = file;
            displayImagePreview(file);
        } else {
            showStatus('Please select a valid image file', 'error');
        }
    });
}

function displayImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewSection = document.getElementById('imagePreviewSection');
        const previewImage = document.getElementById('imagePreview');
        
        previewImage.src = e.target.result;
        previewSection.style.display = 'block';
        
        showStatus(`Image "${file.name}" selected successfully`, 'success');
    };
    reader.readAsDataURL(file);
}

async function matchUploadedImage() {
    if (!uploadedImage) {
        showStatus('Please select an image first', 'error');
        return;
    }

    await matchImage(uploadedImage, 'upload');
}

// Camera functionality
async function startCamera() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showCameraError('Camera not supported in this browser');
            return;
        }

        // Check camera permissions
        if (navigator.permissions) {
            const permission = await navigator.permissions.query({ name: 'camera' });
            if (permission.state === 'denied') {
                showCameraError('Camera access denied. Please enable camera permissions in your browser settings.');
                return;
            }
        }

        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'environment' // Use back camera if available
            } 
        });
        
        const video = document.getElementById('video');
        video.srcObject = stream;
        cameraStream = stream;
        
        // Show camera controls
        document.querySelector('.camera-controls').style.display = 'flex';
        
        console.log('Camera started successfully');
        
    } catch (error) {
        console.error('Error starting camera:', error);
        showCameraError(`Failed to start camera: ${error.message}`);
    }
}

function capturePhoto() {
    if (!cameraStream) {
        showCameraError('Camera not started');
        return;
    }

    try {
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const context = canvas.getContext('2d');
        
        // Set canvas size to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Draw video frame to canvas
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Convert canvas to blob
        canvas.toBlob(function(blob) {
            capturedImage = blob;
            
            // Show preview
            const previewSection = document.getElementById('previewSection');
            const capturedImageElement = document.getElementById('capturedImage');
            
            capturedImageElement.src = URL.createObjectURL(blob);
            previewSection.style.display = 'block';
            
            console.log('Photo captured successfully');
        }, 'image/jpeg', 0.8);
        
    } catch (error) {
        console.error('Error capturing photo:', error);
        showCameraError(`Failed to capture photo: ${error.message}`);
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
        
        const video = document.getElementById('video');
        video.srcObject = null;
        
        // Hide camera controls
        document.querySelector('.camera-controls').style.display = 'none';
        
        console.log('Camera stopped');
    }
}

function checkCameraAvailability() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showCameraError('Camera not supported in this browser');
    }
}

function showCameraError(message) {
    const statusContent = document.getElementById('statusContent');
    statusContent.innerHTML = `
        <div class="camera-error">
            <i class="fas fa-exclamation-triangle"></i>
            <p>${message}</p>
        </div>
    `;
}

// PDF Upload functionality
async function uploadPDF() {
    const fileInput = document.getElementById('pdfFile');
    const businessName = document.getElementById('businessName').value;
    const businessReference = document.getElementById('businessReference').value;
    const tags = document.getElementById('tags').value;
    const imageType = document.getElementById('imageType').value;

    if (!fileInput.files[0]) {
        showStatus('Please select a PDF file', 'error');
        return;
    }

    if (!businessName || !businessReference) {
        showStatus('Please fill in business name and reference', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('business_name', businessName);
    formData.append('business_reference', businessReference);
    formData.append('tags', tags);
    formData.append('image_type', imageType);

    showStatus('Uploading and processing PDF...', 'loading');

    try {
        const response = await fetch('/upload/', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            showStatus(`Success! ${result.message}`, 'success');
            
            // Clear form
            fileInput.value = '';
            document.getElementById('businessName').value = '';
            document.getElementById('businessReference').value = '';
            document.getElementById('tags').value = '';
            document.getElementById('imageType').value = 'logo';
            
            // Refresh database images
            loadDatabaseImages();
        } else {
            const error = await response.json();
            showStatus(`Upload failed: ${error.detail || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showStatus(`Upload failed: ${error.message}`, 'error');
    }
}

// Image matching functionality
async function matchCameraImage() {
    if (!capturedImage) {
        showStatus('Please capture a photo first', 'error');
        return;
    }

    await matchImage(capturedImage, 'camera');
}

async function matchImage(imageBlob, source = 'upload') {
    showStatus('Finding matches...', 'loading');

    try {
        const formData = new FormData();
        formData.append('image', imageBlob, `image_${source}_${Date.now()}.jpg`);

        const response = await fetch('/match-image/', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Match result:', result);
            
            if (result.match_found) {
            displayResults(result);
            } else {
                displayNoResults(result.message);
            }
        } else {
            const error = await response.json();
            showStatus(`Matching failed: ${error.detail || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Matching error:', error);
        showStatus(`Matching failed: ${error.message}`, 'error');
    }
}

// Display functions
function displayResults(result) {
    const statusContent = document.getElementById('statusContent');
    
    const qualityColor = result.match_quality === 'high' ? '#48bb78' : 
                        result.match_quality === 'medium' ? '#ed8936' : '#e53e3e';
    
    statusContent.innerHTML = `
        <div class="result-item">
            <h3><i class="fas fa-check-circle" style="color: ${qualityColor}"></i> Match Found!</h3>
            <p><strong>Business:</strong> ${result.business_name || 'N/A'}</p>
            <p><strong>PDF File:</strong> ${result.pdf_filename || 'N/A'}</p>
            <p><strong>Page:</strong> ${result.page_number || 'N/A'}</p>
            <p><strong>Type:</strong> ${result.image_type || 'N/A'}</p>
            <p><strong>Tags:</strong> ${result.tags || 'N/A'}</p>
            <p><strong>Reference:</strong> ${result.business_reference || 'N/A'}</p>
            <span class="confidence">Confidence: ${(result.similarity_score * 100).toFixed(1)}%</span>
            <span class="confidence" style="background: ${qualityColor}">Quality: ${result.match_quality}</span>
        </div>
        
        ${result.dex_content ? `
        <div class="result-item">
            <h3><i class="fas fa-magic"></i> DEX Experience Available</h3>
            <p><strong>Title:</strong> ${result.dex_content.title}</p>
            <p><strong>Description:</strong> ${result.dex_content.description}</p>
            <p><strong>Type:</strong> ${result.dex_content.content_type}</p>
            
            <div style="margin-top: 15px;">
                <h4><i class="fas fa-rocket"></i> Experience Options:</h4>
                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;">
                    ${result.dex_content.delivery_options.webpage_available ? `
                        <button class="btn btn-success" onclick="openDEXContent('${result.dex_content.delivery_options.direct_link}', 'webpage')">
                            <i class="fas fa-globe"></i> Open Webpage
                        </button>
                    ` : ''}
                    
                    ${result.dex_content.delivery_options.ar_enabled ? `
                        <button class="btn" onclick="openDEXContent('${result.dex_content.delivery_options.ar_link}', 'ar')" style="background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);">
                            <i class="fas fa-cube"></i> Launch AR
                        </button>
                    ` : ''}
                    
                    ${result.dex_content.delivery_options.video_available ? `
                        <button class="btn" onclick="openDEXContent('${result.dex_content.content_url}', 'video')" style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);">
                            <i class="fas fa-play"></i> Play Video
                        </button>
                    ` : ''}
                    
                    <button class="btn btn-secondary" onclick="generateQRCode('${result.dex_content.delivery_options.qr_code}')">
                        <i class="fas fa-qrcode"></i> QR Code
                    </button>
                </div>
            </div>
        </div>
        ` : ''}
        
        <button class="btn" onclick="loadDatabaseImages()">
            <i class="fas fa-refresh"></i> View All Database Images
        </button>
    `;
}

function displayNoResults(message) {
    const statusContent = document.getElementById('statusContent');
    statusContent.innerHTML = `
        <div class="no-match">
            <i class="fas fa-search fa-2x" style="color: #cbd5e0; margin-bottom: 10px;"></i>
            <p>${message || 'No matches found in the database'}</p>
            <p style="font-size: 0.9rem; margin-top: 10px;">Try uploading a different image or check if similar images exist in the database.</p>
        </div>
        
        <button class="btn" onclick="loadDatabaseImages()">
            <i class="fas fa-database"></i> View Database Images
        </button>
    `;
}

function showStatus(message, type = 'info') {
    const statusContent = document.getElementById('statusContent');
    
    let icon = 'info-circle';
    let bgClass = 'info';
    
    switch (type) {
        case 'error':
            icon = 'exclamation-triangle';
            bgClass = 'error';
            break;
        case 'success':
            icon = 'check-circle';
            bgClass = 'success';
            break;
        case 'loading':
            icon = 'spinner';
            bgClass = 'loading';
            break;
    }
    
    if (type === 'loading') {
        statusContent.innerHTML = `
            <div class="loading">
                <i class="fas fa-${icon}"></i>
                <p>${message}</p>
            </div>
        `;
    } else {
        statusContent.innerHTML = `
            <div class="${bgClass}">
                <i class="fas fa-${icon}"></i>
                <p>${message}</p>
        </div>
    `;
    }
}

// Database functions
async function loadDatabaseImages() {
    showStatus('Loading database images...', 'loading');

    try {
        const response = await fetch('/api/images/');
        if (response.ok) {
            const images = await response.json();
            displayDatabaseImages(images);
        } else {
            showStatus('Failed to load database images', 'error');
        }
    } catch (error) {
        console.error('Error loading database:', error);
        showStatus('Failed to load database images', 'error');
    }
}

function displayDatabaseImages(images) {
    const statusContent = document.getElementById('statusContent');
    
    if (images.length === 0) {
        statusContent.innerHTML = `
            <div class="no-match">
                <i class="fas fa-database fa-2x" style="color: #cbd5e0; margin-bottom: 10px;"></i>
                <p>No images in database yet</p>
                <p style="font-size: 0.9rem; margin-top: 10px;">Upload a PDF to get started!</p>
            </div>
        `;
        return;
    }
    
    let imagesHTML = `
        <h3 style="margin-bottom: 20px; color: #4a5568;">
            <i class="fas fa-database"></i> Database Images (${images.length})
        </h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px;">
    `;
    
    images.forEach(image => {
        imagesHTML += `
            <div class="result-item" style="margin: 0;">
                <img src="/images/${image.image_path.split('/').pop()}" 
                     alt="${image.business_name}" 
                     style="width: 100%; height: 120px; object-fit: cover; border-radius: 8px; margin-bottom: 10px;">
                <h4 style="font-size: 1rem; margin-bottom: 5px;">${image.business_name || 'Unknown'}</h4>
                <p style="font-size: 0.8rem; color: #718096;">${image.pdf_filename}</p>
                <p style="font-size: 0.8rem; color: #718096;">Page ${image.page_number}</p>
                <p style="font-size: 0.8rem; color: #718096;">Type: ${image.image_type}</p>
            </div>
        `;
    });
    
    imagesHTML += `
        </div>
        <button class="btn" style="margin-top: 20px;" onclick="showStatus('Upload an image or use your camera to start matching', 'info')">
            <i class="fas fa-arrow-left"></i> Back to Matching
        </button>
    `;
    
    statusContent.innerHTML = imagesHTML;
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// DEX Content interaction functions
function openDEXContent(url, type) {
    console.log(`Opening DEX content: ${type} - ${url}`);
    
    if (type === 'ar') {
        // Open AR viewer in new window
        window.open(url, '_blank', 'width=800,height=600');
        showStatus('AR viewer opened in new window', 'success');
    } else if (type === 'video') {
        // Create video modal
        showVideoModal(url);
    } else if (type === 'webpage') {
        // Open webpage in new tab
        window.open(url, '_blank');
        showStatus('Webpage opened in new tab', 'success');
    }
}

function showVideoModal(videoUrl) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
    `;
    
    modal.innerHTML = `
        <div style="position: relative; max-width: 90%; max-height: 90%;">
            <button onclick="this.parentElement.parentElement.remove()" 
                    style="position: absolute; top: -40px; right: 0; background: #fff; border: none; 
                           border-radius: 50%; width: 30px; height: 30px; cursor: pointer; font-size: 16px;">×</button>
            <video controls autoplay style="width: 100%; height: auto; border-radius: 10px;">
                <source src="${videoUrl}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal on click outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

async function generateQRCode(qrUrl) {
    try {
        showStatus('Generating QR code...', 'loading');
        
        // Create a simple QR code using canvas (no external library needed)
        const qrCodeCanvas = document.createElement('canvas');
        const ctx = qrCodeCanvas.getContext('2d');
        qrCodeCanvas.width = 250;
        qrCodeCanvas.height = 250;
        
        // Fill background
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, 250, 250);
        
        // Create a simple QR-like pattern (for demo purposes)
        ctx.fillStyle = 'black';
        
        // Draw a simple grid pattern that looks like a QR code
        const gridSize = 10;
        for (let x = 0; x < 250; x += gridSize) {
            for (let y = 0; y < 250; y += gridSize) {
                // Create a pseudo-random pattern based on position
                if ((x + y) % (gridSize * 2) === 0 || 
                    (x % (gridSize * 3) === 0 && y % (gridSize * 3) === 0)) {
                    ctx.fillRect(x, y, gridSize, gridSize);
                }
            }
        }
        
        // Add some corner squares (like real QR codes)
        ctx.fillRect(0, 0, gridSize * 3, gridSize * 3);
        ctx.fillRect(250 - gridSize * 3, 0, gridSize * 3, gridSize * 3);
        ctx.fillRect(0, 250 - gridSize * 3, gridSize * 3, gridSize * 3);
        
        // Convert canvas to data URL
        const qrCodeImage = qrCodeCanvas.toDataURL();
        
        // Show the QR code modal
        showQRCodeModal({
            qr_code_image: qrCodeImage,
            qr_code_url: qrUrl,
            instructions: 'Scan this QR code to access the content'
        });
        
        showStatus('QR code generated successfully!', 'success');
        
    } catch (error) {
        console.error('QR code error:', error);
        showStatus('Error generating QR code', 'error');
    }
}

function showQRCodeModal(qrData) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
    `;
    
    modal.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 15px; text-align: center; max-width: 400px;">
            <h3 style="margin-bottom: 20px; color: #4a5568;">Scan QR Code</h3>
            ${qrData.qr_code_image ? `
                <img src="${qrData.qr_code_image}" alt="QR Code" style="width: 250px; height: 250px; margin-bottom: 15px;">
            ` : `
                <div style="width: 250px; height: 250px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px;">
                    <p>QR Code not available</p>
                </div>
            `}
            <p style="color: #718096; margin-bottom: 20px;">${qrData.instructions}</p>
            <div style="background: #f0f9ff; padding: 10px; border-radius: 8px; margin-bottom: 20px;">
                <code style="word-break: break-all; font-size: 12px;">${qrData.qr_code_url}</code>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" 
                    style="background: #4facfe; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer;">
                Close
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal on click outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// PDF Upload functionality
async function uploadPDF() {
    const pdfFileInput = document.getElementById('pdfFile');
    const businessName = document.getElementById('businessName').value;
    const businessReference = document.getElementById('businessReference').value;
    const tags = document.getElementById('tags').value;
    const imageType = document.getElementById('imageType').value;
    
    if (!pdfFileInput.files[0]) {
        showStatus('❌ Please select a PDF file', 'error');
        return;
    }
    
    if (!businessName) {
        showStatus('❌ Please enter a business name', 'error');
        return;
    }
    
    try {
        showStatus('🔄 Uploading and processing PDF...', 'loading');
        
        const formData = new FormData();
        formData.append('file', pdfFileInput.files[0]);
        formData.append('business_name', businessName);
        formData.append('business_reference', businessReference);
        formData.append('tags', tags);
        formData.append('image_type', imageType);
        
        const response = await fetch(`${API_BASE_URL}/upload-pdf/`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            showStatus(`✅ PDF processed successfully! Extracted ${result.extracted_images} images.`, 'success');
            
            // Clear the form
            pdfFileInput.value = '';
            document.getElementById('businessName').value = '';
            document.getElementById('businessReference').value = '';
            document.getElementById('tags').value = '';
            document.getElementById('imageType').value = 'logo';
            
            // Refresh the database
            await loadDatabaseImages();
        } else {
            const error = await response.json();
            showStatus(`❌ Upload failed: ${error.detail}`, 'error');
        }
    } catch (error) {
        console.error('PDF upload error:', error);
        showStatus('❌ Upload failed: Network error', 'error');
    }
}

// Add drag and drop functionality for both image and PDF uploads
document.addEventListener('DOMContentLoaded', function() {
    const imageFileInput = document.querySelector('.card:first-child .file-input');
    const pdfFileInput = document.querySelector('.card:last-child .file-input');
    
    // Image file drag and drop
    imageFileInput.addEventListener('dragover', function(e) {
        e.preventDefault();
        imageFileInput.style.borderColor = '#4facfe';
        imageFileInput.style.background = '#e0f2fe';
    });
    
    imageFileInput.addEventListener('dragleave', function(e) {
        e.preventDefault();
        imageFileInput.style.borderColor = '#4facfe';
        imageFileInput.style.background = '#f0f9ff';
    });
    
    imageFileInput.addEventListener('drop', function(e) {
        e.preventDefault();
        imageFileInput.style.borderColor = '#4facfe';
        imageFileInput.style.background = '#f0f9ff';
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
            document.getElementById('imageFile').files = files;
            uploadedImage = files[0];
            displayImagePreview(files[0]);
        } else {
            showStatus('Please select a valid image file', 'error');
        }
    });
    
    imageFileInput.addEventListener('click', function() {
        document.getElementById('imageFile').click();
    });
    
    // PDF file drag and drop
    pdfFileInput.addEventListener('dragover', function(e) {
        e.preventDefault();
        pdfFileInput.style.borderColor = '#4facfe';
        pdfFileInput.style.background = '#e0f2fe';
    });
    
    pdfFileInput.addEventListener('dragleave', function(e) {
        e.preventDefault();
        pdfFileInput.style.borderColor = '#4facfe';
        pdfFileInput.style.background = '#f0f9ff';
    });
    
    pdfFileInput.addEventListener('drop', function(e) {
        e.preventDefault();
        pdfFileInput.style.borderColor = '#4facfe';
        pdfFileInput.style.background = '#f0f9ff';
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type === 'application/pdf') {
            document.getElementById('pdfFile').files = files;
            showStatus(`PDF file "${files[0].name}" selected`, 'success');
        } else {
            showStatus('Please select a valid PDF file', 'error');
        }
    });
    
    pdfFileInput.addEventListener('click', function() {
        document.getElementById('pdfFile').click();
    });
}); 