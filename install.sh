#!/bin/bash

# Exit on any error
set -e

echo "[INSTALL] Starting Kiosk Installation..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "[INSTALL][ERROR] Please run as root (sudo)"
    exit 1
fi

# Variables
KIOSK_ROOT="/home/kiosk/kiosk"
DISPLAY_DIR="${KIOSK_ROOT}/display"
GITHUB_REPO="PedroRF2008/kiosk-display"

echo "[INSTALL] Installing dependencies..."
apt-get install -y chromium-browser x11-xserver-utils unclutter wget unzip curl zenity wireless-tools libaio1 fonts-noto-color-emoji

echo "[INSTALL] Fetching latest version information..."
KIOSK_VERSION=$(curl -s "https://api.github.com/repos/${GITHUB_REPO}/releases/latest" | grep -Po '"tag_name": "v\K[^"]*')

if [ -z "$KIOSK_VERSION" ]; then
    echo "[INSTALL][ERROR] Failed to fetch latest version from GitHub"
    exit 1
fi

echo "[INSTALL] Latest version: ${KIOSK_VERSION}"

echo "[INSTALL] Creating directory structure..."
mkdir -p "${KIOSK_ROOT}/static/media" "${KIOSK_ROOT}/static/display" "${KIOSK_ROOT}/cache" "${KIOSK_ROOT}/.venv"

echo "[INSTALL] Downloading latest release (v${KIOSK_VERSION})..."
RELEASE_URL="https://github.com/${GITHUB_REPO}/releases/download/v${KIOSK_VERSION}/kiosk-v${KIOSK_VERSION}.zip"

echo "[INSTALL] Download URL: ${RELEASE_URL}"
wget -O /tmp/kiosk.zip "${RELEASE_URL}"

echo "[INSTALL] Extracting release to ${DISPLAY_DIR}..."
mkdir -p "${DISPLAY_DIR}"
unzip /tmp/kiosk.zip -d "${DISPLAY_DIR}"

echo "[INSTALL] Creating .env file..."
cat > "${KIOSK_ROOT}/.env" << EOL
# Firebase Configuration
DEVICE_KEY=your-device-key
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-key-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=your-cert-url

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key

# OpenWeather Configuration
OPENWEATHER_API_KEY=your-api-key
OPENWEATHER_CITY=your-city
EOL

echo "[INSTALL] Setting up Python virtual environment..."
cd "${KIOSK_ROOT}"
python3 -m venv .venv
source .venv/bin/activate

echo "[INSTALL] Setting up Oracle Instant Client..."
# Create directory for Oracle Client
mkdir -p /opt/oracle
cd /opt/oracle

# Download Oracle Instant Client (Basic Light) for ARM64
wget https://download.oracle.com/otn_software/linux/instantclient/191000/instantclient-basiclite-linux.arm64-19.10.0.0.0dbru.zip

# Extract the files
unzip instantclient-basiclite-linux.arm64-19.10.0.0.0dbru.zip
rm instantclient-basiclite-linux.arm64-19.10.0.0.0dbru.zip

# Create symbolic links
echo /opt/oracle/instantclient_19_10 > /etc/ld.so.conf.d/oracle-instantclient.conf
ldconfig

# Set environment variables
echo 'export LD_LIBRARY_PATH="/opt/oracle/instantclient_19_10:$LD_LIBRARY_PATH"' > /etc/profile.d/oracle.sh
echo 'export ORACLE_HOME="/opt/oracle/instantclient_19_10"' >> /etc/profile.d/oracle.sh
chmod +x /etc/profile.d/oracle.sh
source /etc/profile.d/oracle.sh

# Return to kiosk directory
cd "${KIOSK_ROOT}"

pip install -r "${DISPLAY_DIR}/requirements.txt"
deactivate

echo "[INSTALL] Downloading and setting up background wallpaper..."
BACKGROUND_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/main/background.png"
BACKGROUND_PATH="${KIOSK_ROOT}/static/background.png"

# Download the background image
wget -O "${BACKGROUND_PATH}" "${BACKGROUND_URL}"

echo "[INSTALL] Downloading logo..."
LOGO_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/main/static/display/logo.png"
LOGO_PATH="${KIOSK_ROOT}/static/display/logo.png"

