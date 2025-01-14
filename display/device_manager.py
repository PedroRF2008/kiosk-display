from typing import Optional, Dict, Tuple
from firebase_admin import firestore
import time
from version import VERSION
import requests
import threading
import json
import websocket
from time import sleep
import logging

# Configure logging at the top of the file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class DeviceManager:
    def __init__(self, db: firestore.Client, device_key: str, device_ip: str):
        """Initialize the device manager"""
        self.db = db
        self.device_key = device_key
        self.device_ip = device_ip
        self.device_doc = None
        self.group_doc = None
        self.last_heartbeat = time.time()
        self.diagnostic_data = {}
        # Store listener callbacks to prevent garbage collection
        self._listeners = []
        # Add sync lock
        self._sync_lock = threading.Lock()
        self._heartbeat_interval = 60  # Configurable heartbeat interval
        self._last_sync = 0  # Track last sync time
        self._min_sync_interval = 5  # Minimum seconds between syncs
        print(f"DeviceManager initialized with key: {device_key}")
        
    def find_device(self) -> Optional[Dict]:
        """Find device document by device key"""
        try:
            # Get device document directly by key
            device_ref = self.db.collection('devices').document(self.device_key)
            doc = device_ref.get()
            
            if doc.exists:
                self.device_doc = {'id': doc.id, **doc.to_dict()}
                # Update IP address and initial status
                device_ref.update({
                    'ip': self.device_ip,
                    'lastIpUpdate': firestore.SERVER_TIMESTAMP,
                    'status': 'online',
                    'lastSeen': firestore.SERVER_TIMESTAMP
                })
                return self.device_doc
                
            print(f"Device not found with key: {self.device_key}")
            return None
            
        except Exception as e:
            print(f"Error finding device: {str(e)}")
            return None
            
    def get_group_info(self) -> Optional[Dict]:
        """Get group information for the device"""
        if not self.device_doc or not self.device_doc.get('groupId'):
            return None
            
        try:
            group_ref = self.db.collection('groups').document(self.device_doc['groupId'])
            doc = group_ref.get()
            
            if doc.exists:
                self.group_doc = {'id': doc.id, **doc.to_dict()}
                return self.group_doc
                
            return None
        except Exception as e:
            print(f"Error getting group info: {str(e)}")
            return None
            
    def update_device_status(self, status: str = 'online') -> bool:
        """Update device status in Firestore"""
        if not self.device_doc:
            return False
            
        try:
            device_ref = self.db.collection('devices').document(self.device_doc['id'])
            device_ref.update({
                'status': status,
                'lastSeen': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error updating device status: {str(e)}")
            return False
            
    def start_status_listener(self) -> None:
        """Start listening for device document changes"""
        if not self.device_doc:
            return None
            
        def on_snapshot(doc_snapshot, changes, read_time):
            """Handle device document updates"""
            for doc in doc_snapshot:
                data = doc.to_dict()
                # Update local device doc
                self.device_doc = {'id': doc.id, **data}
                
                # Handle group changes
                if self.group_doc and self.group_doc['id'] != data.get('groupId'):
                    # Group has changed, trigger reload
                    print("Group changed, reloading...")
                    time.sleep(1)  # Small delay to ensure Firestore consistency
                    self.get_group_info()
        
        # Listen to device document changes
        device_ref = self.db.collection('devices').document(self.device_doc['id'])
        return device_ref.on_snapshot(on_snapshot)
        
    def start_group_listener(self) -> None:
        """Start listening for group document changes"""
        if not self.group_doc:
            return None
            
        def on_snapshot(doc_snapshot, changes, read_time):
            """Handle group document updates"""
            for doc in doc_snapshot:
                data = doc.to_dict()
                # Update local group doc
                self.group_doc = {'id': doc.id, **data}
                
        # Listen to group document changes
        group_ref = self.db.collection('groups').document(self.group_doc['id'])
        return group_ref.on_snapshot(on_snapshot)
        
    def initialize(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Initialize device and group data"""
        print("Initializing device...")
        device = self.find_device()
        if not device:
            print("Device not found!")
            return None, None
            
        print(f"Device found: {device.get('name', 'unnamed')}")
        group = self.get_group_info()
        
        # Start listeners
        print("Starting listeners...")
        status_listener = self.start_status_listener()
        command_listener = self.start_command_listener()
        if group:
            group_listener = self.start_group_listener()
            self._listeners.extend([status_listener, command_listener, group_listener])
        else:
            self._listeners.extend([status_listener, command_listener])
        
        # Start heartbeat thread
        self._start_heartbeat_thread()
        
        return device, group

    def _start_heartbeat_thread(self):
        """Start background thread for heartbeat"""
        def heartbeat_loop():
            while True:
                try:
                    self.send_heartbeat()
                except Exception as e:
                    print(f"Heartbeat error: {str(e)}")
                time.sleep(self._heartbeat_interval)

        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        print("Heartbeat thread started")

    def start_command_listener(self) -> None:
        """Listen for commands from Firebase"""
        if not self.device_doc:
            print("Cannot start command listener - device not initialized")
            return None

        print(f"Starting command listener for device: {self.device_key}")
        
        def on_snapshot(doc_snapshot, changes, read_time):
            for change in changes:
                if change.type.name == 'MODIFIED':
                    data = change.document.to_dict()
                    current_time = time.time()
                    
                    # Check for sync flag with rate limiting
                    if data.get('needsSync', False):
                        if current_time - self._last_sync >= self._min_sync_interval:
                            print("Sync flag detected")
                            if self._sync_lock.acquire(blocking=False):
                                try:
                                    # Update flag first to prevent multiple triggers
                                    self.db.collection('devices').document(self.device_key).update({
                                        'needsSync': False
                                    })
                                    self.sync_content()
                                    self._last_sync = current_time
                                    # Update lastSync timestamp
                                    self.db.collection('devices').document(self.device_key).update({
                                        'lastSync': firestore.SERVER_TIMESTAMP
                                    })
                                finally:
                                    self._sync_lock.release()
                            else:
                                print("Sync already in progress, skipping...")
                        else:
                            print("Sync requested too soon, skipping...")
                    
                    # Handle reboot command
                    if data.get('needsReboot', False):
                        print("Reboot flag detected")
                        try:
                            # Reset reboot flag first
                            self.db.collection('devices').document(self.device_key).update({
                                'needsReboot': False
                            })
                            # Then initiate reboot
                            self.reboot_device()
                        except Exception as e:
                            print(f"Error handling reboot command: {str(e)}")

        # Listen to device document for commands
        device_ref = self.db.collection('devices').document(self.device_key)
        listener = device_ref.on_snapshot(on_snapshot)
        self._listeners.append(listener)
        print("Command listener started successfully")
        return listener

    def send_heartbeat(self):
        """Send device heartbeat and diagnostic data"""
        current_time = time.time()
        
        try:
            try:
                from system_monitor import (get_cpu_temperature, get_memory_usage,
                                          get_cpu_usage, get_disk_usage,
                                          get_uptime, get_network_stats, get_wifi_info)
            except ImportError as e:
                print(f"Error importing system_monitor functions: {str(e)}")
                print("Make sure psutil is installed: pip install psutil")
                return
            
            self.diagnostic_data = {
                'timestamp': firestore.SERVER_TIMESTAMP,
                'uptime': get_uptime(),
                'memory': get_memory_usage(),
                'cpu': get_cpu_usage(),
                'disk': get_disk_usage(),
                'temperature': get_cpu_temperature(),
                'network': get_network_stats(),
                'wifi': get_wifi_info(),
                'version': VERSION,
            }
            
            print("Sending heartbeat with diagnostics...")
            self.db.collection('devices').document(self.device_key).update({
                'lastHeartbeat': firestore.SERVER_TIMESTAMP,
                'status': 'online',
                'diagnostics': self.diagnostic_data
            })
            
            self.last_heartbeat = current_time
            print("Heartbeat sent successfully")
            
        except Exception as e:
            print(f"Error sending heartbeat: {str(e)}")

    def refresh_browser(self):
        """Refresh the Chromium browser using remote debugging protocol"""
        try:
            logger.info("Getting Chrome debugger info...")
            # First get the WebSocket URL from Chrome's debugging endpoint
            response = requests.get('http://localhost:9222/json')
            if not response.ok:
                logger.error(f"Failed to get debugger info: {response.status_code}")
                return False
            
            pages = response.json()
            logger.debug(f"Got pages: {pages}")
            
            # Find the kiosk page
            kiosk_page = None
            for page in pages:
                if 'webSocketDebuggerUrl' in page and 'localhost:5000' in page.get('url', ''):
                    kiosk_page = page
                    break
                
            if not kiosk_page:
                logger.error("Could not find kiosk page in Chrome debugger")
                return False
            
            logger.info(f"Found kiosk page: {kiosk_page['title']}")
            ws_url = kiosk_page['webSocketDebuggerUrl']
            
            # Connect to the specific page's WebSocket URL
            logger.info(f"Connecting to WebSocket: {ws_url}")
            ws = websocket.create_connection(ws_url, timeout=5)
            
            # Send reload command
            reload_msg = {
                "id": 1,
                "method": "Page.reload",
                "params": {"ignoreCache": True}
            }
            logger.info("Sending reload command")
            ws.send(json.dumps(reload_msg))
            
            # Wait for confirmation
            result = ws.recv()
            logger.info(f"Got reload response: {result}")
            
            ws.close()
            logger.info("Browser refresh completed successfully")
            return True
            
        except websocket.WebSocketTimeoutException:
            logger.error("Timeout connecting to Chrome debugger")
            return False
        except websocket.WebSocketConnectionClosedException:
            logger.error("WebSocket connection was closed unexpectedly")
            return False
        except Exception as e:
            logger.error(f"Error refreshing browser: {str(e)}", exc_info=True)
            return False

    def sync_content(self):
        """Sync content from Firebase"""
        print("Starting content sync...")
        try:
            # Update status to syncing
            self.update_device_status('syncing')
            
            # Get latest group info
            group = self.get_group_info()
            if not group:
                print("No group assigned to device")
                self.update_device_status('online')  # Reset status if no group
                return
            
            # Trigger media sync through cache manager
            if group.get('media'):
                from cache_manager import CacheManager
                cache_manager = CacheManager()
                cache_manager.set_cached_group(group)
                cache_manager.sync_media(group['media'])
                print("Content sync completed")
                self.update_device_status('online')  # Reset status after sync
                
                # Refresh browser after successful sync
                print("Triggering browser refresh...")
                retry_count = 5  # Increased retries
                while retry_count > 0:
                    print(f"Refresh attempt {6-retry_count}/5...")
                    if self.refresh_browser():
                        print("Browser refreshed successfully")
                        break
                    print(f"Refresh attempt failed, retrying in 2 seconds... ({retry_count} attempts left)")
                    retry_count -= 1
                    sleep(2)  # Increased delay between attempts
                
                if retry_count == 0:
                    print("WARNING: All refresh attempts failed!")
                
            else:
                print("No media content in group")
                self.update_device_status('online')  # Reset status if no media
                
        except Exception as e:
            self.update_device_status('error')  # Set error status on failure
            raise Exception(f"Content sync failed: {str(e)}")

    def reboot_device(self):
        """Reboot the device"""
        print("Initiating device reboot...")
        try:
            # Update status before reboot
            self.update_device_status('rebooting')
            
            # Schedule reboot
            import subprocess
            subprocess.Popen(['sudo', 'reboot'])
        except Exception as e:
            self.update_device_status('error')  # Set error status on failure
            raise Exception(f"Reboot failed: {str(e)}")