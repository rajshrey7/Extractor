"""
Configuration file for application settings
"""
import os

# Language Configuration
SUPPORTED_LANGUAGES = ["en", "ar"]
SELECTED_LANGUAGE = "en"

# MOSIP Pre-Registration Configuration
MOSIP_ENABLED = False  # Set to True when you have MOSIP server credentials
MOSIP_BASE_URL = "https://dev2.mosip.net"
MOSIP_PREREG_URL = f"{MOSIP_BASE_URL}/preregistration/v1"
MOSIP_CLIENT_ID = "mosip-prereg-client"
MOSIP_CLIENT_SECRET = ""  # Add your secret here
MOSIP_TIMEOUT = 30
