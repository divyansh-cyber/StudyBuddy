@echo off
REM StudyBuddy Setup Script for Windows
REM This script helps set up the StudyBuddy environment

echo ========================================
echo        StudyBuddy AI Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is installed
python --version

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is not available
    echo Please install pip
    pause
    exit /b 1
)

echo ✅ pip is available

REM Install requirements
echo.
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Failed to install requirements
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Check for .env file
if not exist ".env" (
    echo.
    echo ⚠️  .env file not found
    echo Creating .env template...
    echo GOOGLE_API_KEY=your_gemini_api_key_here > .env
    echo.
    echo 📝 Please edit .env file and add your Google Gemini API key
    echo You can get an API key from: https://makersuite.google.com/app/apikey
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo 🚀 To start StudyBuddy:
echo.
echo 1. Start the backend server:
echo    cd backend
echo    python app.py
echo.
echo 2. In a new terminal, start the frontend:
echo    streamlit run frontend/streamlit_app.py
echo.
echo 3. Open your browser to: http://localhost:8501
echo.
echo 📖 For more information, see README.md
echo.
pause