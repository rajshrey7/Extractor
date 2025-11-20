/**
 * Confidence Overlay Module
 * Renders interactive, color-coded confidence zones over OCR processed images.
 * Supports SSE streaming, progressive rendering, hover tooltips, and click-to-correct.
 */

class ConfidenceOverlay {
    constructor(imageElement, canvasElement) {
        this.imageElement = imageElement;
        this.canvasElement = canvasElement;
        this.ctx = canvasElement.getContext('2d');
        this.regions = [];
        this.documentConfidence = 0;
        this.hoveredRegion = null;
        this.enabled = true;

        // Bind event handlers
        this.canvasElement.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvasElement.addEventListener('click', this.handleClick.bind(this));
        this.canvasElement.addEventListener('mouseleave', this.handleMouseLeave.bind(this));

        // Update canvas size when image loads
        if (this.imageElement.complete) {
            this.updateCanvasSize();
        } else {
            this.imageElement.addEventListener('load', () => this.updateCanvasSize());
        }

        // Handle window resize
        window.addEventListener('resize', () => this.updateCanvasSize());
    }

    updateCanvasSize() {
        const rect = this.imageElement.getBoundingClientRect();
        this.canvasElement.width = rect.width;
        this.canvasElement.height = rect.height;
        this.canvasElement.style.width = `${rect.width}px`;
        this.canvasElement.style.height = `${rect.height}px`;
        this.render();
    }

    connectSSE(image_id) {
        console.log(`Connecting to SSE stream for image: ${image_id}`);
        const url = `/api/ocr_stream?image_id=${image_id}`;
        const eventSource = new EventSource(url);

        eventSource.addEventListener('region', (event) => {
            try {
                const region = JSON.parse(event.data);
                console.log('Received region:', region);
                this.addRegion(region);
            } catch (e) {
                console.error('Error parsing region data:', e);
            }
        });

        eventSource.addEventListener('done', (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Stream complete:', data);
                this.documentConfidence = data.document_confidence;
                this.updateDocumentConfidenceDisplay();
                this.updateLowConfidenceCTA();
                eventSource.close();
            } catch (e) {
                console.error('Error parsing done event:', e);
                eventSource.close();
            }
        });

        eventSource.addEventListener('error', (event) => {
            console.error('SSE error:', event);
            if (event.data) {
                try {
                    const error = JSON.parse(event.data);
                    console.error('Error details:', error);
                } catch (e) {
                    console.error('Could not parse error data');
                }
            }
            eventSource.close();
        });

