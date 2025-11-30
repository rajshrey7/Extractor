"""
Setup configuration for OCR Text Extraction & Verification System
"""
from setuptools import setup, find_packages

setup(
    name="ocr-extractor",
    version="1.0.0",
    description="OCR Text Extraction & Verification System with MOSIP Integration",
    author="Your Name",
    python_requires=">=3.10",  # Ensures Python 3.10+
    packages=find_packages(),
    install_requires=[
        # Core API
        "fastapi",
        "uvicorn",
        "python-multipart",
        "requests",
        
        # Image Processing
        "opencv-python",
        "numpy",
        "Pillow",
        "PyMuPDF",
        
        # OCR & ML Models
        "paddlepaddle",
        "paddleocr",
        "transformers>=4.30.0",
        "torch==2.6.0",
        
        # Utilities
        "aiofiles",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
)
