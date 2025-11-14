"""
Configuration file for API keys
"""
import os

# OpenRouter API Key for AI models
OPENROUTER_API_KEY = "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"

# Llama Cloud API Key for resume parsing
LLAMA_CLOUD_API_KEY = "llx-gPvqEiZkpooRYYDnS1dKLGGoCpBXK9YUeak5ZqPqiIWfpESB"

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

# Google Vision API Key for document parsing and OCR
GOOGLE_VISION_API_KEY = "AIzaSyBD7oL7NTKaJrrWtS7P224BCAGm0qScZW4"

# OpenAI API Key (deprecated - using Google Vision instead)
OPENAI_API_KEY = None
