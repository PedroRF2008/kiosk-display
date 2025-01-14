#!/bin/bash

# Install zenity if not present
if ! command -v zenity &> /dev/null; then
    sudo apt-get install -y zenity
fi

# Function to show notification
show_notification() {
    TITLE="$1"
    MESSAGE="$2"
    zenity --info \
        --title="$TITLE" \
        --text="$MESSAGE" \
        --width=400 \
        --timeout=5 \
        2>/dev/null &
}

# Function to show progress
show_progress() {
    MESSAGE="$1"
    (echo "0"; echo "$MESSAGE"; sleep 1) | zenity --progress \
        --title="Kiosk Update" \
        --text="Starting..." \
        --percentage=0 \
        --auto-close \
        --width=400 \
        2>/dev/null &
}

# Function to check internet connection
check_internet() {
    wget -q --spider http://google.com
    return $?
}

# Function to check for updates
check_updates() {
    echo "[UPDATE] Starting update check process..."
    show_notification "Kiosk Update" "Verificando atualizações..."
    GITHUB_REPO="PedroRF2008/kiosk-display"
    
    # Get current version from version.py
    CURRENT_VERSION=$(python3 -c "from version import VERSION; print(VERSION)")
    echo "[UPDATE] Current version: ${CURRENT_VERSION}"
    
    # Get latest release from GitHub
    echo "[UPDATE] Fetching latest version from GitHub..."
    LATEST_VERSION=$(curl -s "https://api.github.com/repos/${GITHUB_REPO}/releases/latest" | grep -Po '"tag_name": "v\K[^"]*')
    
    if [ -z "$LATEST_VERSION" ]; then
        echo "[UPDATE][ERROR] Failed to fetch latest version from GitHub"
        show_notification "Erro" "Falha ao verificar atualizações"
        return 1
    fi
    
    if [ "$LATEST_VERSION" = "$CURRENT_VERSION" ]; then
        echo "[UPDATE] Already running latest version ${CURRENT_VERSION}"
        show_notification "Kiosk Update" "Sistema já está atualizado (v${CURRENT_VERSION})"
        return 0
    fi
    
    echo "[UPDATE] New version available: ${LATEST_VERSION}"
    show_notification "Nova Atualização" "Instalando versão ${LATEST_VERSION}..."
    
    # Download update
    DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/download/v${LATEST_VERSION}/kiosk-v${LATEST_VERSION}.zip"
    UPDATE_DIR="/home/pedro/kiosk/updates"
    TEMP_DIR="/home/pedro/kiosk/updates/temp"
    KIOSK_ROOT="/home/pedro/kiosk"
    
    show_progress "Baixando atualização..."
    echo "[UPDATE] Creating update directory: ${UPDATE_DIR}"
    mkdir -p "${UPDATE_DIR}"
    mkdir -p "${TEMP_DIR}"
    
    echo "[UPDATE] Downloading new version from: ${DOWNLOAD_URL}"
    wget -O "${UPDATE_DIR}/update.zip" "${DOWNLOAD_URL}"
    echo "[UPDATE] Download completed"
    
    show_progress "Instalando atualização..."
    # Extract update to temporary directory first
    echo "[UPDATE] Extracting update files..."
    unzip "${UPDATE_DIR}/update.zip" -d "${TEMP_DIR}"
    
    # Update Python dependencies
    echo "[UPDATE] Updating Python dependencies..."
    cd "${KIOSK_ROOT}"
    source "${KIOSK_ROOT}/.venv/bin/activate"
    pip install -r "${TEMP_DIR}/requirements.txt"
    deactivate
    
    # Clean up old version and move new version into place
    echo "[UPDATE] Updating display directory..."
    sudo rm -rf "/home/pedro/kiosk/display"
    sudo mv "${TEMP_DIR}" "/home/pedro/kiosk/display"
    sudo rm -f "${UPDATE_DIR}/update.zip"
    
    # Fix permissions after moving files
    sudo chown -R pedro:pedro "/home/pedro/kiosk/display"
    sudo chmod -R 755 "/home/pedro/kiosk/display"
    
    # Reload systemd and restart service
    echo "[UPDATE] Reloading systemd and restarting service..."
    show_notification "Atualização Concluída" "Sistema atualizado para v${LATEST_VERSION}"
    sleep 5
    sudo systemctl restart kiosk.service
    exit 0
}

# Check internet connection and updates
echo "[STARTUP] Checking for internet connection..."
if check_internet; then
    echo "[STARTUP] Internet connection available"
    show_notification "Kiosk" "Conexão com internet estabelecida"
    echo "[STARTUP] Checking for updates..."
    check_updates
else
    echo "[STARTUP] No internet connection, skipping update check"
    show_notification "Aviso" "Sem conexão com internet"
fi

echo "[STARTUP] Starting kiosk application..."

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
KIOSK_ROOT="/home/pedro/kiosk"

# Kill any existing browser instances
pkill -f chromium
pkill -f unclutter

# Wait a moment for X to be ready
sleep 2

# Start unclutter with simpler settings (this worked before)
unclutter -idle 0.1 -root &

# Activate virtual environment and start Flask app
cd "$SCRIPT_DIR"
source "${KIOSK_ROOT}/.venv/bin/activate"
python app.py &

# Wait for Flask to start
sleep 5

# Start Chromium in kiosk mode with optimized video playback settings
DISPLAY=:0 chromium-browser \
    --noerrdialogs \
    --disable-infobars \
    --disable-translate \
    --disable-features=TranslateUI \
    --enable-gpu \
    --ignore-gpu-blocklist \
    --enable-hardware-acceleration \
    --disk-cache-dir=/dev/null \
    --disk-cache-size=1 \
    --remote-debugging-port=9222 \
    --remote-allow-origins=http://localhost:9222 \
    --autoplay-policy=no-user-gesture-required \
    --kiosk \
    --app=http://localhost:5000 