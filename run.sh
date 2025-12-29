#!/bin/bash

echo "================================"
echo "Street Signal - Quick Start"
echo "================================"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check if USER_AGENT is configured
if grep -q "contact@example.com" config.py; then
    echo
    echo "================================"
    echo "WARNING: Please update USER_AGENT in config.py"
    echo "================================"
    echo
fi

# Run the application
echo
echo "Starting Street Signal..."
echo "Open your browser to: http://127.0.0.1:5000"
echo
echo "Press Ctrl+C to stop the server"
echo
python app.py
