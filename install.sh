#!/bin/bash
# install.sh - Setup script for Web Crawler project

echo "Installing Web Crawler..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Check if Python is installed
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "Python not found. Please install Python 3.8 or later."
    exit 1
fi

# Check Python version
PY_VERSION=$($PYTHON -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$PY_VERSION < 3.8" | bc) -eq 1 ]]; then
    echo "Python 3.8 or later is required. Found version $PY_VERSION"
    exit 1
fi

echo "Using Python $PY_VERSION"

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON -m venv venv

# Activate virtual environment
if [[ "$OS" == "windows" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p crawler_data screenshots downloads logs templates static

# Check if Chrome is installed (for Selenium)
echo "Checking for Chrome browser..."
if [[ "$OS" == "linux" ]]; then
    if ! command -v google-chrome &>/dev/null; then
        echo "Chrome not found. Would you like to install Chrome? (y/n)"
        read -r install_chrome
        if [[ "$install_chrome" == "y" ]]; then
            echo "Installing Chrome..."
            wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
            echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google.list
            sudo apt-get update
            sudo apt-get install -y google-chrome-stable
        else
            echo "Selenium-based crawling will not work without Chrome."
        fi
    else
        echo "Chrome is installed."
    fi
elif [[ "$OS" == "mac" ]]; then
    if ! [ -d "/Applications/Google Chrome.app" ]; then
        echo "Chrome not found. Please install Chrome for Selenium-based crawling."
    else
        echo "Chrome is installed."
    fi
elif [[ "$OS" == "windows" ]]; then
    if ! [ -d "/c/Program Files/Google/Chrome/Application/chrome.exe" ] && \
       ! [ -d "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" ]; then
        echo "Chrome not found. Please install Chrome for Selenium-based crawling."
    else
        echo "Chrome is installed."
    fi
fi

# Initialize database
echo "Initializing database..."
$PYTHON -c "from database_manager import DatabaseManager; DatabaseManager()"

echo "Web Crawler installation complete!"
echo ""
echo "To run the web interface:"
echo "  1. Activate the virtual environment:"
if [[ "$OS" == "windows" ]]; then
    echo "     source venv/Scripts/activate"
else
    echo "     source venv/bin/activate"
fi
echo "  2. Start the server:"
echo "     python main.py"
echo ""
echo "Or use the command-line interface:"
echo "  python cli.py --help"
echo ""
echo "Enjoy crawling!"