# Create directory if it doesn't exist and download the logo
mkdir -p "${KIOSK_ROOT}/static/display"
wget -O "${LOGO_PATH}" "${LOGO_URL}"

# Ensure pcmanfm is installed (default file manager in Raspberry Pi OS that handles desktop)
apt-get install -y pcmanfm

# Set the background wallpaper - Modified to check for display
if [ -n "$DISPLAY" ]; then
    su - kiosk -c "pcmanfm --set-wallpaper ${BACKGROUND_PATH}"
else
    echo "[INSTALL] Warning: No display available. Wallpaper will be set on next boot."
fi

# Create autostart directory if it doesn't exist
mkdir -p /home/kiosk/.config/autostart

# Modified desktop entry to be more robust
cat > /home/kiosk/.config/autostart/wallpaper.desktop << EOL
[Desktop Entry]
Type=Application
Name=Set Wallpaper
Exec=bash -c 'sleep 5 && pcmanfm --set-wallpaper "${BACKGROUND_PATH}"'
Hidden=false
X-GNOME-Autostart-enabled=true
EOL

# Set proper ownership
chown -R kiosk:kiosk /home/kiosk/.config/autostart

echo "[INSTALL] Setting up systemd service..."
cp "${DISPLAY_DIR}/kiosk.service" /etc/systemd/system/
chmod 644 /etc/systemd/system/kiosk.service

echo "[INSTALL] Setting permissions..."
chown -R kiosk:kiosk "${KIOSK_ROOT}"
chmod +x "${DISPLAY_DIR}/start_kiosk.sh"

echo "[INSTALL] Starting kiosk service..."
systemctl daemon-reload
systemctl enable kiosk.service

echo "[INSTALL] Cleaning up..."
rm /tmp/kiosk.zip

echo "[INSTALL] Setting up D-Bus directories..."
mkdir -p /run/user/1000
chown kiosk:kiosk /run/user/1000
chmod 700 /run/user/1000

# Ensure D-Bus is running for the user
loginctl enable-linger kiosk

echo "[INSTALL] Setting up custom boot splash..."

# Install plymouth if not already installed
apt-get install -y plymouth

# Step 1: Remove Rainbow Screen
echo "disable_splash=1" >> /boot/config.txt

# Step 2: Remove text message under splash image
PLYMOUTH_SCRIPT="/usr/share/plymouth/themes/pix/pix.script"
# Backup original script
cp "${PLYMOUTH_SCRIPT}" "${PLYMOUTH_SCRIPT}.backup"
# Comment out the message sprite lines
sed -i '/message_sprite = Sprite();/s/^/#/' "${PLYMOUTH_SCRIPT}"
sed -i '/message_sprite.SetPosition/s/^/#/' "${PLYMOUTH_SCRIPT}"
sed -i '/my_image = Image.Text/s/^/#/' "${PLYMOUTH_SCRIPT}"
sed -i '/message_sprite.SetImage/s/^/#/' "${PLYMOUTH_SCRIPT}"

# Step 3: Modify boot parameters
CMDLINE="/boot/cmdline.txt"
# Backup original cmdline
cp "${CMDLINE}" "${CMDLINE}.backup"
# Replace console=tty1 with console=tty3 and add other parameters
sed -i 's/console=tty1/console=tty3/' "${CMDLINE}"
sed -i 's/$/ splash quiet plymouth.ignore-serial-consoles logo.nologo vt.global_cursor_default=0/' "${CMDLINE}"

# Replace splash image with our background
cp "${BACKGROUND_PATH}" /usr/share/plymouth/themes/pix/splash.png

# Remove the old splashscreen service if it exists
if [ -f "/etc/systemd/system/splashscreen.service" ]; then
    systemctl disable splashscreen
    rm /etc/systemd/system/splashscreen.service
fi

# Update initramfs to apply changes
update-initramfs -u

# Add GPU memory configuration
echo "gpu_mem=128" | sudo tee -a /boot/config.txt

# Enable hardware video decoding
echo "decode_MPG2=0x0" | sudo tee -a /boot/config.txt
echo "decode_WVC1=0x0" | sudo tee -a /boot/config.txt

echo "[INSTALL] Installation complete!"
echo "Please update the .env file at ${KIOSK_ROOT}/.env with your actual configuration values"
echo "You can check the service status with: systemctl status kiosk.service" 