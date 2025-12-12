import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

/**
 * Service to share OCR extracted data between components
 * Allows OCR integration component to store data that demographic form can use
 */
@Injectable({
    providedIn: 'root'
})
export class OcrDataService {
    // Store extracted OCR data
    private extractedDataSubject = new BehaviorSubject<any>(null);
    public extractedData$ = this.extractedDataSubject.asObservable();

    // Flag to indicate if OCR data is available
    private hasDataSubject = new BehaviorSubject<boolean>(false);
    public hasData$ = this.hasDataSubject.asObservable();

    constructor() {
        console.log('OcrDataService initialized');
    }

    /**
     * Store OCR extracted data
     */
    setExtractedData(data: any): void {
        console.log('OcrDataService: Storing extracted data', data);
        this.extractedDataSubject.next(data);
        this.hasDataSubject.next(!!data && Object.keys(data).length > 0);
    }

    /**
     * Get current OCR data
     */
    getExtractedData(): any {
        return this.extractedDataSubject.value;
    }

    /**
     * Clear stored OCR data
     */
    clearData(): void {
        this.extractedDataSubject.next(null);
        this.hasDataSubject.next(false);
    }

    /**
     * Get a specific field value from OCR data
     */
    getFieldValue(fieldName: string): string | null {
        const data = this.extractedDataSubject.value;
        if (!data) return null;

        // Try different field name formats
        const possibleKeys = [
            fieldName,
            fieldName.toLowerCase(),
            fieldName.toUpperCase(),
            this.camelToTitle(fieldName),
            this.titleToCamel(fieldName)
        ];

        for (const key of possibleKeys) {
            if (data[key]) {
                // Handle both simple values and {value, confidence} objects
                if (typeof data[key] === 'object' && data[key].value) {
                    return data[key].value;
                }
                return data[key];
            }
        }

        return null;
    }

    /**
     * Map OCR fields to MOSIP form fields
     */
    getMappedFormData(): any {
        const data = this.extractedDataSubject.value;
        if (!data) return {};

        const mappedData: any = {};

        // Field mapping from OCR to MOSIP - comprehensive list
        const fieldMap: { [key: string]: string } = {
            // Name fields
            'fullName': 'fullName',
            'Full Name': 'fullName',
            'Name': 'fullName',
            'name': 'fullName',
            'Applicant Name': 'fullName',
            'Candidate Name': 'fullName',

            // DOB
            'dateOfBirth': 'dateOfBirth',
            'Date of Birth': 'dateOfBirth',
            'DOB': 'dateOfBirth',
            'dob': 'dateOfBirth',
            'Birth Date': 'dateOfBirth',
            'Date Of Birth': 'dateOfBirth',

            // Gender
            'gender': 'gender',
            'Gender': 'gender',
            'Sex': 'gender',
            'sex': 'gender',

            // Phone
            'phone': 'phone',
            'Phone': 'phone',
            'Mobile': 'phone',
            'mobile': 'phone',
            'Contact': 'phone',
            'Phone No': 'phone',
            'Mobile No': 'phone',

            // Email
            'email': 'email',
            'Email': 'email',
            'E-mail': 'email',
            'Email ID': 'email',

            // Address
            'address': 'addressLine1',
            'Address': 'addressLine1',
            'addressLine1': 'addressLine1',
            'Permanent Address': 'addressLine1',
            'Present Address': 'addressLine1',
            'Residence': 'addressLine1',

            // Father name
            'fatherName': 'fatherName',
            'Father Name': 'fatherName',
            'Father': 'fatherName',
            'father': 'fatherName',
            'Father\'s Name': 'fatherName',

            // Mother name
            'motherName': 'motherName',
            'Mother Name': 'motherName',
            'Mother': 'motherName',
            'mother': 'motherName',
            'Mother\'s Name': 'motherName',

            // District/City
            'district': 'city',
            'District': 'city',
            'city': 'city',
            'City': 'city',
            'Town': 'city',

            // State/Region
            'state': 'region',
            'State': 'region',
            'region': 'region',
            'Region': 'region',
            'Province': 'province',
            'province': 'province',

            // Postal Code
            'postalCode': 'postalCode',
            'Postal Code': 'postalCode',
            'Pin Code': 'postalCode',
            'PIN Code': 'postalCode',
            'pincode': 'postalCode',
            'PIN': 'postalCode',
            'Zip Code': 'postalCode',

            // Place of Birth
            'Place of Birth': 'placeOfBirth',
            'placeOfBirth': 'placeOfBirth',
            'Birth Place': 'placeOfBirth',

            // Registration/Certificate Numbers (for documents)
            'Registration No': 'referenceIdentityNumber',
            'Certificate No': 'referenceIdentityNumber',
            'Aadhaar': 'referenceIdentityNumber',
            'Aadhaar No': 'referenceIdentityNumber',
            'PAN': 'referenceIdentityNumber',
            'Passport No': 'referenceIdentityNumber'
        };

        for (const [ocrKey, mosipKey] of Object.entries(fieldMap)) {
            if (data[ocrKey]) {
                const value = typeof data[ocrKey] === 'object' && data[ocrKey].value
                    ? data[ocrKey].value
                    : data[ocrKey];
                mappedData[mosipKey] = value;
            }
        }

        return mappedData;
    }

    private camelToTitle(str: string): string {
        return str.replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase()).trim();
    }

    private titleToCamel(str: string): string {
        return str.replace(/(?:^\w|[A-Z]|\b\w)/g, (word, index) =>
            index === 0 ? word.toLowerCase() : word.toUpperCase()
        ).replace(/\s+/g, '');
    }
}
