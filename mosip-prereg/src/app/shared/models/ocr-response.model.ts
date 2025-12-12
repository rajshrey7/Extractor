export interface OcrFieldData {
    value: string;
    confidence: number;
}

export interface OcrExtractedData {
    [fieldName: string]: OcrFieldData;
}

export interface OcrResponseModel {
    success: boolean;
    extracted_data: OcrExtractedData;
    processing_time?: number;
    error?: string;
}

// Field mapping between OCR and MOSIP
export const OCR_TO_MOSIP_FIELD_MAP = {
    'name': 'fullName',
    'full_name': 'fullName',
    'fullname': 'fullName',
    'date_of_birth': 'dateOfBirth',
    'dob': 'dateOfBirth',
    'dateofbirth': 'dateOfBirth',
    'gender': 'gender',
    'sex': 'gender',
    'address': 'addressLine1',
    'address_line_1': 'addressLine1',
    'address_line_2': 'addressLine2',
    'address_line_3': 'addressLine3',
    'city': 'city',
    'town': 'city',
    'region': 'region',
    'province': 'province',
    'state': 'province',
    'postal_code': 'postalCode',
    'pin_code': 'postalCode',
    'pincode': 'postalCode',
    'zip': 'postalCode',
    'zone': 'zone',
    'phone': 'phone',
    'mobile': 'phone',
    'contact': 'phone',
    'email': 'email',
    'email_id': 'email',
    'reference_identity_number': 'referenceIdentityNumber',
    'uin': 'UIN',
    'aadhar': 'referenceIdentityNumber',
    'aadhaar': 'referenceIdentityNumber'
};
