// Camera handling logic

let videoStream = null;
let imageCapture = null;

// Initialize camera
async function initCamera() {
    const modal = document.getElementById('cameraModal');
    const video = document.getElementById('cameraVideo');
    const canvas = document.getElementById('cameraCanvas');
    const preview = document.getElementById('capturedPreview');
    const captureBtn = document.getElementById('captureBtn');
    const retakeBtn = document.getElementById('retakeBtn');
    const useBtn = document.getElementById('useImageBtn');
    const errorMsg = document.getElementById('cameraError');

    // Reset UI
    modal.style.display = 'flex';
    video.style.display = 'block';
    canvas.style.display = 'none';
    preview.style.display = 'none';
    captureBtn.style.display = 'inline-block';
    retakeBtn.style.display = 'none';
    useBtn.style.display = 'none';
    errorMsg.style.display = 'none';

    try {
        // Request camera access
        // Prefer rear camera on mobile (environment)
        const constraints = {
            video: {
                facingMode: 'environment',
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            }
        };

        videoStream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = videoStream;

        // Wait for video to be ready to play
        video.onloadedmetadata = () => {
            video.play();
        };

    } catch (err) {
        console.error("Camera error:", err);
        errorMsg.textContent = "Could not access camera. Please allow permissions or use file upload.";
        errorMsg.style.display = 'block';
        captureBtn.style.display = 'none';
    }
}

// Capture image from video stream
function captureImage() {
    const video = document.getElementById('cameraVideo');
    const canvas = document.getElementById('cameraCanvas');
    const preview = document.getElementById('capturedPreview');
    const captureBtn = document.getElementById('captureBtn');
    const retakeBtn = document.getElementById('retakeBtn');
    const useBtn = document.getElementById('useImageBtn');

    if (!videoStream) return;

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame to canvas
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Show preview
    preview.src = canvas.toDataURL('image/jpeg', 0.9);

    // Update UI
    video.style.display = 'none';
    preview.style.display = 'block';
    captureBtn.style.display = 'none';
    retakeBtn.style.display = 'inline-block';
    useBtn.style.display = 'inline-block';
}

// Retake image (go back to video stream)
function retakeImage() {
    const video = document.getElementById('cameraVideo');
    const preview = document.getElementById('capturedPreview');
    const captureBtn = document.getElementById('captureBtn');
    const retakeBtn = document.getElementById('retakeBtn');
    const useBtn = document.getElementById('useImageBtn');

    video.style.display = 'block';
    preview.style.display = 'none';
    captureBtn.style.display = 'inline-block';
    retakeBtn.style.display = 'none';
    useBtn.style.display = 'none';
}

// Close camera modal and stop stream
function closeCameraModal() {
    const modal = document.getElementById('cameraModal');
    modal.style.display = 'none';

    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
}

// Upload captured image
async function uploadCapturedImage() {
    const canvas = document.getElementById('cameraCanvas');
    const useOpenAI = document.getElementById('useOpenAI'); // Re-use existing checkbox if present

    // Convert canvas to blob
    canvas.toBlob(async (blob) => {
        if (!blob) {
            alert("Failed to capture image");
            return;
        }

        // Create FormData
        const formData = new FormData();
        // Generate a filename
        const timestamp = new Date().toISOString().replace(/[-:.]/g, "");
        formData.append('image', blob, `camera_${timestamp}.jpg`);

        // Add other parameters
        if (useOpenAI && useOpenAI.checked) {
            formData.append('use_openai', 'true');
        }

        // Close modal
        closeCameraModal();

        // Show loading on main page
        document.getElementById('loading').classList.add('show');
        document.getElementById('results').classList.remove('show');

        // Use existing hideAlert if available
        if (typeof hideAlert === 'function') hideAlert('alert');

        try {
            const response = await fetch('/api/camera_upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();

            // Reuse existing processImage success logic by simulating it
            // We can call the same logic or just manually trigger the UI updates
            // Since processImage logic is inside the 'app' Alpine component or global scope, 
            // we might need to bridge it. 

            // However, looking at index.html, processImage is a global function? 
            // No, it's inside `function app() { ... }` but also defined as `async function processImage()` in global scope?
            // Let's check index.html again.
            // It seems `processImage` is defined inside `script` tag but NOT inside `app()` object.
            // Wait, lines 799 `function app() {` starts the Alpine component.
            // Line 952 `async function processImage() {` is OUTSIDE `app()`.
            // So we can reuse the logic or just call a handler.

            // Actually, `processImage` in index.html handles the file input. 
            // We need a similar function to handle the response data directly.

            // Let's create a helper function in index.html to handle the success data, 
            // or we can just duplicate the success handling here if we want to keep it isolated,
            // BUT the requirement says "reuse current OCR & verification pipeline".
            // The backend reuses it. The frontend needs to display the results.

            // The easiest way is to call a global function `handleUploadSuccess(data)` 
            // which we will refactor out in index.html, OR just copy the success logic.
            // Given "Do NOT change any existing features or workflows", refactoring might be risky if not careful.
            // But `processImage` does a lot of UI work.

            // Let's look at `processImage` in `index.html` again.
            // It calls `/api/upload` then handles `data`.
            // We can modify `processImage` to accept `data` directly or create a shared `handleResponse(data)` function.

            // For now, I will implement `handleCameraResponse(data)` in this file that mimics the success logic of `processImage`.
            // Or better, I will expose a function in `index.html` that `camera.js` can call.

            if (window.handleUploadSuccess) {
                window.handleUploadSuccess(data);
            } else {
                console.error("handleUploadSuccess not found. Please update index.html");
                alert("Image uploaded but could not display results. Check console.");
            }

        } catch (error) {
            console.error("Upload error:", error);
            if (typeof showAlert === 'function') {
                showAlert('alert', "Error uploading camera image: " + error.message, 'error');
            } else {
                alert("Error: " + error.message);
            }
        } finally {
            document.getElementById('loading').classList.remove('show');
        }

    }, 'image/jpeg', 0.9);
}
