import { Component, OnInit, Output, EventEmitter, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { AppConfigService } from 'src/app/app-config.service';
import { OcrDataService } from 'src/app/core/services/ocr-data.service';

@Component({
    selector: 'app-ocr-integration',
    templateUrl: './ocr-integration.component.html',
    styleUrls: ['./ocr-integration.component.css']
})
export class OcrIntegrationComponent implements OnInit, OnDestroy {
    @Output() ocrDataExtracted = new EventEmitter<any>();
    @ViewChild('ocrFrame') ocrFrame: ElementRef;

    // OCR page URL (your standalone index.html served by Python)
    ocrPageUrl: SafeResourceUrl;

    // Last received data
    lastExtractedData: any = null;

    // Message listener
    private messageListener: any;

    constructor(
        private sanitizer: DomSanitizer,
        private configService: AppConfigService,
        private ocrDataService: OcrDataService
    ) {
        // Get the OCR page URL from config or use default
        const config = this.configService.getConfig();
        const baseUrl = config && config['BASE_URL']
            ? config['BASE_URL'].replace(/\/$/, '')
            : 'http://localhost:8001';

        // The standalone OCR page is served at the root of the Python server
        this.ocrPageUrl = this.sanitizer.bypassSecurityTrustResourceUrl(baseUrl);
    }

    ngOnInit() {
        console.log('OCR Integration Component initialized (embedded mode)');

        // Set up message listener to receive data from iframe
        this.messageListener = this.handleMessage.bind(this);
        window.addEventListener('message', this.messageListener);
    }

    ngOnDestroy() {
        // Clean up message listener
        if (this.messageListener) {
            window.removeEventListener('message', this.messageListener);
        }
    }

    onIframeLoad() {
        console.log('OCR iframe loaded successfully');
    }

    // Handle messages from the embedded OCR page
    handleMessage(event: MessageEvent) {
        // Accept messages from our OCR server
        if (event.origin !== 'http://localhost:8001' &&
            event.origin !== 'http://127.0.0.1:8001') {
            return;
        }

        // Check if it's OCR data
        if (event.data && event.data.type === 'OCR_DATA_EXTRACTED') {
            console.log('Received OCR data from embedded scanner:', event.data.payload);
            this.lastExtractedData = event.data.payload;

            // Store in shared service for demographic form to use
            const extractedFields = event.data.payload.extracted_fields || event.data.payload;
            this.ocrDataService.setExtractedData(extractedFields);

            // Also emit event
            this.applyExtractedData();
        }
    }

    // Apply extracted data to MOSIP form
    applyExtractedData() {
        if (!this.lastExtractedData) {
            return;
        }

        const extractedFields = this.lastExtractedData.extracted_fields || this.lastExtractedData;

        // Store in service
        this.ocrDataService.setExtractedData(extractedFields);

        // Get mapped data for MOSIP form
        const mappedData = this.ocrDataService.getMappedFormData();

        console.log('Applying OCR data to form:', mappedData);
        this.ocrDataExtracted.emit(mappedData);
    }
}
