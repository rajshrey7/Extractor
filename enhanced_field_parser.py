"""
Enhanced Field Parser with Detailed Logging
This module improves field extraction from birth certificates and complex documents
"""
import re
import difflib
from typing import Dict, List


def parse_text_to_json_with_logging(text: str, blocks_data: List[Dict], 
                                     patterns: Dict, STANDARD_FIELDS: Dict,
                                     extract_spatial_key_values_func) -> tuple:
    """
    Enhanced parsing with comprehensive logging to debug field extraction issues.
    
    Args:
        text: Full extracted text
        blocks_data: List of text blocks with bounding boxes
        patterns: Regex patterns for field matching
        STANDARD_FIELDS: Standard field variations dictionary
        extract_spatial_key_values_func: Function for spatial extraction
        
    Returns:
        Tuple of (extracted_fields, field_metadata)
    """
    
    result = {}
    lines = text.split('\n')
    
    # Helper function to find closest standard key
    def get_standard_key(ocr_key):
        ocr_key = ocr_key.lower().strip()
        best_match = None
        max_len = 0
        
        # Direct check with "best match" logic
        for std_key, variations in STANDARD_FIELDS.items():
            if ocr_key in variations:
                return std_key
            for var in variations:
                if var in ocr_key:
                    if len(var) > max_len:
                        max_len = len(var)
                        best_match = std_key
        
        if best_match:
            return best_match
        
        # Fuzzy check
        all_variations = []
        for variations in STANDARD_FIELDS.values():
            all_variations.extend(variations)
            
        matches = difflib.get_close_matches(ocr_key, all_variations, n=1, cutoff=0.7)
        if matches:
            match = matches[0]
            for std_key, variations in STANDARD_FIELDS.items():
                if match in variations:
                    return std_key
        return None

    # ============================================================
    # DEBUGGING OUTPUT
    # ============================================================
    print(f"\n{'='*60}")
    print(f"📊 FIELD EXTRACTION DEBUGGING")
    print(f"{'='*60}")
    print(f"📝 Total text length: {len(text)} chars")
    print(f"📝 Total lines: {len(lines)}")
    print(f"📦 Total blocks: {len(blocks_data) if blocks_data else 0}")
    
    # Show first 5 lines of text for context
    print(f"\n📄 First 5 lines of extracted text:")
    for i, line in enumerate(lines[:5]):
        print(f"   Line {i+1}: {line[:80]}{'...' if len(line) > 80 else ''}")
    
    # ============================================================
    # STEP 1: SPATIAL EXTRACTION
    # ============================================================
    if blocks_data:
        print(f"\n🔍 STEP 1: Running Spatial Extraction...")
        try:
            spatial_results = extract_spatial_key_values_func(blocks_data, STANDARD_FIELDS)
            if spatial_results:
                print(f"✅ Spatial extraction found {len(spatial_results)} fields:")
                for key, value in spatial_results.items():
                    display_value = value[:60] + "..." if len(value) > 60 else value
                    print(f"   • {key}: {display_value}")
                result.update(spatial_results)
            else:
                print("⚠️ Spatial extraction found 0 fields")
        except Exception as e:
            print(f"❌ Spatial extraction error: {e}")
            import traceback
            traceback.print_exc()
    
    # ============================================================
    # STEP 2: REGEX PATTERN MATCHING
    # ============================================================
    print(f"\n🔍 STEP 2: Regex Pattern Matching...")
    regex_found = 0
    for field, field_patterns in patterns.items():
        if field in result:
            continue  # Skip if already found
            
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                value = re.sub(r'[^\w\s@./-\u0600-\u06FF]', '', value).strip()
                if value and len(value) > 1:
                    result[field] = value
                    regex_found += 1
                    display_value = value[:50] + "..." if len(value) > 50 else value
                    print(f"   ✅ Regex found {field}: {display_value}")
                    break
    print(f"✅ Regex matching found {regex_found} fields")
    
    # ============================================================
    # STEP 3: BLOCK-BASED REGEX
    # ============================================================
    if blocks_data:
        print(f"\n🔍 STEP 3: Block-based Regex...")
        block_found = 0
        for block in blocks_data:
            block_text = block.get("text", "")
            if not block_text:
                continue
            
            for field, field_patterns in patterns.items():
                if field in result:
                    continue
                for pattern in field_patterns:
                    match = re.search(pattern, block_text, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        value = re.sub(r'[^\w\s@./-\u0600-\u06FF]', '', value).strip()
                        if value and len(value) > 1:
                            result[field] = value
                            block_found += 1
                            break
        print(f"✅ Block-based regex found {block_found} fields")
    
    # ============================================================
    # STEP 4: LINE-BY-LINE PARSING (ENHANCED)
    # ============================================================
    print(f"\n🔍 STEP 4: Line-by-Line Parsing...")
    
    # Count lines with different separators
    lines_with_colon = [line for line in lines if ':' in line]
    lines_with_dash = [line for line in lines if '.-' in line]
    lines_with_space = [line for line in lines if '  ' in line]  # double space
    
    print(f"   Found {len(lines_with_colon)} lines with ':' separator")
    print(f"   Found {len(lines_with_dash)} lines with '.-' separator")
    print(f"   Found {len(lines_with_space)} lines with double-space separator")
    
    line_found = 0
    custom_fields = 0
    
    for line_idx, line in enumerate(lines):
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key_raw = parts[0].strip()
                value = parts[1].strip()
                
                # Skip empty values
                if not value or len(value) < 1:
                    continue
                
                # Clean value
                value = value.replace('"', '').replace("'", "").strip(" .,!")
                val_lower = value.lower()
                
                # Email fixes
                if '@' in value or 'gmail' in val_lower:
                    value = value.replace('Gymail', 'gmail').replace(' ', '')
                    if '@' not in value and 'gmail' in value:
                        value = value.replace('gmail', '@gmail')
                
                std_key = get_standard_key(key_raw)
                
                if std_key:
                    if std_key not in result:
                        result[std_key] = value
                        line_found += 1
                        display_value = value[:50] + "..." if len(value) > 50 else value
                        print(f"   ✅ Line {line_idx+1} found {std_key}: {display_value}")
                    elif std_key == 'Name':
                        current_val = result[std_key]
                        if len(current_val) > len(value) + 10 and value in current_val:
                             result[std_key] = value
                             print(f"   🔄 Updated {std_key}: {value[:50]}...")
                else:
                    clean_key = key_raw.title().replace('_', ' ')
                    if clean_key not in result and len(clean_key) > 2:
                        result[clean_key] = value
                        custom_fields += 1
                        if custom_fields <= 10:  # Log first 10 custom fields
                            display_value = value[:40] + "..." if len(value) > 40 else value
                            print(f"   📝 Custom field '{clean_key}': {display_value}")
    
    print(f"✅ Line parser found {line_found} standard fields, {custom_fields} custom fields")
    
    # ============================================================
    # FINAL CLEANUP
    # ============================================================
    print(f"\n🧹 Running Final Cleanup...")
    cleaned_result = {}
    field_metadata = {}
    
    # Normalize keys
    for key, value in result.items():
        std_key = get_standard_key(key)
        final_key = std_key if std_key else key.title().replace('_', ' ')
        
        if final_key in cleaned_result:
            if 'Email' in final_key and '@' in value and '@' not in cleaned_result[final_key]:
                cleaned_result[final_key] = value
        else:
            cleaned_result[final_key] = value

    # Build metadata
    for key, value in cleaned_result.items():
        if value and len(value.strip()) > 0:
            confidence = 0.95 if blocks_data else 0.85
            source = "spatial" if blocks_data else "regex"
            field_metadata[key] = {"confidence": confidence, "source": source}
    
    # Strip trailing field names from values
    all_field_variations = []
    for variations in STANDARD_FIELDS.values():
        all_field_variations.extend([v.lower() for v in variations])
    
    cleanup_count = 0
    for key, value in list(cleaned_result.items()):
        if not value or not isinstance(value, str):
            continue
        value_cleaned = value.replace('\n', ' ').replace('\r', ' ').strip()
        
        for field_name in all_field_variations:
            if value_cleaned.lower().endswith(field_name):
                potential_clean = value_cleaned[:-(len(field_name))].strip()
                if len(potential_clean) > 2:
                    cleaned_result[key] = potential_clean
                    cleanup_count += 1
                    if cleanup_count <= 5:  # Log first 5 cleanups
                        print(f"   ✂️ Cleaned '{key}': removed trailing '{field_name}'")
    
    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    print(f"\n{'='*60}")
    print(f"📊 EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Total fields extracted: {len(cleaned_result)}")
    print(f"📋 Fields found:")
    for key in sorted(cleaned_result.keys()):
        value = cleaned_result[key]
        display_value = value[:50] + "..." if len(value) > 50 else value
        print(f"   • {key}: {display_value}")
    print(f"{'='*60}\n")
    
    return cleaned_result, field_metadata
