"""
Threading classes for NetBox Import Wizard
"""
import json
from typing import Dict, List
from PyQt6.QtCore import QThread, pyqtSignal


class NetBoxConnectionThread(QThread):
    """Thread for testing NetBox connection without blocking UI"""

    connection_result = pyqtSignal(bool, str, int)  # success, message, site_count

    def __init__(self, url: str, token: str, verify_ssl: bool = False):
        super().__init__()
        self.url = url
        self.token = token
        self.verify_ssl = verify_ssl

    def run(self):
        try:
            # Configure threading and SSL
            import requests
            import pynetbox

            session = requests.Session()
            if not self.verify_ssl:
                session.verify = False

            nb = pynetbox.api(self.url, token=self.token)
            nb.http_session = session

            # Test the connection by getting sites
            sites = list(nb.dcim.sites.all())
            ssl_status = "SSL verified" if self.verify_ssl else "SSL verification disabled"
            message = f"Connected ({ssl_status}) - Found {len(sites)} sites"
            self.connection_result.emit(True, message, len(sites))

        except Exception as e:
            error_msg = str(e)
            if "SSL" in error_msg or "certificate" in error_msg.lower():
                error_msg += "\n\nTip: Try unchecking 'Verify SSL Certificate' for self-signed certificates"
            self.connection_result.emit(False, f"Connection failed: {error_msg}", 0)


class TopologyLoadThread(QThread):
    """Thread for loading and processing topology files"""

    load_complete = pyqtSignal(dict)  # discovered_devices
    load_error = pyqtSignal(str)
    progress_update = pyqtSignal(str, int)  # status_message, percentage

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            self.progress_update.emit("Reading topology file...", 10)

            with open(self.file_path, 'r') as f:
                raw_data = json.load(f)

            self.progress_update.emit("Validating topology data...", 30)

            # Validate and clean the data structure
            discovered_devices = self._validate_topology_data(raw_data)

            self.progress_update.emit("Processing device relationships...", 70)

            # Add small delay to show progress (remove in production)
            self.msleep(500)

            self.progress_update.emit("Topology loading complete", 100)
            self.load_complete.emit(discovered_devices)

        except json.JSONDecodeError as e:
            self.load_error.emit(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            self.load_error.emit(f"Error loading topology file: {str(e)}")

    def _validate_topology_data(self, raw_data: Dict) -> Dict:
        """Validate and normalize topology data structure"""
        validated_devices = {}
        total_devices = len(raw_data)
        processed = 0

        for device_name, device_data in raw_data.items():
            processed += 1
            progress = 30 + int((processed / total_devices) * 40)  # 30-70% range
            self.progress_update.emit(f"Processing device {processed}/{total_devices}: {device_name}", progress)

            if not isinstance(device_name, str) or not device_name.strip():
                continue  # Skip invalid device names

            # Ensure device_data is a dictionary
            if not isinstance(device_data, dict):
                device_data = {}

            # Normalize node_details
            node_details = device_data.get('node_details', {})
            if not isinstance(node_details, dict):
                node_details = {}

            validated_node_details = {
                'ip': self._safe_get_string(node_details, 'ip'),
                'platform': self._safe_get_string(node_details, 'platform')
            }

            # Normalize peers
            peers = device_data.get('peers', {})
            if not isinstance(peers, dict):
                peers = {}

            validated_peers = {}
            for peer_name, peer_data in peers.items():
                if not isinstance(peer_name, str) or not peer_name.strip():
                    continue  # Skip invalid peer names

                if not isinstance(peer_data, dict):
                    peer_data = {}

                validated_peer = {
                    'ip': self._safe_get_string(peer_data, 'ip'),
                    'platform': self._safe_get_string(peer_data, 'platform'),
                    'connections': self._safe_get_connections(peer_data.get('connections', []))
                }

                validated_peers[peer_name] = validated_peer

            validated_devices[device_name] = {
                'node_details': validated_node_details,
                'peers': validated_peers
            }

        return validated_devices

    def _safe_get_string(self, data: Dict, key: str, default: str = '') -> str:
        """Safely extract string value from dictionary"""
        value = data.get(key, default)
        if value is None:
            return default
        return str(value).strip()

    def _safe_get_connections(self, connections_data) -> List:
        """Safely extract and validate connections data"""
        if not isinstance(connections_data, list):
            return []

        validated_connections = []
        for connection in connections_data:
            if isinstance(connection, list) and len(connection) >= 2:
                # Ensure both interface names are strings
                local_int = str(connection[0]).strip() if connection[0] is not None else ''
                remote_int = str(connection[1]).strip() if connection[1] is not None else ''

                if local_int and remote_int:  # Only add if both interfaces are valid
                    validated_connections.append([local_int, remote_int])

        return validated_connections


class NetBoxDataThread(QThread):
    """Thread for fetching NetBox data (sites, roles, device types, etc.)"""

    data_ready = pyqtSignal(dict)  # All NetBox data in one dict
    data_error = pyqtSignal(str)
    progress_update = pyqtSignal(str, int)

    def __init__(self, netbox_api):
        super().__init__()
        self.netbox_api = netbox_api

    def run(self):
        try:
            data = {}

            self.progress_update.emit("Fetching sites...", 10)
            data['sites'] = self.netbox_api.get_sites()

            self.progress_update.emit("Fetching device roles...", 30)
            data['roles'] = self.netbox_api.get_device_roles()

            self.progress_update.emit("Fetching device types...", 50)
            data['device_types'] = self.netbox_api.get_device_types()

            self.progress_update.emit("Fetching existing devices...", 70)
            data['existing_devices'] = self.netbox_api.get_existing_devices()

            self.progress_update.emit("Fetching platforms...", 90)
            data['platforms'] = self.netbox_api.get_platforms()

            self.progress_update.emit("Data fetch complete", 100)
            self.data_ready.emit(data)

        except Exception as e:
            self.data_error.emit(f"Error fetching NetBox data: {str(e)}")


class DeviceImportThread(QThread):
    """Thread for importing devices to NetBox"""

    import_progress = pyqtSignal(str, int, int)  # device_name, current, total
    import_complete = pyqtSignal(int, int)  # successful, failed
    import_error = pyqtSignal(str)
    device_created = pyqtSignal(str, bool, str)  # device_name, success, message

    def __init__(self, netbox_api, import_data: List[Dict]):
        super().__init__()
        self.netbox_api = netbox_api
        self.import_data = import_data

    def run(self):
        successful = 0
        failed = 0
        total = len(self.import_data)

        for i, device_data in enumerate(self.import_data):
            if self.isInterruptionRequested():
                break

            device_name = device_data.get('name', 'Unknown')
            self.import_progress.emit(device_name, i + 1, total)

            try:
                # Build device creation payload
                device_payload = {
                    'name': device_data['name'],
                    'site': device_data['site_id'],
                    'device_role': device_data['role_id'],
                    'device_type': device_data['type_id'],
                    'status': 'active'
                }

                # Add platform if provided
                if device_data.get('platform_id'):
                    device_payload['platform'] = device_data['platform_id']

                # Create device in NetBox
                result = self.netbox_api.create_device(device_payload)

                successful += 1
                self.device_created.emit(device_name, True, f"Created successfully (ID: {result.id})")

            except Exception as e:
                failed += 1
                self.device_created.emit(device_name, False, f"Failed: {str(e)}")

            # Small delay to prevent overwhelming the API
            self.msleep(100)

        self.import_complete.emit(successful, failed)