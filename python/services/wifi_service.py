"""
WiFi service for managing wireless connections
"""
import asyncio
import subprocess
import json
import logging
from config.settings import WIFI_FAVORITES

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def get_wifi_status():
    """Get current WiFi connection status"""
    try:
        # Get current connection info
        result = subprocess.run(
            ["iwgetid", "-r"],
            capture_output=True,
            text=True
        )

        connected_ssid = result.stdout.strip() if result.returncode == 0 else None

        # Get signal strength if connected
        signal_strength = None
        if connected_ssid:
            signal_result = subprocess.run(
                ["iwconfig", "wlan0"],
                capture_output=True,
                text=True
            )

            # Extract signal level from iwconfig output
            for line in signal_result.stdout.split("\n"):
                if "Signal level" in line:
                    parts = line.split("Signal level=")
                    if len(parts) > 1:
                        signal_parts = parts[1].split(" ")
                        signal_strength = signal_parts[0]

        return {
            "connected": connected_ssid is not None,
            "ssid": connected_ssid,
            "signal_strength": signal_strength,
            "favorites": WIFI_FAVORITES
        }
    except Exception as e:
        log.error(f"Error getting WiFi status: {e}")
        return {
            "connected": False,
            "ssid": None,
            "signal_strength": None,
            "favorites": WIFI_FAVORITES,
            "error": str(e)
        }

async def scan_networks():
    """Scan for available WiFi networks"""
    try:
        # Scan for networks
        subprocess.run(["sudo", "iwlist", "wlan0", "scan"], capture_output=True)

        # Get scan results
        result = subprocess.run(
            ["sudo", "iw", "dev", "wlan0", "scan"],
            capture_output=True,
            text=True
        )

        # Parse the output to extract network information
        networks = []
        current_network = {}

        for line in result.stdout.split("\n"):
            line = line.strip()

            if "BSS" in line and "(" in line:
                # New network found
                if current_network and "ssid" in current_network:
                    networks.append(current_network)

                current_network = {"bssid": line.split("(")[0].split("BSS ")[1].strip()}

            elif "SSID: " in line:
                current_network["ssid"] = line.split("SSID: ")[1].strip()

            elif "signal:" in line:
                current_network["signal"] = line.split("signal:")[1].strip()

        # Add the last network
        if current_network and "ssid" in current_network:
            networks.append(current_network)

        # Check which ones are favorites
        for network in networks:
            network["is_favorite"] = network.get("ssid") in [f["ssid"] for f in WIFI_FAVORITES]

        return {
            "networks": networks
        }
    except Exception as e:
        log.error(f"Error scanning WiFi networks: {e}")
        return {
            "networks": [],
            "error": str(e)
        }

async def connect_to_network(ssid, password=None):
    """Connect to a WiFi network"""
    try:
        # Check if we need a password
        needs_password = password is not None and password.strip() != ""

        # For saved networks, just use nmcli to connect
        if not needs_password:
            result = subprocess.run(
                ["sudo", "nmcli", "device", "wifi", "connect", ssid],
                capture_output=True,
                text=True
            )
        else:
            # Connect with password
            result = subprocess.run(
                ["sudo", "nmcli", "device", "wifi", "connect", ssid, "password", password],
                capture_output=True,
                text=True
            )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr
            }

        return {
            "success": True,
            "ssid": ssid
        }
    except Exception as e:
        log.error(f"Error connecting to WiFi network: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def disconnect_network():
    """Disconnect from current WiFi network"""
    try:
        result = subprocess.run(
            ["sudo", "nmcli", "device", "disconnect", "wlan0"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr
            }

        return {
            "success": True
        }
    except Exception as e:
        log.error(f"Error disconnecting from WiFi network: {e}")
        return {
            "success": False,
            "error": str(e)
        }