import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AppConfigService } from 'src/app/app-config.service';

export interface OcrFieldData {
    value: string;
    confidence: number;
}

export interface OcrExtractedData {
    [fieldName: string]: OcrFieldData;
}

export interface OcrResponse {
    success: boolean;
    extracted_data: OcrExtractedData;
    processing_time?: number;
    error?: string;
}

@Injectable({
    providedIn: 'root'
})
export class OcrService {
    private ocrApiUrl: string;

    constructor(
        private http: HttpClient,
        private configService: AppConfigService
    ) {
        const config = this.configService.getConfig();
        this.ocrApiUrl = config && config['OCR_API_URL'] ? config['OCR_API_URL'] : '/proxyapi/ocr';
    }

    /**
     * Extract data from uploaded document
     * @param file - Document file (PDF/Image)
     * @returns Observable with OCR results
     */
    extractData(file: File): Observable<OcrResponse> {
        const formData = new FormData();
        formData.append('file', file, file.name);

        const headers = new HttpHeaders();
        // Let browser set Content-Type for multipart/form-data

        return this.http.post<OcrResponse>(`${this.ocrApiUrl}/extract`, formData, {
            headers: headers
        });
    }

    /**
     * Get extraction confidence threshold
     */
    getConfidenceThreshold(): number {
        return 0.7; // 70% confidence minimum
    }
}
