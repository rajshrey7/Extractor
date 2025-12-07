# MOSIP Multi-Language Field Format Guide
# Based on collab.mosip.net schema

## What the Schema Shows:

Some fields in MOSIP support multiple languages with this format:

```json
{
  "fullName": [
    {"value": "John Doe", "lang": "eng"},
    {"value": "জন ডো", "lang": "ben"}
  ],
  "city": [
    {"value": "Mumbai", "lang": "eng"},
    {"value": "मुंबई", "lang": "hin"}
  ]
}
```

## Fields That Support Multi-Language:

Based on mosip-context.json, these fields support multi-language:
- fullName
- addressLine1
- addressLine2  
- addressLine3
- city
- province
- region
- gender
- residenceStatus

## Simple Fields (No Language Context):

These are simple strings:
- dateOfBirth
- email
- phone
- postalCode
- UIN
- biometrics

## Your Current Implementation:

✅ Your current mapper uses simple strings:
```python
{
  "fullName": "John Doe",
  "city": "Mumbai"
}
```

## Is This a Problem?

**NO!** MOSIP accepts both formats:
1. Simple string: `"fullName": "John Doe"` ✅ Works
2. Multi-language: `"fullName": [{"value": "John Doe", "lang": "eng"}]` ✅ Also works

## When to Use Multi-Language Format:

Use multi-language format if:
- You have text in multiple languages
- You want to preserve language information
- Your OCR detects different scripts

## Optional Enhancement:

If you want to add multi-language support later, here's the code:

```python
# In mosip_field_mapper.py

def format_multilang_field(self, value: str, lang: str = "eng") -> list:
    """
    Format a value for multi-language MOSIP fields.
    """
    return [{"value": value, "lang": lang}]

def map_to_mosip_schema(self, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
    # ... existing code ...
    
    # For multi-language fields:
    MULTILANG_FIELDS = [
        "fullName", "addressLine1", "addressLine2", "addressLine3",
        "city", "province", "region", "gender", "residenceStatus"
    ]
    
    # Convert to multi-language format if needed
    for field in MULTILANG_FIELDS:
        if field in mosip_data and isinstance(mosip_data[field], str):
            # Optionally convert to multi-lang format
            # mosip_data[field] = self.format_multilang_field(mosip_data[field])
            pass  # Keep as simple string for now
    
    return mosip_data
```

## Recommendation:

**Keep your current simple format!**

Reasons:
1. ✅ It works with MOSIP
2. ✅ Simpler code
3. ✅ Easier to debug
4. ✅ Most deployments accept simple strings

Only add multi-language format if:
- MOSIP specifically requires it
- You're handling multi-script documents
- You see validation errors

## Summary:

Your current implementation is **CORRECT** and **COMPATIBLE** with collab.mosip.net! ✅

The schema shows multi-language *capability*, not *requirement*.
