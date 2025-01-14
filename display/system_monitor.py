import psutil
import subprocess
import os
import time
import re

def get_cpu_temperature():
    """Get CPU temperature on Raspberry Pi"""
    try:
        temp = subprocess.check_output(['vcgencmd', 'measure_temp']).decode()
        return float(temp.replace('temp=', '').replace('\'C', ''))
    except:
        return None

def get_memory_usage():
    """Get memory usage statistics"""
    mem = psutil.virtual_memory()
    return {
        'total': mem.total,
        'available': mem.available,
        'percent': mem.percent,
        'used': mem.used,
        'free': mem.free
    }

def get_cpu_usage():
    """Get CPU usage percentage"""
    return psutil.cpu_percent(interval=1)

def get_disk_usage():
    """Get disk usage statistics"""
    disk = psutil.disk_usage('/')
    return {
        'total': disk.total,
        'used': disk.used,
        'free': disk.free,
        'percent': disk.percent
    }

def get_uptime():
    """Get system uptime"""
    return int(time.time() - psutil.boot_time())

def get_network_stats():
    """Get network interface statistics"""
    net = psutil.net_io_counters()
    return {
        'bytes_sent': net.bytes_sent,
        'bytes_recv': net.bytes_recv,
        'packets_sent': net.packets_sent,
        'packets_recv': net.packets_recv
    }

def get_wifi_info():
    """Get current WiFi SSID and signal strength"""
    try:
        # Use iwconfig to get wireless interface info
        output = subprocess.check_output(['iwgetid']).decode()
        # Extract SSID using regex
        ssid_match = re.search('ESSID:"(.*?)"', output)
        ssid = ssid_match.group(1) if ssid_match else "Not connected"
        
        # Get signal strength if connected
        if ssid != "Not connected":
            signal_output = subprocess.check_output(['iwconfig']).decode()
            # Extract signal level
            signal_match = re.search('Signal level=(.*? dBm)', signal_output)
            signal_strength = signal_match.group(1) if signal_match else "Unknown"
        else:
            signal_strength = "No signal"

        return {
            'ssid': ssid,
            'signal_strength': signal_strength
        }
    except Exception as e:
        print(f"Error getting WiFi info: {str(e)}")
        return {
            'ssid': "Error",
            'signal_strength': "Error"
        }