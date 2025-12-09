#!/bin/bash
# Setup virtual environment for Engram backend

set -e

echo "=========================================="
echo "Setting up Python Virtual Environment"
echo "=========================================="
echo ""

# Check if venv already exists
if [ -d "venv" ]; then
    echo "✓ Virtual environment already exists"
    echo ""
    echo "To activate:"
    echo "  source venv/bin/activate"
    echo ""
    read -p "Recreate virtual environment? (y/n): " RECREATE
    if [[ $RECREATE == "y" ]]; then
        rm -rf venv
    else
        echo "Using existing venv"
        exit 0
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

echo "✓ Virtual environment created"
echo ""

# Activate and install dependencies
echo "Installing dependencies..."
source venv/bin/activate

cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "To use the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "Then you can:"
echo "  - Run tests: ./test-voicelive.sh"
echo "  - Start backend: cd backend && uvicorn backend.api.main:app --reload"
echo ""

