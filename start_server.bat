@echo off
echo ============================================================
echo OCR Text Extraction Server Startup
echo ============================================================
echo.
echo Checking setup...
python test_setup.py
echo.
echo ============================================================
echo Starting server...
echo ============================================================
echo.
python app.py
pause

