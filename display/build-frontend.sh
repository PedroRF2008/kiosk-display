#!/bin/bash

# Kiosk Display Frontend Build Script
# Builds React app for production and prepares it for Flask serving

set -e  # Exit on any error

echo "🏗️  Building Kiosk Display Frontend for Production"
echo "=================================================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
STATIC_DIR="$SCRIPT_DIR/static"
BUILD_OUTPUT_DIR="$STATIC_DIR/build"

# Check if Node.js/npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm is required but not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Change to frontend directory
cd "$FRONTEND_DIR"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found in frontend directory"
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
else
    echo "✅ Frontend dependencies found"
fi

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf dist/

# Build React app for production
echo "⚛️  Building React app for production..."
npm run build

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "❌ Build failed - dist directory not created"
    exit 1
fi

# Create static directory if it doesn't exist
mkdir -p "$STATIC_DIR"

# Remove previous build from static directory
if [ -d "$BUILD_OUTPUT_DIR" ]; then
    echo "🧹 Removing previous build from static directory..."
    rm -rf "$BUILD_OUTPUT_DIR"
fi

# Copy build to static directory (Vite outputs to 'dist' instead of 'build')
echo "📁 Copying build files to static directory..."
cp -r dist "$BUILD_OUTPUT_DIR"

# Update permissions
echo "🔐 Setting correct permissions..."
chmod -R 755 "$BUILD_OUTPUT_DIR"

# Get build size
BUILD_SIZE=$(du -sh "$BUILD_OUTPUT_DIR" | cut -f1)

echo ""
echo "✅ Build completed successfully!"
echo "=================================================="
echo "📊 Build size: $BUILD_SIZE"
echo "📁 Build location: $BUILD_OUTPUT_DIR"
echo "🌐 Files ready for production serving"
echo ""
echo "Next steps:"
echo "1. Test production build: python app.py"
echo "2. Visit http://localhost:5000 to test"
echo "3. Create release package when ready"
echo "=================================================="