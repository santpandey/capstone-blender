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
            
            if (data.success && data.model_url) {
                // Model generation completed
                const modelViewer = document.getElementById('modelViewer');
                modelViewer.src = data.model_url;
                currentModelUrl = data.model_url;
                
                toggleClass('loading', 'show', false);
                showElement('modelViewer', true);
                toggleClass('downloadBtn', 'show', true);
                updateStatus('✅ 3D asset generated successfully!', 'success');
                
            } else if (data.status === 'processing') {
                // Still processing, poll for updates
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
        
        if (data.status === 'completed' && data.model_url) {
            const modelViewer = document.getElementById('modelViewer');
            modelViewer.src = data.model_url;
            currentModelUrl = data.model_url;
            
            toggleClass('loading', 'show', false);
            showElement('modelViewer', true);
            toggleClass('downloadBtn', 'show', true);
            updateStatus('✅ 3D asset generated successfully!', 'success');
            
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
    }
}

// Download the generated model
function downloadModel() {
    if (!currentModelUrl) {
        updateStatus('❌ No model available for download', 'error');
        return;
    }
    
    // Create download link
    const link = document.createElement('a');
    link.href = currentModelUrl;
    link.download = 'generated_model.glb';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    updateStatus('📥 Model downloaded successfully!', 'success');
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
});
