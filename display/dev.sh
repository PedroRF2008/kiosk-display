#!/bin/bash

# Kiosk Display Development Environment
# This script starts both Flask API and React development servers

echo "🚀 Starting Kiosk Display Development Environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if Node.js/npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm is required but not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if virtual environment exists
VENV_DIR="$SCRIPT_DIR/../.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Virtual environment not found, creating one..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r "$SCRIPT_DIR/requirements.txt" > /dev/null 2>&1

# Run the development server
python3 "$SCRIPT_DIR/dev-server.py"