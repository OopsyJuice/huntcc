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

# Check for compatible Python version
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
    echo "Error: Python 3.8 or higher is required"
    echo "You have Python $PYTHON_VERSION"
    exit 1
fi

# Special handling for Python 3.13
if [ "$PYTHON_VERSION" = "3.13" ]; then
    echo "Python 3.13 detected - using updated package versions for compatibility"
fi

# Upgrade pip first to handle newer packages
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install dependencies with retry for Python 3.13 compatibility
echo "Installing Python packages..."
if python3 -m pip install -r requirements.txt; then
    echo "Dependencies installed successfully"
else
    echo "Installation failed. Trying alternative approach..."
    echo "Installing packages individually..."
    
    # Try installing packages one by one with fallbacks
    python3 -m pip install fastapi==0.104.1 || echo "FastAPI install failed"
    python3 -m pip install uvicorn==0.24.0 || echo "Uvicorn install failed"
    python3 -m pip install pydantic==2.5.0 || echo "Pydantic install failed"
    python3 -m pip install python-multipart==0.0.6 || echo "Multipart install failed"
    python3 -m pip install pyperclip==1.8.2 || echo "Pyperclip install failed"
    python3 -m pip install requests==2.31.0 || echo "Requests install failed"
    python3 -m pip install pystray==0.19.4 || echo "Pystray install failed"
    
    # Try newer Pillow version for Python 3.13
    if [ "$PYTHON_VERSION" = "3.13" ]; then
        python3 -m pip install "Pillow>=10.4.0" || echo "Pillow install failed - trying system version"
    else
        python3 -m pip install "Pillow>=10.0.0" || echo "Pillow install failed"
    fi
    
    # Optional keyboard package (may fail on some systems)
    python3 -m pip install keyboard==0.13.5 || echo "Keyboard package failed (optional)"
    
    echo "Individual package installation completed"
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
echo ""
if [ "$PYTHON_VERSION" = "3.13" ]; then
    echo "Note: Python 3.13 is very new. If you encounter issues, consider using Python 3.11 or 3.12."
fi