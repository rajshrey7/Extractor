"""
Language Support Module
Handles multi-lingual support (English/Arabic) for OCR, UI, and Field Mapping
"""
from typing import Dict, List, Any

class LanguageLoader:
    """
    Manages language translations and configurations
    """
    
    SUPPORTED_LANGUAGES = ["en", "ar", "hi"]
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
        },
        "hi": {
            # UI Elements
            "app_title": "OCR टेक्स्ट निष्कर्षण और सत्यापन",
            "app_subtitle": "दस्तावेज़ों से टेक्स्ट निकालें, फॉर्म ऑटो-फिल करें, और डेटा सटीकता सत्यापित करें",
            "tab_extract": "टेक्स्ट निकालें",
            "tab_verify": "डेटा सत्यापित करें",
            "tab_jobform": "ऑटो-फिल फॉर्म",
            "tab_autofill": "फ़ील्ड मिलान",
            "upload_title": "दस्तावेज़ अपलोड करें (छवि या PDF)",
            "upload_desc": "ब्राउज़ करने के लिए क्लिक करें या अपनी फ़ाइल यहां खींचें और छोड़ें",
            "upload_support": "समर्थित: JPG, PNG, JPEG, PDF",
            "use_google_vision": "🤖 Google Vision API का उपयोग करें",
            "process_btn": "छवि प्रोसेस करें",
            "google_vision_note": "Google Vision: छवियों से संरचित JSON निकालने के लिए Google Cloud Vision API का उपयोग करता है।",
            "processing": "छवि प्रोसेस हो रही है... कृपया प्रतीक्षा करें",
            "extracted_json_title": "📄 निकाला गया डेटा (JSON प्रारूप)",
            "copy_json": "📋 JSON कॉपी करें",
            "json_note": "✓ यह JSON 'डेटा सत्यापित करें' और 'ऑटो-फिल फॉर्म' टैब में स्वचालित रूप से भरा जाता है",
            "extracted_fields_title": "📋 निकाले गए फ़ील्ड (स्वरूपित दृश्य)",
            "general_text_title": "📝 सामान्य टेक्स्ट",
            
            # Verify Tab
            "verify_title": "🔍 उन्नत OCR सत्यापन प्रणाली",
            "verify_desc": "OCR डेटा सटीकता, प्रारूप को मान्य करता है, और त्रुटियों का पता लगाता है",
            "verify_btn": "🔍 डेटा सत्यापित और वैधता जांचें",
            "verifying": "डेटा सत्यापित हो रहा है... कृपया प्रतीक्षा करें",
            "verification_status": "📊 सत्यापन स्थिति",
            "cleaned_data_title": "✨ साफ और सत्यापित डेटा",
            "verification_report": "📋 विस्तृत सत्यापन रिपोर्ट",
            "summary_stats": "📊 सारांश सांख्यिकी",
            
            # Job Form Tab
            "job_form_title": "💼 स्वचालित जॉब एप्लिकेशन फॉर्म फिलर",
            "job_form_desc": "अपना दस्तावेज़ या रिज्यूमे अपलोड करें, डेटा निकालें, और AI के साथ जॉब एप्लिकेशन फॉर्म स्वचालित रूप से भरें",
            "upload_resume": "📄 रिज्यूमे अपलोड करें (PDF) - AI-संचालित भरने के लिए",
            "process_resume_btn": "AI के साथ रिज्यूमे प्रोसेस करें",
            "google_form_url": "📋 Google फॉर्म URL",
            "paste_url_placeholder": "जॉब एप्लिकेशन के लिए Google फॉर्म URL पेस्ट करें",
            "ai_model_select": "🤖 AI मॉडल चयन",
            "analyze_btn": "🔍 फॉर्म का विश्लेषण करें",
            "fill_ocr_btn": "✨ OCR डेटा से फॉर्म भरें",
            "fill_ai_btn": "🤖 AI के साथ फॉर्म भरें (रिज्यूमे आवश्यक)",
            "form_questions": "📝 फॉर्म प्रश्न",
            "form_filled_success": "✅ फॉर्म सफलतापूर्वक भरा गया!",
            "form_data_summary": "📋 फॉर्म डेटा सारांश (JSON)",
            
            # Auto-Fill Tab
            "autofill_title": "फॉर्म ऑटो-फिल",
            "autofill_desc": "निकाले गए डेटा को फॉर्म फ़ील्ड से मिलाएं",
            "form_fields_label": "📝 फॉर्म फ़ील्ड (JSON सूची या लाइन-अलग)",
            "match_btn": "🎯 फ़ील्ड मिलान करें",
            "matching": "फ़ील्ड मिलान हो रहा है... कृपया प्रतीक्षा करें",
            "field_matches": "🎯 फ़ील्ड मिलान",
            
            # Field Names (Hindi Mappings)
            "field_surname": "उपनाम",
            "field_name": "नाम",
            "field_nationality": "राष्ट्रीयता",
            "field_sex": "लिंग",
            "field_dob": "जन्म तिथि",
            "field_pob": "जन्म स्थान",
            "field_issue_date": "जारी तिथि",
            "field_expiry_date": "समाप्ति तिथि",
            "field_issuing_office": "जारी करने वाला कार्यालय",
            "field_height": "ऊंचाई",
            "field_type": "प्रकार",
            "field_country": "देश",
            "field_passport_no": "पासपोर्ट नंबर",
            "field_personal_no": "व्यक्तिगत नंबर",
            "field_card_no": "कार्ड नंबर",
            "field_phone": "फोन",
            "field_email": "ईमेल",
            "field_address": "पता",
            
            # OCR Config
            "ocr_lang_code": "hi",
            "google_vision_lang_hint": "hi",
            "text_direction": "ltr"
        }
    }
    
    # Regex Patterns (Localized)
    REGEX_PATTERNS = {
        "en": {
            "Name": [
                # Universal name patterns - handles all documents
                r'(?:name|full name|first name|given name|applicant name|candidate name|holder name|bearer name)[\s:.-]*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)',
                r'(?:name|naam)[\s:.-]*([A-Z][a-zA-Z\s]{3,50})',
                r'Name[\s:.-]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)$'  # Standalone name
            ],
            "Surname": [
                r'(?:surname|last name|family name|sumname)[\s:]*([A-Z][a-z]+)',
                r'Surname[\s:]*([A-Z][a-z]+)'
            ],
            "Date of Birth": [
                # Universal date patterns - all formats
                r'(?:date of birth|dob|d\.?o\.?b\.?|birth date|born|date of binth|of birth|janma|जन्म)[\s:.-]*(\d{1,2}[/\-.]+\d{1,2}[/\-.]+\d{2,4})',
                r'(?:dob|date)[\s:.-]*(\d{4}[/\-.]+\d{1,2}[/\-.]+\d{1,2})',  # YYYY-MM-DD
                r'(\d{1,2}[/\-.]+\d{1,2}[/\-.]+\d{2,4})',  # Standalone date
                r'(\d{2}[/\-.]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[/\-.]+\d{4})'  # DD-MMM-YYYY
            ],
            "Passport No": [
                # Universal passport patterns
                r'(?:passport|passport no\.?|passport number|document no\.?|document number|passport na|पासपोर्ट)[\s:.-]*([A-Z]\d{7,8}|[A-Z]{2}\d{6,7}|[A-Z0-9]{6,10})',
                r'Passport[\s:.-]*(?:No|Number)?[\s:.-]*([A-Z]\d{7,8})',
                r'\b([A-Z]\d{7,8})\b',  # Standalone passport format
                r'\b([A-Z]{2}\d{7})\b'  # Some countries use 2 letters + 7 digits
            ],
            "Aadhaar": [
                # Aadhaar patterns - MUST come BEFORE Personal No
                r'(?:aadhaar|aadhar|aadhaar no\.?|aadhar no\.?|aadhaar number|uid|आधार)[\s:.-]*(\d{4}[\s-]?\d{4}[\s-]?\d{4})',
                r'Aadhaar[\s:]*(?:No|Number)?[\s:.-]*(\d{12})',
                r'\b(\d{4}\s\d{4}\s\d{4})\b',  # Standalone with spaces - PRIORITY for Aadhaar cards
                r'\b(\d{12})\b'  # 12 digits no spaces
            ],
            "Personal No": [
                # Universal ID patterns - Aadhaar, PAN, Voter ID, etc.
                r'(?:personal no|national id|id number|personal number|identification|id no|citizen id)[\s:.-]*([A-Z0-9]{6,20})',
                r'(?:aadhaar|aadhar|uid|आधार)[\s:.-]*(\d{4}[\s-]?\d{4}[\s-]?\d{4})',
                r'(?:pan|पैन)[\s:.-]*([A-Z]{5}\d{4}[A-Z])',
                r'(?:voter id|epic no|electoral)[\s:.-]*([A-Z]{3}\d{7})',
                r'Personal[\s:]*No[\s:.-]*([A-Z0-9]+)'
            ],
            "Phone": [
                # Phone patterns - MUST have label to avoid matching Aadhaar
                r'(?:phone|mobile|mob|tel|telephone|contact|cell|फोन|मोबाइल)[\s:.-]*([+]?[\d\s\-()]{8,15})',
                r'(?:phone|mobile|tel)[\s:.-]*(\+?\d{1,3}[\s.\-]?\(?\d{3,4}\)?[\s.\-]?\d{3,4}[\s.\-]?\d{3,4})',
                r'(?:contact|mob)[\s:.-]*([+]91[\s\-]?\d{10})'  # Indian with label
            ],
            "Email": [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            "Address": [
                # Birth Certificate Specific Patterns
                r'(?:address of parents at the time of birth of the child|permanent address of parents|address of parents)[\s:.-]*((?:[LHM]\.?[IА]?\.?[GО]\.?-?\d+|\d+/\d+)[^\n]+)',
                r'(?:address|addr)[\s:.-]*((?:[LHM]\.?[IА]?\.?[GО]\.?-?\d+)[^\n]+)',
                # General address patterns  
                r'(?:address|street|location)[\s:]*([A-Z0-9][^,\n]+(?:,\s*[A-Z][a-z]+)*)',
                r'((?:[LHM]I?G?-\d+|\d+/\d+),?\s+[A-Za-z]+(?:\s+[A-Za-z]+)*(?:\s+(?:Housing|Colony|Society|Board|Apartment|Complex|Nagar|Layout))?[^\n]*)',
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
                r'(?:sex|gender|isex|पुरुष|महिला)[\s:/]*([MF]|Male|Female|MALE|FEMALE|पुरुष|महिला)',
                r'Sex[\s:./]*([MF]|Male|Female)',
                r'/\s*(MALE|FEMALE|Male|Female)\b',  # After slash like "पुरुष / MALE"
                r'\b(MALE|FEMALE)\b'  # Standalone
            ],
            "Place of Birth": [
                r'(?:place of birth|place of binth)[\s:]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'Place[\s:]*of[\s:]*Birth[\s:]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ],
            "Card No": [
                # Universal card number patterns - DL, Credit, etc.
                r'(?:card no\.?|card number|driving license|dl no\.?|license no\.?|driving licence)[\s:.-]*([A-Z0-9]{6,20})',
                r'(?:dl|lic|license)[\s:.-]*([A-Z]{2}[-\s]?\d{2}[-\s]?\d{4}[-\s]?\d{7})',  # Indian DL format
                r'Card[\s:]*(?:No|Number)?[\s:.-]*([A-Z0-9\-]{6,20})',
                r'([A-Z]{2}[-]?\d{13,14})'  # Some DL formats
            ],
            "Blood Group": [
                r'(?:blood group|blood type|b\.?g\.?)[\s:]*([ABO]{1,2}[+-])',
                r'Blood[\s:]*Group[\s:]*([ABO]{1,2}[+-])',
                r'\b([ABO]{1,2}[+-])\b'
            ],
            # ===== BIRTH CERTIFICATE SPECIFIC FIELDS =====
            "Father Name": [
                r'(?:father[\'s]*\s*name|fathers name|father name|name of father)[\\s:.-]*([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)',
                r'Father[\\s:.-]*([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)'
            ],
            "Mother Name": [
                r'(?:mother[\'s]*\s*name|mothers name|mother name|name of mother)[\\s:.-]*([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)',
                r'Mother[\\s:.-]*([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)'
            ],
            "Certificate No": [
                r'(?:certificate no|certificate number|cert no|cert number|registration number)[\\s:.-]*(\\d+)',
                r'Certificate[\\s:]*No[\\s:.-]*(\\d+)'
            ],
            "Registration No": [
                r'(?:registration no|registration number|reg no|reg number)[\\s:.-]*(\\d+)',
                r'Registration[\\s:]*No[\\s:.-]*(\\d+)'
            ],
            "Date of Registration": [
                r'(?:date of registration|registration date|reg date|registered on)[\\s:]*(\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4})',
                r'Registration[\\s:]*Date[\\s:]*(\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4})'
            ],
            "Place of Issue": [
                r'(?:place of issue|issued at|issuing office|place)[\\s:.-]*([A-Z][a-z]+(?:(?:\\s+[A-Z][a-z]+)*|\\s*[-,]\\s*[A-Z][a-z]+)*)',
                r'Place[\\s:]*of[\\s:]*Issue[\\s:.-]*([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*)'
            ],
            "Religion": [
                r'(?:religion|relig)[\\s:.-]*(\\w+)',
                r'Religion[\\s:.-]*(\\w+)'
            ],
            "Pin Code": [
                r'(?:pin code|pincode|pin|postal code)[\\s:.-]*(\\d{6})',
                r'Pin[\\s:]*Code[\\s:.-]*(\\d{6})'
            ],
            "District": [
                r'(?:district|dist)[\\s:.-]*([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*)',
                r'District[\\s:.-]*([A-Z][a-z]+)'
            ],
            "Aadhaar": [
                r'(?:aadhaar|aadhar|aadhaar no|aadhar no|aadhaar number)[\\s:.-]*(\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4})',
                r'Aadhaar[\\s:]*(?:No|Number)[\\s:.-]*(\\d{12})'
            ],
            "Permanent Address": [
                r'(?:permanent address of parents|permanent address)[\\s:.-]*((?:[LHM]\\.?[IA]?\\.?[GO]?\\.?-?\\d+|\\d+/\\d+)[^\\n]+)',
                r'Permanent[\\s:]*Address[\\s:.-]*([A-Z0-9][^\\n]+)'
            ],
            # ===== ADDITIONAL UNIVERSAL DOCUMENT FIELDS =====
            "PAN": [
                r'(?:pan|pan no\.?|pan number|pan card|permanent account number|पैन)[\\s:.-]*([A-Z]{5}\\d{4}[A-Z])',
                r'\\b([A-Z]{5}\\d{4}[A-Z])\\b'  # Standalone PAN format
            ],
            "Aadhaar": [
                r'(?:aadhaar|aadhar|aadhaar no\.?|aadhar no\.?|aadhaar number|uid|आधार)[\\s:.-]*(\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4})',
                r'Aadhaar[\\s:]*(?:No|Number)?[\\s:.-]*(\\d{12})',
                r'\\b(\\d{4}\\s\\d{4}\\s\\d{4})\\b'  # 12 digit format with spaces - PRIORITY
            ],
            "VID": [
                r'(?:vid|virtual id|virtual identity)[\\s:.-]*(\\d{16})',
                r'VID[\\s:.-]*(\\d{16})',
                r'\\b(\\d{16})\\b'  # 16 digit standalone
            ],
            "Driving License": [
                r'(?:driving license|driving licence|dl no\.?|dl number|license no\.?|ड्राइविंग)[\\s:.-]*([A-Z]{2}[-\\s]?\\d{2}[-\\s]?\\d{4}[-\\s]?\\d{7})',
                r'(?:dl|lic)[\\s:.-]*([A-Z]{2}\\d{13,15})',
                r'([A-Z]{2}[-]?\\d{13,14})'  # Indian DL format
            ],
            "Voter ID": [
                r'(?:voter id|epic no\.?|electoral|voter card|मतदाता)[\\s:.-]*([A-Z]{3}\\d{7})',
                r'(?:epic|voter)[\\s:.-]*([A-Z]{3}\\d{7})',
                r'\\b([A-Z]{3}\\d{7})\\b'  # Standalone voter ID
            ],
            "School": [
                r'(?:school|school name|institution|स्कूल)[\\s:.-]*([A-Z][a-zA-Z\\s,\\.]{5,100})',
                r'School[\\s:.-]*([A-Z][^\\n]{5,80})'
            ],
            "College": [
                r'(?:college|university|institution|कॉलेज)[\\s:.-]*([A-Z][a-zA-Z\\s,\\.]{5,100})',
                r'College[\\s:.-]*([A-Z][^\\n]{5,80})'
            ],
            "Roll No": [
                r'(?:roll no\.?|roll number|admission no\.?|student id)[\\s:.-]*([A-Z0-9/-]{5,20})',
                r'Roll[\\s:]*(?:No|Number)[\\s:.-]*([A-Z0-9/-]+)'
            ],
            "Class": [
                r'(?:class|grade|standard|std)[\\s:.-]*(\\d{1,2}(?:th|st|nd|rd)?|[IVX]+)',
                r'Class[\\s:.-]*(\\d{1,2}|[IVX]+)'
            ],
            "Marks": [
                r'(?:marks|score|cgpa|percentage)[\\s:.-]*(\\d{1,3}\\.?\\d{0,2}%?)',
                r'Marks[\\s:.-]*(\\d+)'
            ],
            "Occupation": [
                r'(?:occupation|profession|job|पेशा)[\\s:.-]*([A-Z][a-zA-Z\\s]{2,50})',
                r'Occupation[\\s:.-]*([A-Z][a-z\\s]+)'
            ],
            "Marital Status": [
                r'(?:marital status|marriage status|वैवाहिक)[\\s:.-]*((?:married|unmarried|single|divorced|widowed|widow))',
                r'Marital[\\s:]*Status[\\s:.-]*(\\w+)'
            ],
            "Spouse Name": [
                r'(?:spouse name|husband name|wife name|पति|पत्नी)[\\s:.-]*([A-Z][a-zA-Z\\s]+)',
                r'(?:Spouse|Husband|Wife)[\\s:.-]*([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)'
            ],
            "State": [
                r'(?:state|province|राज्य)[\\s:.-]*([A-Z][a-zA-Z\\s]{2,50})',
                r'State[\\s:.-]*([A-Z][a-z\\s]+)'
            ],
            "City": [
                r'(?:city|town|शहर)[\\s:.-]*([A-Z][a-zA-Z\\s]{2,50})',
                r'City[\\s:.-]*([A-Z][a-z\\s]+)'
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
            ],
            "Blood Group": [
                r'(?:فصيلة الدم|زمرة الدم)[\s:]*([ABO]{1,2}[+-])',
                r'\b([ABO]{1,2}[+-])\b'
            ]
        },
        "hi": {
            "Name": [
                r'(?:नाम|पूरा नाम|पहला नाम|दिया गया नाम)[\s:]*([\u0900-\u097F\s]+)',
                r'नाम[\s:]*([\u0900-\u097F\s]+)'
            ],
            "Surname": [
                r'(?:उपनाम|अंतिम नाम|कुल नाम)[\s:]*([\u0900-\u097F\s]+)',
                r'उपनाम[\s:]*([\u0900-\u097F\s]+)'
            ],
            "Date of Birth": [
                r'(?:जन्म तिथि|जन्मतिथि|जन्म की तारीख)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "Passport No": [
                r'(?:पासपोर्ट संख्या|पासपोर्ट नंबर)[\s:]*([A-Z0-9]{6,})'
            ],
            "Personal No": [
                r'(?:व्यक्तिगत संख्या|राष्ट्रीय पहचान|पहचान संख्या)[\s:]*([A-Z0-9]+)'
            ],
            "Phone": [
                r'(?:फोन|मोबाइल|दूरभाष|फोन नंबर)[\s:]*([+]?[\d\s\-()]{8,})'
            ],
            "Email": [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            "Address": [
                r'(?:पता|स्थान)[\s:]*([\u0900-\u097F0-9\s,.-]+)'
            ],
            "Issue Date": [
                r'(?:जारी तिथि|जारी करने की तिथि)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "Expiry Date": [
                r'(?:समाप्ति तिथि|समाप्त होने की तिथि)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "Nationality": [
                r'(?:राष्ट्रीयता)[\s:]*([\u0900-\u097F\s]+)'
            ],
            "Country": [
                r'(?:देश|राष्ट्र)[\s:]*([\u0900-\u097F\s]+)'
            ],
            "Issuing Office": [
                r'(?:जारी करने वाला कार्यालय|जारी करने वाली प्राधिकरण)[\s:]*([\u0900-\u097F\s]+)'
            ],
            "Height": [
                r'(?:ऊंचाई)[\s:]*(\d+\s*(?:सेमी|मी|cm|m))'
            ],
            "Sex": [
                r'(?:लिंग)[\s:]*([पुरुष|महिला|M|F])'
            ],
            "Place of Birth": [
                r'(?:जन्म स्थान)[\s:]*([\u0900-\u097F\s]+)'
            ],
            "Card No": [
                r'(?:कार्ड संख्या|कार्ड नंबर)[\s:]*([A-Z0-9]+)'
            ],
            "Blood Group": [
                r'(?:रक्त समूह|ब्लड ग्रुप)[\s:]*([ABO]{1,2}[+-])',
                r'\b([ABO]{1,2}[+-])\b'
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
            'Email': ['email', 'e-mail', 'email address', 'mail', 'email id'],
            'Personal No': ['id', 'id number', 'aadhaar', 'pan', 'personal no', 'personal number', 'national id'],
            'Passport No': ['passport', 'passport no', 'passport number', 'document no', 'document number'],
            'Card No': ['card no', 'card number', 'driving license', 'license number'],
            'Address': ['address', 'residence', 'location', 'street'],
            'City': ['city', 'town'],
            'State': ['state', 'province'],
            'Country': ['country', 'nation'],
            'Gender': ['gender', 'sex'],
            'Pincode': ['pincode', 'pin code', 'postal code', 'zip code', 'zip'],
            'Blood Group': ['blood group', 'blood type', 'b.g.', 'bg', 'blood'],
            # Birth Certificate Fields
            'Father Name': ['father name', 'fathers name', 'father', 'name of father', 'father\'s name'],
            'Mother Name': ['mother name', 'mothers name', 'mother', 'name of mother', 'mother\'s name'],
            'Certificate No': ['certificate no', 'certificate number', 'cert no', 'cert number', 'certificate', 'registration number'],
            'Registration No': ['registration no', 'registration number', 'reg no', 'reg number', 'registration'],
            'Date of Registration': ['date of registration', 'registration date', 'reg date', 'registered on', 'registration'],
            'Place of Issue': ['place of issue', 'issued at', 'issuing office', 'place', 'issue place'],
            'Religion': ['religion', 'relig'],
            'Pin Code': ['pin code', 'pincode', 'pin', 'postal code', 'zip code', 'zip'],
            'District': ['district', 'dist'],
            'Aadhaar': ['aadhaar', 'aadhar', 'aadhaar no', 'aadhar no', 'aadhaar number', 'aadhar number', 'uid'],
            'VID': ['vid', 'virtual id', 'virtual identity'],
            'Permanent Address': ['permanent address', 'permanent address of parents', 'perm address'],
            # Universal Document Fields
            'PAN': ['pan', 'pan no', 'pan number', 'pan card', 'permanent account number'],
            'Driving License': ['driving license', 'driving licence', 'dl', 'dl no', 'dl number', 'license'],
            'Voter ID': ['voter id', 'epic', 'epic no', 'electoral', 'voter card'],
            'School': ['school', 'school name', 'institution'],
            'College': ['college', 'university', 'institution'],
            'Roll No': ['roll no', 'roll number', 'admission no', 'student id'],
            'Class': ['class', 'grade', 'standard', 'std'],
            'Marks': ['marks', 'score', 'cgpa', 'percentage', 'result'],
            'Occupation': ['occupation', 'profession', 'job', 'work'],
            'Marital Status': ['marital status', 'marriage status', 'married'],
            'Spouse Name': ['spouse', 'spouse name', 'husband', 'wife', 'husband name', 'wife name']
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
            'Pincode': ['الرمز البريدي', 'صندوق البريد'],
            'Blood Group': ['فصيلة الدم', 'زمرة الدم', 'الدم']
        },
        "hi": {
            'Name': ['नाम', 'पूरा नाम', 'पहला नाम', 'अंतिम नाम', 'उपनाम', 'दिया गया नाम'],
            'Age': ['आयु', 'उम्र'],
            'Date of Birth': ['जन्म तिथि', 'जन्मतिथि', 'जन्म की तारीख'],
            'Phone': ['फोन', 'मोबाइल', 'फोन नंबर', 'संपर्क', 'मोबाइल नंबर', 'दूरभाष'],
            'Email': ['ईमेल', 'ई-मेल', 'ईमेल पता'],
            'Personal No': ['पहचान', 'पहचान संख्या', 'आधार', 'पैन', 'व्यक्तिगत संख्या', 'राष्ट्रीय पहचान'],
            'Passport No': ['पासपोर्ट', 'पासपोर्ट संख्या', 'पासपोर्ट नंबर'],
            'Card No': ['कार्ड संख्या', 'कार्ड नंबर', 'ड्राइविंग लाइसेंस', 'लाइसेंस नंबर'],
            'Address': ['पता', 'निवास', 'स्थान', 'गली'],
            'City': ['शहर', 'नगर'],
            'State': ['राज्य', 'प्रदेश'],
            'Country': ['देश', 'राष्ट्र'],
            'Gender': ['लिंग', 'जेंडर'],
            'Pincode': ['पिनकोड', 'पिन कोड', 'डाक कोड', 'जिप कोड'],
            'Blood Group': ['रक्त समूह', 'ब्लड ग्रुप', 'खून का समूह']
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
        elif self.current_language == "hi":
            return ['hi', 'en'] # Hindi usually needs English too
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
        },
        "hi": {
            "name": {
                "aliases": ["पूरा नाम", "पहला नाम", "अंतिम नाम", "उपनाम", "आवेदक का नाम"],
                "type": "text",
                "required": True,
                "weight": 1.0
            },
            "email": {
                "aliases": ["ईमेल पता", "ई-मेल", "ईमेल", "संपर्क ईमेल"],
                "type": "email",
                "required": True,
                "weight": 1.0
            },
            "phone": {
                "aliases": ["फोन", "मोबाइल", "दूरभाष", "फोन नंबर", "मोबाइल नंबर", "संपर्क नंबर"],
                "type": "tel",
                "required": True,
                "weight": 0.9
            },
            "address": {
                "aliases": ["पता", "निवास", "स्थान", "सड़क का पता", "घर का पता"],
                "type": "text",
                "required": True,
                "weight": 0.8
            },
            "city": {
                "aliases": ["शहर", "नगर"],
                "type": "text",
                "required": True,
                "weight": 0.7
            },
            "country": {
                "aliases": ["देश", "राष्ट्र"],
                "type": "text",
                "required": True,
                "weight": 0.7
            },
            "date_of_birth": {
                "aliases": ["जन्म तिथि", "जन्मतिथि", "जन्म की तारीख"],
                "type": "date",
                "required": True,
                "weight": 0.8
            },
            "education": {
                "aliases": ["शिक्षा", "योग्यता", "डिग्री", "विश्वविद्यालय", "कॉलेज", "स्कूल"],
                "type": "text",
                "required": False,
                "weight": 0.6
            },
            "experience": {
                "aliases": ["अनुभव", "कार्य अनुभव", "रोजगार", "नौकरी का इतिहास", "करियर"],
                "type": "text",
                "required": False,
                "weight": 0.7
            },
            "skills": {
                "aliases": ["कौशल", "तकनीकी कौशल", "योग्यताएँ", "क्षमताएँ"],
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
