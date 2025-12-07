"""
Configuration file for OCR Text Extraction & Verification System
"""

import os

# ============================================================================
# Language Configuration
# ============================================================================
SUPPORTED_LANGUAGES = ["en", "ar", "hi"]
SELECTED_LANGUAGE = "en"  # Default language: English

# ============================================================================
# MOSIP Pre-Registration Configuration
# ============================================================================

# MOSIP Server URL (collab.mosip.net is the official sandbox)
MOSIP_BASE_URL = "https://collab.mosip.net"

# Enable/disable MOSIP integration (set to False for mock mode)
MOSIP_ENABLED = False

# MOSIP Pre-Registration API endpoint
MOSIP_PREREG_URL = f"{MOSIP_BASE_URL}/preregistration/v1"

# MOSIP Authentication Credentials
MOSIP_CLIENT_ID = "mosip-prereg-client"
MOSIP_CLIENT_SECRET = "mosip"

# Request timeout in seconds
MOSIP_TIMEOUT = 30
