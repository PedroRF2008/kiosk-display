# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based digital signage kiosk application designed to run on Raspberry Pi systems. The application displays rotating media content, weather information, and employee birthday announcements on TV screens. It includes Firebase integration for cloud-based content management and Oracle database connectivity for employee data.

## Architecture

### Core Components
- **Flask App** (`display/app.py`): Main web server handling display logic, media rotation, weather API integration, and Oracle database queries
- **Firebase Integration** (`display/firebase_config.py`): Cloud storage and configuration management via Firebase Admin SDK
- **Device Management** (`display/device_manager.py`): Handles device registration and group assignments
- **Cache Management** (`display/cache_manager.py`): Local caching system for media files and configuration
- **System Monitor** (`display/system_monitor.py`): System health monitoring and diagnostics
- **Oracle Config** (`display/oracle_config.py`): Oracle database connection configuration for employee data

### Key Features
- Cloud-based media management through Firebase
- Automatic content synchronization and caching
- Weather widget using OpenWeatherMap API
- Employee birthday display from Oracle database
- Automatic software updates via GitHub releases
- Kiosk mode with Chromium browser
- Device monitoring and health checks

## Development Commands

### Running the Application
```bash
# Navigate to display directory
cd display/

# Activate virtual environment
source /home/kiosk/kiosk/.venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Flask development server
python app.py
```

### Testing Components
```bash
# Test birthday data retrieval
curl http://localhost:5000/test/birthdays

# Test admin interface
# Navigate to http://localhost:5000/admin (password: admin123)
```

### Version Management
- Update version in `display/version.py` following semantic versioning
- Version is displayed in the UI and used for auto-update checks

## Configuration

### Environment Variables (.env file)
The application requires a `.env` file in the kiosk root directory with:
- Firebase service account credentials
- Device key for cloud configuration
- Flask secret key
- OpenWeather API configuration

### Production Deployment
- Install script: `install.sh` (downloads latest release, sets up systemd service)
- Systemd service: `display/kiosk.service`
- Startup script: `display/start_kiosk.sh` (handles updates, launches Chromium)

### Oracle Database Integration
- Requires Oracle Instant Client installation
- Connects to Oracle database for employee birthday queries
- Encoding set to UTF-8 for proper character handling

## Important Development Notes

### Media Handling
- Supports images (PNG, JPG, GIF) and videos (MP4, WebM, MOV)
- Automatic image optimization and resizing for 1920x1080 displays
- Video duration handling (-1 for "play until end")
- Local caching of cloud media files

### Firebase Structure
- Device configuration stored in Firestore
- Media files stored in Firebase Storage
- Weather configuration in `config/openWeather` document
- Device grouping for content management

### Auto-Update System
- Checks GitHub releases on startup
- Downloads and applies updates automatically
- Maintains virtual environment and dependencies
- Restarts service after successful update

### Hardware Considerations
- Designed for Raspberry Pi with Chromium browser
- GPU acceleration enabled for video playback
- Optimized cache settings for limited storage
- Boot splash customization for professional appearance

## Testing and Quality Assurance

When making changes:
1. Test Flask app locally: `python app.py`
2. Verify Oracle connectivity with test route: `/test/birthdays`
3. Check admin interface functionality at `/admin`
4. Test media upload and processing
5. Verify weather API integration
6. Validate auto-update mechanism

## Deployment Process

1. Update version in `display/version.py`
2. Test changes locally
3. Commit and tag release following semantic versioning
4. GitHub Actions automatically creates release package
5. Production systems auto-update on next startup