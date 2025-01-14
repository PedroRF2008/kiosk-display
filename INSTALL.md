# Kiosk Installation Guide

## Quick Install
```bash
wget -O - https://raw.githubusercontent.com/PedroRF2008/kiosk-display/main/install.sh | sudo bash
```

## 1. Install Required Packages
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y chromium-browser x11-xserver-utils unclutter

# Create project directory and set permissions
sudo mkdir -p /home/pedro/kiosk/static /home/pedro/kiosk/cache
sudo cp /path/to/project/.env /home/pedro/kiosk/
sudo chown -R pedro:pedro /home/pedro/kiosk

# Remove old display directory if it exists
sudo rm -rf /home/pedro/display

# Install Python packages
cd /home/pedro/kiosk/display-1.0.0
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure Auto-login
```bash
# Enable auto-login for user
sudo raspi-config
# Navigate to: System Options > Boot / Auto Login > Desktop Autologin
# Make sure to select the correct user (pedro)
```

## 3. Setup Kiosk Service
```bash
# Make startup script executable
chmod +x /home/pedro/display/start_kiosk.sh

# Copy service file to systemd
sudo cp kiosk.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable kiosk.service
sudo systemctl start kiosk.service
```

## Useful Commands
- Check service status: `sudo systemctl status kiosk.service`
- View logs: `sudo journalctl -u kiosk.service`
- Restart service: `sudo systemctl restart kiosk.service`
- Stop service: `sudo systemctl stop kiosk.service`

## Troubleshooting
1. If the screen goes blank:
   ```bash
   sudo nano /etc/lightdm/lightdm.conf
   # Add under [SeatDefaults]:
   xserver-command=X -s 0 -dpms
   ```

2. If Chromium doesn't start:
   - Check if DISPLAY is set: `echo $DISPLAY`
   - Check X server logs: `cat ~/.local/share/xorg/Xorg.0.log`
   - Check Xauthority path: `ls -l /home/pedro/.Xauthority`

3. If Flask app doesn't start:
   - Check Python virtual environment
   - Check permissions on project directory
   - Check network connectivity 