#!/bin/bash

echo "=== Cloud Clipboard Installation ==="
echo "Installing dependencies for macOS..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $PYTHON_VERSION"

# Install pip dependencies
echo "Installing Python packages..."
if python3 -m pip install -r requirements.txt; then
    echo "Dependencies installed successfully"
else
    echo "Failed to install dependencies"
    echo "You may need to run: pip3 install -r requirements.txt"
    exit 1
fi

# Make the app executable
chmod +x app.py

echo ""
echo "Installation complete!"
echo ""
echo "To run Cloud Clipboard:"
echo "  python3 app.py"
echo ""
echo "The app will appear in your system tray with clipboard sharing options."