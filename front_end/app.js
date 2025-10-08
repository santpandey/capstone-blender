// Frontend JavaScript for 3D Asset Generator
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : '/api'; // Use nginx proxy in production

let currentModelUrl = null;

// Set example prompt when clicked
function setPrompt(element) {
    document.getElementById('prompt').value = element.textContent;
}

// Update status display
function updateStatus(message, type = 'idle') {
    const statusElement = document.getElementById('status');
    statusElement.textContent = message;
    statusElement.className = `status ${type}`;
}

// Show/hide UI elements
function showElement(id, show = true) {
    const element = document.getElementById(id);
    if (show) {
        element.style.display = 'block';
    } else {
        element.style.display = 'none';
    }
}

function toggleClass(id, className, add = true) {
    const element = document.getElementById(id);
    if (add) {
        element.classList.add(className);
    } else {
        element.classList.remove(className);
    }
}

// Main function to generate 3D asset
async function generateAsset() {
    const prompt = document.getElementById('prompt').value.trim();
    
    if (!prompt) {
        updateStatus('Please enter a description for your 3D asset', 'error');
        return;
    }
    
    // Disable submit button and show loading
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.disabled = true;
    generateBtn.textContent = '⏳ Generating...';
    
    // Update UI state
    updateStatus('🧠 Processing your request...', 'processing');
    showElement('placeholder', false);
    showElement('modelViewer', false);
    toggleClass('loading', 'show', true);
    toggleClass('downloadBtn', 'show', false);
    
    try {
        // Call backend API
        const response = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                style_preferences: {
                    quality: 'high',
                    style: 'realistic'
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Check if response is a GLB file
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/octet-stream')) {
            // Handle GLB file response
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            // Update model viewer
            const modelViewer = document.getElementById('modelViewer');
            modelViewer.src = url;
            currentModelUrl = url;
            
            // Update UI
            toggleClass('loading', 'show', false);
            showElement('modelViewer', true);
            toggleClass('downloadBtn', 'show', true);
            updateStatus('✅ 3D asset generated successfully!', 'success');
            
        } else {
            // Handle JSON response with status updates
            const data = await response.json();
            
            if (data.success && data.job_id) {
                // Job started successfully, begin polling
                updateStatus('🔄 ' + (data.message || 'Generating 3D model...'), 'processing');
                setTimeout(() => pollStatus(data.job_id), 2000);
                
            } else {
                throw new Error(data.message || 'Generation failed');
            }
        }
        
    } catch (error) {
        console.error('Error generating asset:', error);
        updateStatus(`❌ Error: ${error.message}`, 'error');
        
        // Reset UI
        toggleClass('loading', 'show', false);
        showElement('placeholder', true);
        
    } finally {
        // Re-enable submit button
        generateBtn.disabled = false;
        generateBtn.textContent = '🚀 Generate 3D Asset';
    }
}

// Poll for generation status (for async processing)
async function pollStatus(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/status/${jobId}`);
        const data = await response.json();
        
        if (data.status === 'completed') {
            // Check if we have a model_url (docker mode) or just script generation (local mode)
            if (data.model_url) {
                // Build full URL for the model
                const fullModelUrl = data.model_url.startsWith('http') 
                    ? data.model_url 
                    : `${API_BASE_URL}${data.model_url}`;
                
                // Docker mode - show 3D viewer
                const modelViewer = document.getElementById('modelViewer');
                modelViewer.src = fullModelUrl;
                currentModelUrl = fullModelUrl;
                
                toggleClass('loading', 'show', false);
                showElement('modelViewer', true);
                toggleClass('downloadBtn', 'show', true);
                updateStatus('✅ 3D asset generated successfully!', 'success');
            } else {
                // Local mode - script generated but no GLB
                toggleClass('loading', 'show', false);
                showElement('placeholder', true);
                updateStatus('✅ Script generated! ' + data.message, 'success');
            }
            
            // Re-enable button in both cases
            const generateBtn = document.getElementById('generateBtn');
            generateBtn.disabled = false;
            generateBtn.textContent = '🚀 Generate 3D Asset';
            
        } else if (data.status === 'processing') {
            updateStatus('🔄 ' + (data.message || 'Still generating...'), 'processing');
            setTimeout(() => pollStatus(jobId), 2000);
            
        } else if (data.status === 'failed') {
            throw new Error(data.message || 'Generation failed');
        }
        
    } catch (error) {
        console.error('Error polling status:', error);
        updateStatus(`❌ Error: ${error.message}`, 'error');
        toggleClass('loading', 'show', false);
        showElement('placeholder', true);
        
        // Re-enable button on error
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = false;
        generateBtn.textContent = '🚀 Generate 3D Asset';
    }
}

// Download the generated model and open in viewer
async function downloadModel() {
    if (!currentModelUrl) {
        updateStatus('❌ No model available for download', 'error');
        return;
    }
    
    try {
        // Fetch the model as blob
        const response = await fetch(currentModelUrl);
        if (!response.ok) throw new Error('Failed to fetch model');
        
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        
        // 1. Download the file
        const downloadLink = document.createElement('a');
        downloadLink.href = blobUrl;
        downloadLink.download = 'generated_model.glb';
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        
        // 2. Open in new tab for viewing
        // Store blob data in localStorage for the viewer page
        const modelData = {
            blob: blobUrl,
            jobId: currentModelUrl.split('/').pop().replace('.glb', '') || 'generated_model',
            timestamp: Date.now()
        };
        
        // Open viewer in new tab
        const viewerWindow = window.open('viewer.html', '_blank');
        
        // Wait a bit for the viewer window to load, then pass the blob
        setTimeout(() => {
            try {
                if (viewerWindow && !viewerWindow.closed) {
                    // Try to directly pass the blob via postMessage
                    viewerWindow.postMessage({
                        type: 'MODEL_DATA',
                        blobUrl: blobUrl,
                        jobId: modelData.jobId
                    }, '*');
                }
            } catch (e) {
                console.log('Could not post message to viewer:', e);
            }
        }, 1000);
        
        updateStatus('📥 Model downloaded and opened in viewer!', 'success');
        
        // Clean up the blob URL after a delay
        setTimeout(() => URL.revokeObjectURL(blobUrl), 60000);
        
    } catch (error) {
        console.error('Error downloading model:', error);
        updateStatus(`❌ Download failed: ${error.message}`, 'error');
    }
}

// Handle Enter key in textarea
document.getElementById('prompt').addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && event.ctrlKey) {
        generateAsset();
    }
});

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    updateStatus('Ready to generate your 3D asset', 'idle');
    
    // Attach event listeners
    const generateBtn = document.getElementById('generateBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', generateAsset);
    }
    
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadModel);
    }
});
