"""
Configuration file for API keys
"""
import os

# OpenRouter API Key for AI models (Optional)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Llama Cloud API Key for resume parsing (Optional)
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", "")

# Available AI models
OPENROUTER_MODELS = {
    "Mistral 7B Instruct": "mistralai/mistral-7b-instruct:free",
    "DeepSeek R1": "deepseek/deepseek-r1-zero:free",
    "MythoMax L2 13B": "gryphe/mythomax-l2-13b",
    "Llama 2 70B": "meta-llama/llama-2-70b-chat:free",
    "Claude 2.1": "anthropic/claude-2.1",
    "GPT-4": "openai/gpt-4",
    "GPT-3.5 Turbo": "openai/gpt-3.5-turbo"
}

# Default model
DEFAULT_MODEL = "gryphe/mythomax-l2-13b"

# Google Vision API Key (Removed - using offline TrOCR)
# GOOGLE_VISION_API_KEY = "REMOVED"

# OpenAI API Key (deprecated - using Google Vision instead)
OPENAI_API_KEY = None

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
