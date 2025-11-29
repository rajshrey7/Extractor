"""
Language Support Module
Handles multi-lingual support (English/Arabic) for OCR, UI, and Field Mapping
"""
from typing import Dict, List, Any

class LanguageLoader:
    """
    Manages language translations and configurations
    """
    
    SUPPORTED_LANGUAGES = ["en", "ar"]
    DEFAULT_LANGUAGE = "en"
    
    # Translation Dictionary
    TRANSLATIONS = {
        "en": {
            # UI Elements
            "app_title": "OCR Text Extraction & Verification",
            "app_subtitle": "Extract text from documents, auto-fill forms, and verify data accuracy",
            "tab_extract": "Extract Text",
            "tab_verify": "Verify Data",
            "tab_jobform": "Auto-Fill Form",
            "tab_autofill": "Match Fields",
            "upload_title": "Upload Document (Image or PDF)",
            "upload_desc": "Click to browse or drag and drop your file here",
            "upload_support": "Supports: JPG, PNG, JPEG, PDF",
            "use_google_vision": "🤖 Use Google Vision API (Direct Image to JSON)",
            "process_btn": "Process Image",
            "google_vision_note": "Google Vision: Uses Google Cloud Vision API to extract structured JSON from images.",
            "processing": "Processing image... Please wait",
            "extracted_json_title": "📄 Extracted Data (JSON Format)",
            "copy_json": "📋 Copy JSON",
            "json_note": "✓ This JSON is automatically populated in the 'Verify Data' and 'Auto-Fill Form' tabs",
            "extracted_fields_title": "📋 Extracted Fields (Formatted View)",
            "general_text_title": "📝 General Text",
            
            # Verify Tab
            "verify_title": "🔍 Advanced OCR Verification System",
            "verify_desc": "Validates OCR data accuracy, format, and detects errors",
            "verify_btn": "🔍 Verify & Validate Data",
            "verifying": "Verifying data... Please wait",
            "verification_status": "📊 Verification Status",
            "cleaned_data_title": "✨ Cleaned & Verified Data",
            "verification_report": "📋 Detailed Verification Report",
            "summary_stats": "📊 Summary Statistics",
            
            # Job Form Tab
            "job_form_title": "💼 Automatic Job Application Form Filler",
            "job_form_desc": "Upload your document or resume, extract data, and automatically fill job application forms with AI",
            "upload_resume": "📄 Upload Resume (PDF) - For AI-Powered Filling",
            "process_resume_btn": "Process Resume with AI",
            "google_form_url": "📋 Google Form URL",
            "paste_url_placeholder": "Paste the Google Form URL for the job application",
            "ai_model_select": "🤖 AI Model Selection",
            "analyze_btn": "🔍 Analyze Form",
            "fill_ocr_btn": "✨ Fill Form with OCR Data",
            "fill_ai_btn": "🤖 Fill Form with AI (Resume Required)",
            "form_questions": "📝 Form Questions",
            "form_filled_success": "✅ Form Filled Successfully!",
            "form_data_summary": "📋 Form Data Summary (JSON)",
            
            # Auto-Fill Tab
            "autofill_title": "Form Auto-Fill",
            "autofill_desc": "Match extracted data to form fields",
            "form_fields_label": "📝 Form Fields (JSON List or Line-separated)",
            "match_btn": "🎯 Match Fields",
            "matching": "Matching fields... Please wait",
            "field_matches": "🎯 Field Matches",
            
            # Field Names (Standard)
            "field_surname": "Surname",
            "field_name": "Name",
            "field_nationality": "Nationality",
            "field_sex": "Sex",
            "field_dob": "Date of Birth",
            "field_pob": "Place of Birth",
            "field_issue_date": "Issue Date",
            "field_expiry_date": "Expiry Date",
            "field_issuing_office": "Issuing Office",
            "field_height": "Height",
            "field_type": "Type",
            "field_country": "Country",
            "field_passport_no": "Passport No",
            "field_personal_no": "Personal No",
            "field_card_no": "Card No",
            "field_phone": "Phone",
            "field_email": "Email",
            "field_address": "Address",
            
            # OCR Config
            "ocr_lang_code": "en",
            "google_vision_lang_hint": "en",
            "text_direction": "ltr"
        },
        "ar": {
            # UI Elements
            "app_title": "استخراج النصوص والتحقق منها (OCR)",
            "app_subtitle": "استخراج النصوص من المستندات، ملء النماذج تلقائياً، والتحقق من دقة البيانات",
            "tab_extract": "استخراج النص",
            "tab_verify": "التحقق من البيانات",
            "tab_jobform": "تعبئة النماذج تلقائياً",
            "tab_autofill": "مطابقة الحقول",
            "upload_title": "رفع المستند (صورة أو PDF)",
            "upload_desc": "انقر للاستعراض أو اسحب الملف هنا",
            "upload_support": "يدعم: JPG, PNG, JPEG, PDF",
            "use_google_vision": "🤖 استخدام Google Vision API (تحويل مباشر للصورة إلى JSON)",
            "process_btn": "معالجة الصورة",
            "google_vision_note": "Google Vision: يستخدم Google Cloud Vision API لاستخراج JSON منظم من الصور.",
            "yolo_note": "YOLO+EasyOCR: يستخدم نموذج YOLO المدرب للكشف عن الحقول (الافتراضي).",
            "processing": "جاري معالجة الصورة... يرجى الانتظار",
            "extracted_json_title": "📄 البيانات المستخرجة (تنسيق JSON)",
            "copy_json": "📋 نسخ JSON",
            "json_note": "✓ يتم تعبئة هذا JSON تلقائياً في علامات تبويب 'التحقق من البيانات' و 'تعبئة النماذج تلقائياً'",
            "extracted_fields_title": "📋 الحقول المستخرجة (عرض منسق)",
            "general_text_title": "📝 نص عام",
            
            # Verify Tab
            "verify_title": "🔍 نظام التحقق المتقدم من OCR",
            "verify_desc": "يتحقق من دقة بيانات OCR، التنسيق، ويكتشف الأخطاء",
            "verify_btn": "🔍 التحقق والتدقيق في البيانات",
            "verifying": "جاري التحقق من البيانات... يرجى الانتظار",
            "verification_status": "📊 حالة التحقق",
            "cleaned_data_title": "✨ البيانات المنظفة والمتحقق منها",
            "verification_report": "📋 تقرير التحقق التفصيلي",
            "summary_stats": "📊 إحصائيات الملخص",
            
            # Job Form Tab
            "job_form_title": "💼 تعبئة نماذج التوظيف التلقائية",
            "job_form_desc": "ارفع مستندك أو سيرتك الذاتية، استخرج البيانات، واملأ نماذج التوظيف تلقائياً باستخدام الذكاء الاصطناعي",
            "upload_resume": "📄 رفع السيرة الذاتية (PDF) - للتعبئة بالذكاء الاصطناعي",
            "process_resume_btn": "معالجة السيرة الذاتية بالذكاء الاصطناعي",
            "google_form_url": "📋 رابط نموذج Google",
            "paste_url_placeholder": "الصق رابط نموذج Google لطلب التوظيف",
            "ai_model_select": "🤖 اختيار نموذج الذكاء الاصطناعي",
            "analyze_btn": "🔍 تحليل النموذج",
            "fill_ocr_btn": "✨ تعبئة النموذج ببيانات OCR",
            "fill_ai_btn": "🤖 تعبئة النموذج بالذكاء الاصطناعي (يتطلب سيرة ذاتية)",
            "form_questions": "📝 أسئلة النموذج",
            "form_filled_success": "✅ تم تعبئة النموذج بنجاح!",
            "form_data_summary": "📋 ملخص بيانات النموذج (JSON)",
            
            # Auto-Fill Tab
            "autofill_title": "تعبئة النماذج تلقائياً",
            "autofill_desc": "مطابقة البيانات المستخرجة مع حقول النموذج",
            "form_fields_label": "📝 حقول النموذج (قائمة JSON أو مفصولة بأسطر)",
            "match_btn": "🎯 مطابقة الحقول",
            "matching": "جاري مطابقة الحقول... يرجى الانتظار",
            "field_matches": "🎯 مطابقات الحقول",
            
            # Field Names (Arabic Mappings)
            "field_surname": "اللقب",
            "field_name": "الاسم",
            "field_nationality": "الجنسية",
            "field_sex": "الجنس",
            "field_dob": "تاريخ الميلاد",
            "field_pob": "مكان الميلاد",
            "field_issue_date": "تاريخ الإصدار",
            "field_expiry_date": "تاريخ الانتهاء",
            "field_issuing_office": "جهة الإصدار",
            "field_height": "الطول",
            "field_type": "النوع",
            "field_country": "البلد",
            "field_passport_no": "رقم الجواز",
            "field_personal_no": "الرقم الشخصي",
            "field_card_no": "رقم البطاقة",
            "field_phone": "رقم الهاتف",
            "field_email": "البريد الإلكتروني",
            "field_address": "العنوان",
            
            # OCR Config
            "ocr_lang_code": "ar",
            "google_vision_lang_hint": "ar",
            "text_direction": "rtl"
        }
    }
    
    # Regex Patterns (Localized)
    REGEX_PATTERNS = {
        "en": {
            "Name": [
                r'(?:name|full name|first name|given name|given)[\s:]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$',
                r'Name[\s:]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
            ],
            "Surname": [
                r'(?:surname|last name|family name|sumname)[\s:]*([A-Z][a-z]+)',
                r'Surname[\s:]*([A-Z][a-z]+)'
            ],
            "Date of Birth": [
                r'(?:date of birth|dob|birth date|born|of birth)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "Passport No": [
                r'(?:passport|passport no|passport number|document no|document number)[\s:]*([A-Z0-9]{6,})',
                r'Passport[\s:]*([A-Z0-9]{6,})'
            ],
            "Personal No": [
                r'(?:personal no|national id|id number|personal number)[\s:]*([A-Z0-9]+)',
                r'Personal[\s:]*No[\s:]*([A-Z0-9]+)'
            ],
            "Phone": [
                r'(?:phone|mobile|tel|telephone)[\s:]*([+]?[\d\s\-()]{8,})',
                r'(\+?\d{1,3}[\s\-]?\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4})'
            ],
            "Email": [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            "Address": [
                r'(?:address|street|location)[\s:]*([A-Z0-9][^,\n]+(?:,\s*[A-Z][a-z]+)*)',
                r'(\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr)[^,\n]*)'
            ],
            "Issue Date": [
                r'(?:issue date|issued on|date of issue|issue)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Issue[\s:]*Date[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "Expiry Date": [
                r'(?:expiry date|expires|expiration date|expiry|exp)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Expiry[\s:]*Date[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "Nationality": [
                r'(?:nationality|nationalitv)[\s:]*([A-Z][a-z]+)',
                r'Nationality[\s:]*([A-Z][a-z]+)'
            ],
            "Country": [
                r'(?:country|code of state|code of issuing state)[\s:]*([A-Z]{2,3})',
                r'Country[\s:]*([A-Z]{2,3})'
            ],
            "Issuing Office": [
                r'(?:issuing office|issuing authority|authority|iss office)[\s:]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'Issuing[\s:]*Office[\s:]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ],
            "Height": [
                r'(?:height|iheight)[\s:]*(\d+\s*(?:cm|ft|in|m))',
                r'Height[\s:]*(\d+)'
            ],
            "Sex": [
                r'(?:sex|gender|isex)[\s:]*([MF|Male|Female])',
                r'Sex[\s:]*([MF])'
            ],
            "Place of Birth": [
                r'(?:place of birth|place of binth)[\s:]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'Place[\s:]*of[\s:]*Birth[\s:]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ],
            "Card No": [
                r'(?:card no|card number|card no_)[\s:]*([A-Z0-9]+)',
                r'Card[\s:]*No[\s:]*([A-Z0-9]+)'
            ]
        },
        "ar": {
            "Name": [
                r'(?:الاسم|الاسم الكامل|الاسم الأول)[\s:]*([\u0600-\u06FF\s]+)',
                r'الاسم[\s:]*([\u0600-\u06FF\s]+)'
            ],
            "Surname": [
                r'(?:اللقب|اسم العائلة)[\s:]*([\u0600-\u06FF\s]+)',
                r'اللقب[\s:]*([\u0600-\u06FF\s]+)'
            ],
            "Date of Birth": [
                r'(?:تاريخ الميلاد|الميلاد)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "Passport No": [
                r'(?:رقم الجواز|رقم جواز السفر)[\s:]*([A-Z0-9]{6,})'
            ],
            "Personal No": [
                r'(?:الرقم الشخصي|رقم الهوية|الرقم الوطني)[\s:]*([A-Z0-9]+)'
            ],
            "Phone": [
                r'(?:الهاتف|الجوال|رقم الهاتف)[\s:]*([+]?[\d\s\-()]{8,})'
            ],
            "Email": [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            "Address": [
                r'(?:العنوان|الموقع)[\s:]*([\u0600-\u06FF0-9\s،,-]+)'
            ],
            "Issue Date": [
                r'(?:تاريخ الإصدار|صدر في)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "Expiry Date": [
                r'(?:تاريخ الانتهاء|ينتهي في)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "Nationality": [
                r'(?:الجنسية)[\s:]*([\u0600-\u06FF\s]+)'
            ],
            "Country": [
                r'(?:البلد|الدولة)[\s:]*([\u0600-\u06FF\s]+)'
            ],
            "Issuing Office": [
                r'(?:جهة الإصدار|مكان الإصدار)[\s:]*([\u0600-\u06FF\s]+)'
            ],
            "Height": [
                r'(?:الطول)[\s:]*(\d+\s*(?:سم|م))'
            ],
            "Sex": [
                r'(?:الجنس|النوع)[\s:]*([ذكر|انثى|M|F])'
            ],
            "Place of Birth": [
                r'(?:مكان الميلاد)[\s:]*([\u0600-\u06FF\s]+)'
            ],
            "Card No": [
                r'(?:رقم البطاقة)[\s:]*([A-Z0-9]+)'
            ]
        }
    }

    # Field Types (Synonyms for normalization)
    # Keys use Title Case to match regex pattern keys and ensure consistency
    FIELD_TYPES = {
        "en": {
            'Name': ['name', 'full name', 'first name', 'last name', 'surname', 'given name'],
            'Age': ['age'],
            'Date of Birth': ['dob', 'date of birth', 'birthdate', 'birth date', 'date_of_birth'],
            'Phone': ['phone', 'mobile', 'phone number', 'contact', 'mobile number', 'telephone', 'contact number'],
            'Email': ['email', 'e-mail', 'email address', 'mail'],
            'Personal No': ['id', 'id number', 'aadhaar', 'pan', 'personal no', 'personal number', 'national id'],
            'Passport No': ['passport', 'passport no', 'passport number', 'document no', 'document number'],
            'Card No': ['card no', 'card number', 'driving license', 'license number'],
            'Address': ['address', 'residence', 'location', 'street'],
            'City': ['city', 'town'],
            'State': ['state', 'province'],
            'Country': ['country', 'nation'],
            'Gender': ['gender', 'sex'],
            'Pincode': ['pincode', 'pin code', 'postal code', 'zip code', 'zip']
        },
        "ar": {
            'Name': ['الاسم', 'الاسم الكامل', 'الاسم الأول', 'اللقب', 'اسم العائلة'],
            'Age': ['العمر'],
            'Date of Birth': ['تاريخ الميلاد', 'الميلاد', 'يوم الميلاد'],
            'Phone': ['رقم الهاتف', 'الجوال', 'الهاتف', 'رقم الجوال', 'تلفون'],
            'Email': ['البريد الإلكتروني', 'ايميل', 'بريد'],
            'Personal No': ['رقم الهوية', 'الرقم الوطني', 'الرقم الشخصي'],
            'Passport No': ['رقم الجواز', 'رقم جواز السفر'],
            'Card No': ['رقم البطاقة'],
            'Address': ['العنوان', 'الموقع', 'مكان الإقامة'],
            'City': ['المدينة', 'البلدة'],
            'Country': ['البلد', 'الدولة'],
            'Gender': ['الجنس', 'النوع'],
            'Pincode': ['الرمز البريدي', 'صندوق البريد']
        }
    }

    def __init__(self, language: str = "en"):
        self.current_language = language if language in self.SUPPORTED_LANGUAGES else self.DEFAULT_LANGUAGE
    
    def set_language(self, language: str):
        if language in self.SUPPORTED_LANGUAGES:
            self.current_language = language
            return True
        return False
    
    def get_text(self, key: str) -> str:
        """Get translated text for UI"""
        return self.TRANSLATIONS.get(self.current_language, {}).get(key, key)
    
    def get_all_translations(self) -> Dict[str, str]:
        """Get all translations for current language"""
        return self.TRANSLATIONS.get(self.current_language, {})
    
    def get_field_name(self, standard_field: str) -> str:
        """Get localized field name"""
        # Map standard internal names to localized display names
        key = f"field_{standard_field.lower().replace(' ', '_')}"
        return self.get_text(key)

    def get_regex_patterns(self) -> Dict[str, List[str]]:
        """Get regex patterns for current language"""
        return self.REGEX_PATTERNS.get(self.current_language, self.REGEX_PATTERNS["en"])

    def get_field_types(self) -> Dict[str, List[str]]:
        """Get field types/synonyms for current language"""
        return self.FIELD_TYPES.get(self.current_language, self.FIELD_TYPES["en"])
    
    def get_ocr_lang(self) -> List[str]:
        """Get EasyOCR language codes"""
        if self.current_language == "ar":
            return ['ar', 'en'] # Arabic usually needs English too
        return ['en']
    
    def get_google_vision_lang(self) -> List[str]:
        """Get Google Vision language hints"""
        return [self.TRANSLATIONS.get(self.current_language, {}).get("google_vision_lang_hint", "en")]
    
    def get_text_direction(self) -> str:
        """Get text direction (ltr/rtl)"""
        return self.TRANSLATIONS.get(self.current_language, {}).get("text_direction", "ltr")

    JOB_FIELD_ALIASES = {
        "en": {
            "name": {
                "aliases": ["full name", "first name", "last name", "surname", "given name", "applicant name"],
                "type": "text",
                "required": True,
                "weight": 1.0
            },
            "email": {
                "aliases": ["email address", "e-mail", "email", "contact email"],
                "type": "email",
                "required": True,
                "weight": 1.0,
                "validation": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            },
            "phone": {
                "aliases": ["phone", "mobile", "telephone", "phone number", "mobile number", "contact number"],
                "type": "tel",
                "required": True,
                "weight": 0.9
            },
            "address": {
                "aliases": ["address", "residence", "location", "street address", "home address"],
                "type": "text",
                "required": True,
                "weight": 0.8
            },
            "city": {
                "aliases": ["city", "town"],
                "type": "text",
                "required": True,
                "weight": 0.7
            },
            "state": {
                "aliases": ["state", "province", "region"],
                "type": "text",
                "required": True,
                "weight": 0.7
            },
            "zip": {
                "aliases": ["zip code", "postal code", "pincode", "zip"],
                "type": "text",
                "required": True,
                "weight": 0.7
            },
            "country": {
                "aliases": ["country", "nation"],
                "type": "text",
                "required": True,
                "weight": 0.7
            },
            "date_of_birth": {
                "aliases": ["dob", "birthdate", "date of birth", "birth date"],
                "type": "date",
                "required": True,
                "weight": 0.8
            },
            "education": {
                "aliases": ["education", "qualification", "degree", "university", "college", "school"],
                "type": "text",
                "required": False,
                "weight": 0.6
            },
            "experience": {
                "aliases": ["experience", "work experience", "employment", "job history", "career"],
                "type": "text",
                "required": False,
                "weight": 0.7
            },
            "skills": {
                "aliases": ["skills", "technical skills", "competencies", "abilities"],
                "type": "text",
                "required": False,
                "weight": 0.5
            },
            "resume": {
                "aliases": ["resume", "cv", "curriculum vitae"],
                "type": "file",
                "required": True,
                "weight": 0.9
            },
            "cover_letter": {
                "aliases": ["cover letter", "motivation letter"],
                "type": "file",
                "required": False,
                "weight": 0.4
            },
            "linkedin": {
                "aliases": ["linkedin", "linkedin profile", "linkedin url"],
                "type": "url",
                "required": False,
                "weight": 0.3,
                "validation": r'(https?:\/\/)?(www\.)?linkedin\.com\/in\/.*'
            },
            "website": {
                "aliases": ["website", "portfolio", "personal website"],
                "type": "url",
                "required": False,
                "weight": 0.3
            },
            "availability": {
                "aliases": ["availability", "start date", "when can you start"],
                "type": "date",
                "required": False,
                "weight": 0.5
            },
            "salary": {
                "aliases": ["salary", "expected salary", "compensation", "pay"],
                "type": "number",
                "required": False,
                "weight": 0.4
            },
            "references": {
                "aliases": ["references", "referees", "reference contacts"],
                "type": "text",
                "required": False,
                "weight": 0.3
            },
            "Date": {
                "aliases": ["Date", "Today's Date", "Current Date", "Date of Application"],
                "type": "date",
                "required": False,
                "weight": 0.5
            }
        },
        "ar": {
             "name": {
                "aliases": ["الاسم الكامل", "الاسم الأول", "اسم العائلة", "اللقب", "اسم مقدم الطلب"],
                "type": "text",
                "required": True,
                "weight": 1.0
            },
            "email": {
                "aliases": ["البريد الإلكتروني", "إيميل", "البريد الالكتروني"],
                "type": "email",
                "required": True,
                "weight": 1.0
            },
            "phone": {
                "aliases": ["رقم الهاتف", "الجوال", "الموبايل", "رقم الاتصال", "هاتف"],
                "type": "tel",
                "required": True,
                "weight": 0.9
            },
            "address": {
                "aliases": ["العنوان", "مكان الإقامة", "الشارع", "عنوان المنزل"],
                "type": "text",
                "required": True,
                "weight": 0.8
            },
            "city": {
                "aliases": ["المدينة", "البلدة"],
                "type": "text",
                "required": True,
                "weight": 0.7
            },
            "country": {
                "aliases": ["البلد", "الدولة"],
                "type": "text",
                "required": True,
                "weight": 0.7
            },
            "date_of_birth": {
                "aliases": ["تاريخ الميلاد", "المواليد", "يوم الميلاد"],
                "type": "date",
                "required": True,
                "weight": 0.8
            },
            "education": {
                "aliases": ["التعليم", "المؤهل العلمي", "الشهادة", "الجامعة", "الكلية", "المدرسة"],
                "type": "text",
                "required": False,
                "weight": 0.6
            },
            "experience": {
                "aliases": ["الخبرة", "خبرة العمل", "التوظيف", "تاريخ العمل", "السيرة المهنية"],
                "type": "text",
                "required": False,
                "weight": 0.7
            },
            "skills": {
                "aliases": ["المهارات", "المهارات التقنية", "الكفاءات", "القدرات"],
                "type": "text",
                "required": False,
                "weight": 0.5
            }
        }
    }

    def get_job_field_aliases(self) -> Dict[str, Any]:
        """Get job field aliases for current language"""
        # Return Arabic aliases if language is Arabic, otherwise default to English
        # We merge with English to ensure all fields are present even if not fully translated
        if self.current_language == 'ar':
            # Start with English as base
            aliases = self.JOB_FIELD_ALIASES['en'].copy()
            # Update with Arabic where available
            if 'ar' in self.JOB_FIELD_ALIASES:
                for key, value in self.JOB_FIELD_ALIASES['ar'].items():
                    aliases[key] = value
            return aliases
        
        return self.JOB_FIELD_ALIASES.get('en', {})
