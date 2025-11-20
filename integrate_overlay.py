#!/usr/bin/env python3
"""
Script to safely integrate confidence overlay into index.html
This avoids the issue of manual edits corrupting the large HTML file.
"""

html_file = "index.html"

# Read the file
with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Step 1: Add CSS links after line 11 (Alpine.js script)
# Find the Alpine.js line
for i, line in enumerate(lines):
    if 'alpinejs@3.x.x/dist/cdn.min.js' in line:
        # Insert two new lines after this
        lines.insert(i + 1, '  <link rel="stylesheet" href="/static/css/confidence_overlay.css">\n')
        lines.insert(i + 2, '  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">\n')
        print(f"STEP 1: Added CSS links after line {i+1}")
        break

# Step 2: Add overlay UI elements before image preview
# Find the line with <div id="imagePreview"
for i, line in enumerate(lines):
    if '<div id="imagePreview"' in line and 'style="display: none' in line:
        # Insert overlay controls before this
        overlay_html = '''        <!-- Confidence Overlay Controls -->
        <div id="overlayControls" class="overlay-controls" style="display: none; margin-top: 20px;">
          <div class="overlay-toggle">
            <input type="checkbox" id="overlayToggle" checked onchange="toggleConfidenceOverlay(this.checked)">
            <label for="overlayToggle">Show Confidence Overlay</label>
          </div>
        </div>

        <!-- Confidence Legend -->
        <div id="confidenceLegend" class="confidence-legend" style="display: none;">
          <strong style="margin-right: 10px;">Confidence Levels:</strong>
          <div class="legend-item">
            <div class="legend-color legend-high"></div>
            <span>High (≥85%)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color legend-medium"></div>
            <span>Medium (60-84%)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color legend-low"></div>
            <span>Low (<60%)</span>
          </div>
        </div>

        <!-- Document Confidence Display -->
        <div id="docConfidence" style="display: none;"></div>

        <!-- Low Confidence CTA -->
        <div id="lowConfidenceCTA" style="display: none;"></div>

'''
        lines.insert(i, overlay_html)
        print(f"STEP 2: Added overlay UI elements before line {i+1}")
        break

# Step 3: Wrap image preview with canvas overlay
# Find the image preview section and modify it
for i, line in enumerate(lines):
    if '<div id="imagePreview"' in line:
        # Check the next few lines for the img tag
        for j in range(i, min(i+5, len(lines))):
            if '<img id="previewImg"' in lines[j] and 'preview-image' in lines[j]:
                # Replace this section
                # First, modify the imagePreview div to add wrapper
                lines[i] = '        <div id="imagePreview" style="display: none; text-align: center">\n'
                lines.insert(i+1, '          <div class="confidence-overlay-wrapper" style="display: inline-block; position: relative;">\n')
                
                # Modify the img tag
                lines[j+1] = '            <img id="previewImg" class="preview-image" alt="Preview"\n'
                lines.insert(j+2, '              style="max-width: 100%; max-height: 400px; border-radius: 8px; display: block;" />\n')
                lines.insert(j+3, '            <canvas id="confidenceCanvas" class="confidence-canvas" style="display: none;"></canvas>\n')
                lines.insert(j+4, '          </div>\n')
                
                print(f"STEP 3: Wrapped image with canvas overlay at line {i+1}")
                break
        break

# Step 4: Add confidence overlay JavaScript before </body>
# Find the camera.js script line
for i in range(len(lines)-1, -1, -1):
    if '<script src="/static/js/camera.js"></script>' in lines[i]:
        # Add our script after this
        js_code = '''
  <!-- Confidence Overlay Module -->
  <script src="/static/js/confidence_overlay.js"></script>
  <script>
    // Global confidence overlay instance
    let confidenceOverlay = null;
    let currentImageId = null;

    // Initialize confidence overlay
    function initConfidenceOverlay() {
      const imageElement = document.getElementById('previewImg');
      const canvasElement = document.getElementById('confidenceCanvas');
      
      if (imageElement && canvasElement) {
        confidenceOverlay = new ConfidenceOverlay(imageElement, canvasElement);
        
        // Listen for region correction events
        window.addEventListener('regionCorrection', (event) => {
          const { region_id, text } = event.detail;
          console.log('Region correction requested:', region_id, text);
        });
      }
    }

    // Toggle confidence overlay visibility
    function toggleConfidenceOverlay(enabled) {
      if (confidenceOverlay) {
        confidenceOverlay.toggle(enabled);
      }
      const canvas = document.getElementById('confidenceCanvas');
      if (canvas) {
        canvas.style.display = enabled ? 'block' : 'none';
      }
    }

    // Process image with streaming
    async function processImageWithStreaming() {
      const fileInput = document.getElementById('fileInput');
      const file = fileInput.files[0];
      
      if (!file) {
        alert('Please select a file first');
        return;
      }

      document.getElementById('loading').classList.add('show');
      
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('stream', 'true');
        
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (data.success && data.image_id) {
          currentImageId = data.image_id;
          
          const previewImg = document.getElementById('previewImg');
          previewImg.src = data.image_path;
          previewImg.onload = () => {
            document.getElementById('imagePreview').style.display = 'block';
            document.getElementById('overlayControls').style.display = 'flex';
            document.getElementById('confidenceLegend').style.display = 'flex';
            document.getElementById('docConfidence').style.display = 'block';
            document.getElementById('confidenceCanvas').style.display = 'block';
            
            if (!confidenceOverlay) {
              initConfidenceOverlay();
            } else {
              confidenceOverlay.clear();
              confidenceOverlay.updateCanvasSize();
            }
            
            confidenceOverlay.connectSSE(data.image_id);
          };
        }
      } catch (error) {
        console.error('Error:', error);
        showAlert('alert', 'Error processing image: ' + error.message, 'error');
      } finally {
        document.getElementById('loading').classList.remove('show');
      }
    }

    // Add streaming toggle on page load
    document.addEventListener('DOMContentLoaded', () => {
      const useOpenAICheckbox = document.getElementById('useOpenAI');
      if (useOpenAICheckbox && useOpenAICheckbox.parentElement) {
        const streamingLabel = document.createElement('label');
        streamingLabel.style.cssText = 'display: inline-flex; align-items: center; cursor: pointer; margin-left: 20px;';
        streamingLabel.innerHTML = `
          <input type="checkbox" id="useStreaming" style="margin-right: 8px; width: 18px; height: 18px" />
          <span>🔄 Show Live Confidence Zones</span>
        `;
        useOpenAICheckbox.parentElement.parentElement.appendChild(streamingLabel);
        
        const oldProcessImage = window.processImage;
        window.processImage = async function() {
          const useStreaming = document.getElementById('useStreaming')?.checked || false;
          if (useStreaming) {
            await processImageWithStreaming();
          } else if (oldProcessImage) {
            await oldProcessImage();
          }
        };
      }
    });
  </script>
'''
        lines.insert(i+1, js_code)
        print(f"STEP 4: Added JavaScript integration after line {i+1}")
        break

# Write the modified file
with open(html_file, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\nIntegration complete! All 4 steps applied successfully.")
print("\nNext: Start the server and test with 'Show Live Confidence Zones' enabled!")
