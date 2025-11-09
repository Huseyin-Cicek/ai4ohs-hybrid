#!/bin/bash
#
# AI4OHS Hybrid - Setup Script
# This script sets up the development/production environment
#

set -e

echo "================================================="
echo "AI4OHS Hybrid - Setup Script"
echo "================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if Python is 3.8+
required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "✗ Error: Python 3.8 or higher is required"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip -q
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp config/example.env .env
    echo "✓ .env file created"
    echo "⚠ Please edit .env file with your configuration"
else
    echo "✓ .env file already exists"
fi

# Create data directory
if [ ! -d "data" ]; then
    echo ""
    echo "Creating data directory..."
    mkdir -p data/vector_db
    echo "✓ Data directory created"
else
    echo "✓ Data directory already exists"
fi

# Test installation
echo ""
echo "Testing installation..."
python main.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Installation successful!"
else
    echo "✗ Installation test failed"
    exit 1
fi

echo ""
echo "================================================="
echo "Setup Complete!"
echo "================================================="
echo ""
echo "Quick Start:"
echo "  1. Activate virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run interactive mode:"
echo "     python main.py"
echo ""
echo "  3. Try a query:"
echo "     python main.py --query 'What are risk assessment requirements?'"
echo ""
echo "  4. Start API server:"
echo "     python main.py --api"
echo ""
echo "  5. View documentation:"
echo "     cat docs/USER_GUIDE.md"
echo ""
echo "For more information, see README.md"
echo ""