        return eventSource;
    }

    addRegion(region) {
        this.regions.push(region);
        this.renderRegion(region);
    }

    renderRegion(region) {
        if (!this.enabled) return;

        const color = this.getColorForConfidence(region.confidence);
        const box = region.box; // [x, y, w, h]

        // Get the actual displayed dimensions of the image
        const displayedWidth = this.imageElement.width || this.imageElement.clientWidth;
        const displayedHeight = this.imageElement.height || this.imageElement.clientHeight;

        // Calculate scale based on the original image dimensions to displayed dimensions
        const scaleX = displayedWidth / this.imageElement.naturalWidth;
        const scaleY = displayedHeight / this.imageElement.naturalHeight;

        const x = box[0] * scaleX;
        const y = box[1] * scaleY;
        const w = box[2] * scaleX;
        const h = box[3] * scaleY;

        // Draw filled rectangle with transparency
        this.ctx.fillStyle = color.fill;
        this.ctx.fillRect(x, y, w, h);

        // Draw border
        this.ctx.strokeStyle = color.stroke;
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(x, y, w, h);
    }

    render() {
        if (!this.enabled) {
            this.ctx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
            return;
        }

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);

        // Render all regions
        this.regions.forEach(region => this.renderRegion(region));

        // Highlight hovered region
        if (this.hoveredRegion) {
            this.highlightRegion(this.hoveredRegion);
        }
    }

    highlightRegion(region) {
        const box = region.box;
        const scaleX = this.canvasElement.width / this.imageElement.naturalWidth;
        const scaleY = this.canvasElement.height / this.imageElement.naturalHeight;

        const x = box[0] * scaleX;
        const y = box[1] * scaleY;
        const w = box[2] * scaleX;
        const h = box[3] * scaleY;

        // Draw highlighted border
        this.ctx.strokeStyle = '#FFFFFF';
        this.ctx.lineWidth = 3;
        this.ctx.strokeRect(x, y, w, h);

        // Increase opacity
        const color = this.getColorForConfidence(region.confidence);
        this.ctx.fillStyle = color.fillHover;
        this.ctx.fillRect(x, y, w, h);
    }

    getColorForConfidence(confidence) {
        if (confidence >= 0.85) {
            // Green - high confidence
            return {
                fill: 'rgba(0, 255, 0, 0.15)',
                fillHover: 'rgba(0, 255, 0, 0.3)',
                stroke: 'rgba(0, 200, 0, 0.8)'
            };
        } else if (confidence >= 0.6) {
            // Yellow - medium confidence
            return {
                fill: 'rgba(255, 200, 0, 0.2)',
                fillHover: 'rgba(255, 200, 0, 0.4)',
                stroke: 'rgba(220, 180, 0, 0.9)'
            };
        } else {
            // Red - low confidence
            return {
                fill: 'rgba(255, 0, 0, 0.25)',
                fillHover: 'rgba(255, 0, 0, 0.45)',
                stroke: 'rgba(200, 0, 0, 1)'
            };
        }
    }

    handleMouseMove(event) {
        const rect = this.canvasElement.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        // Find region under mouse
        const region = this.getRegionAtPoint(mouseX, mouseY);

        if (region !== this.hoveredRegion) {
            this.hoveredRegion = region;
            this.render();

            if (region) {
                this.showTooltip(region, event.clientX, event.clientY);
                this.canvasElement.style.cursor = 'pointer';
            } else {
                this.hideTooltip();
                this.canvasElement.style.cursor = 'default';
            }
        }
    }

    handleClick(event) {
        if (!this.hoveredRegion) return;

        // Open correction modal with pre-filled text
        this.openCorrectionModal(this.hoveredRegion);
    }

    handleMouseLeave() {
        this.hoveredRegion = null;
        this.hideTooltip();
        this.render();
    }

    getRegionAtPoint(x, y) {
        // Get the actual displayed dimensions of the image
        const displayedWidth = this.imageElement.width || this.imageElement.clientWidth;
        const displayedHeight = this.imageElement.height || this.imageElement.clientHeight;

        const scaleX = displayedWidth / this.imageElement.naturalWidth;
        const scaleY = displayedHeight / this.imageElement.naturalHeight;

        // Check regions in reverse order (last rendered on top)
        for (let i = this.regions.length - 1; i >= 0; i--) {
            const region = this.regions[i];
            const box = region.box;

            const rx = box[0] * scaleX;
            const ry = box[1] * scaleY;
            const rw = box[2] * scaleX;
            const rh = box[3] * scaleY;

            if (x >= rx && x <= rx + rw && y >= ry && y <= ry + rh) {
                return region;
            }
        }

        return null;
    }

    showTooltip(region, x, y) {
        let tooltip = document.getElementById('confidenceTooltip');

        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'confidenceTooltip';
            tooltip.className = 'confidence-tooltip';
            document.body.appendChild(tooltip);
        }

        const conf = Math.round(region.confidence * 100);
        const ocrConf = Math.round(region.ocr_confidence * 100);

        tooltip.innerHTML = `
            <div class="tooltip-header">
                <strong>${region.text || '(no text)'}</strong>
            </div>
            <div class="tooltip-body">
                <div class="tooltip-row">
                    <span>Overall Confidence:</span>
                    <span class="tooltip-value ${this.getConfidenceClass(region.confidence)}">${conf}%</span>
                </div>
                <div class="tooltip-row">
                    <span>OCR Confidence:</span>
                    <span class="tooltip-value">${ocrConf}%</span>
                </div>
                <div class="tooltip-row">
                    <span>Blur Score:</span>
                    <span class="tooltip-value">${region.blur_score}</span>
                </div>
                <div class="tooltip-row">
                    <span>Lighting:</span>
                    <span class="tooltip-value">${region.lighting_score}</span>
                </div>
                ${region.suggestions && region.suggestions.length > 0 ? `
                    <div class="tooltip-suggestions">
                        <span>Suggestions:</span>
                        <span class="tooltip-value">${region.suggestions.join(', ')}</span>
                    </div>
                ` : ''}
            </div>
            <div class="tooltip-footer">
                <small>Click to correct</small>
            </div>
        `;

        tooltip.style.display = 'block';
        tooltip.style.left = `${x + 10}px`;
        tooltip.style.top = `${y + 10}px`;
    }

    hideTooltip() {
        const tooltip = document.getElementById('confidenceTooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.85) return 'conf-high';
        if (confidence >= 0.6) return 'conf-medium';
        return 'conf-low';
    }

    openCorrectionModal(region) {
        // Trigger the existing manual correction modal
        // Assuming it's the same modal used in the Extract Text tab
        // We'll dispatch a custom event that the main app can listen to
        const event = new CustomEvent('regionCorrection', {
            detail: {
                region_id: region.region_id,
                text: region.text,
                confidence: region.confidence
            }
        });
        window.dispatchEvent(event);
    }

    updateRegion(region_id, newData) {
        const index = this.regions.findIndex(r => r.region_id === region_id);
        if (index !== -1) {
            Object.assign(this.regions[index], newData);
            this.render();
        }
    }

    updateDocumentConfidenceDisplay() {
        const docConfElement = document.getElementById('docConfidence');
        if (docConfElement) {
            const percentage = Math.round(this.documentConfidence * 100);
            const className = this.getConfidenceClass(this.documentConfidence);
            docConfElement.innerHTML = `
                Overall Document Confidence: 
                <span class="doc-conf-value ${className}">${percentage}%</span>
            `;
        }
    }

    updateLowConfidenceCTA() {
        const lowConfRegions = this.regions.filter(r => r.confidence < 0.6);
        const ctaElement = document.getElementById('lowConfidenceCTA');

        if (ctaElement) {
            if (lowConfRegions.length > 0) {
                ctaElement.style.display = 'block';
                ctaElement.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    ${lowConfRegions.length} region(s) with low confidence - click regions to correct
                `;
            } else {
                ctaElement.style.display = 'none';
            }
        }
    }

    toggle(enabled) {
        this.enabled = enabled;
        this.render();
    }

    clear() {
        this.regions = [];
        this.documentConfidence = 0;
        this.hoveredRegion = null;
        this.render();
    }
}

// Export for use in main application
window.ConfidenceOverlay = ConfidenceOverlay;
