#!/bin/bash

# StudyBuddy Setup Script for Linux/Mac
# This script helps set up the StudyBuddy environment

echo "========================================"
echo "       StudyBuddy AI Setup Script"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "✅ Python is installed"
python3 --version

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not available"
    echo "Please install pip3"
    exit 1
fi

echo "✅ pip3 is available"

# Install requirements
echo
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install requirements"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Check for .env file
if [ ! -f ".env" ]; then
    echo
    echo "⚠️  .env file not found"
    echo "Creating .env template..."
    echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env
    echo
    echo "📝 Please edit .env file and add your Google Gemini API key"
    echo "You can get an API key from: https://makersuite.google.com/app/apikey"
fi

echo
echo "🎉 Setup completed successfully!"
echo
echo "🚀 To start StudyBuddy:"
echo
echo "1. Start the backend server:"
echo "   cd backend"
echo "   python3 app.py"
echo
echo "2. In a new terminal, start the frontend:"
echo "   streamlit run frontend/streamlit_app.py"
echo
echo "3. Open your browser to: http://localhost:8501"
echo
echo "📖 For more information, see README.md"
echo