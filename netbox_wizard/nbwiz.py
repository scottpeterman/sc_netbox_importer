import json
import sys
import urllib3
from typing import Dict, List, Optional, Tuple
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QComboBox, QLineEdit, QTextEdit, QTabWidget, QGroupBox,
    QProgressBar, QCheckBox, QFileDialog, QMessageBox,
    QSplitter, QTreeWidget, QTreeWidgetItem, QFormLayout,
    QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor
import pynetbox

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
                # Create device in NetBox
                result = self.netbox_api.create_device({
                    'name': device_data['name'],
                    'site': device_data['site_id'],
                    'device_role': device_data['role_id'],
                    'device_type': device_data['type_id'],
                    'status': 'active'
                })

                successful += 1
                self.device_created.emit(device_name, True, f"Created successfully (ID: {result.id})")

            except Exception as e:
                failed += 1
                self.device_created.emit(device_name, False, f"Failed: {str(e)}")

            # Small delay to prevent overwhelming the API
            self.msleep(100)

        self.import_complete.emit(successful, failed)


class NetBoxAPI:
    """Wrapper for NetBox API operations"""

    def __init__(self, url: str, token: str, verify_ssl: bool = False):
        # Configure threading and SSL
        import requests
        session = requests.Session()
        if not verify_ssl:
            session.verify = False

        self.nb = pynetbox.api(url, token=token)
        self.nb.http_session = session
        self._cache = {}

    def get_manufacturers(self) -> List[Dict]:
        if 'manufacturers' not in self._cache:
            try:
                self._cache['manufacturers'] = list(self.nb.dcim.manufacturers.all())
            except Exception as e:
                print(f"Error fetching manufacturers: {e}")
                self._cache['manufacturers'] = []
        return self._cache['manufacturers']

    def get_device_types(self, manufacturer_id: Optional[int] = None) -> List[Dict]:
        cache_key = f'device_types_{manufacturer_id}'
        if cache_key not in self._cache:
            try:
                if manufacturer_id:
                    self._cache[cache_key] = list(self.nb.dcim.device_types.filter(manufacturer_id=manufacturer_id))
                else:
                    self._cache[cache_key] = list(self.nb.dcim.device_types.all())
            except Exception as e:
                print(f"Error fetching device types: {e}")
                self._cache[cache_key] = []
        return self._cache[cache_key]

    def get_device_roles(self) -> List[Dict]:
        if 'device_roles' not in self._cache:
            try:
                self._cache['device_roles'] = list(self.nb.dcim.device_roles.all())
            except Exception as e:
                print(f"Error fetching device roles: {e}")
                self._cache['device_roles'] = []
        return self._cache['device_roles']

    def get_platforms(self) -> List[Dict]:
        if 'platforms' not in self._cache:
            try:
                self._cache['platforms'] = list(self.nb.dcim.platforms.all())
            except Exception as e:
                print(f"Error fetching platforms: {e}")
                self._cache['platforms'] = []
        return self._cache['platforms']

    def get_sites(self) -> List[Dict]:
        if 'sites' not in self._cache:
            try:
                self._cache['sites'] = list(self.nb.dcim.sites.all())
            except Exception as e:
                print(f"Error fetching sites: {e}")
                self._cache['sites'] = []
        return self._cache['sites']

    def get_existing_devices(self) -> List[Dict]:
        if 'existing_devices' not in self._cache:
            try:
                self._cache['existing_devices'] = list(self.nb.dcim.devices.all())
            except Exception as e:
                print(f"Error fetching existing devices: {e}")
                self._cache['existing_devices'] = []
        return self._cache['existing_devices']

    def create_device(self, device_data: Dict) -> Dict:
        """Create a new device in NetBox"""
        return self.nb.dcim.devices.create(device_data)

    def create_cable(self, cable_data: Dict) -> Dict:
        """Create a cable connection in NetBox"""
        return self.nb.dcim.cables.create(cable_data)


class DeviceDiscoveryModel:
    """Model for managing discovered devices and their NetBox mapping"""

    def __init__(self):
        self.discovered_devices = {}
        self.device_mappings = {}
        self.existing_devices = {}

    def set_discovered_devices(self, devices: Dict):
        """Set discovered devices from thread result"""
        self.discovered_devices = devices

    def extract_unique_platforms(self) -> List[str]:
        """Extract unique platform strings from discovered devices"""
        platforms = set()

        for device_name, device_data in self.discovered_devices.items():
            # Get platform from node_details
            node_details = device_data.get('node_details', {})
            if isinstance(node_details, dict):
                platform = node_details.get('platform', '')
                if platform and platform.strip():
                    platforms.add(platform.strip())

            # Also check peers for platforms
            peers = device_data.get('peers', {})
            if isinstance(peers, dict):
                for peer_name, peer_data in peers.items():
                    if isinstance(peer_data, dict):
                        peer_platform = peer_data.get('platform', '')
                        if peer_platform and peer_platform.strip():
                            platforms.add(peer_platform.strip())

        return sorted(list(platforms))

    def find_potential_matches(self, netbox_devices: List[Dict]) -> Dict:
        """Find potential matches between discovered and existing NetBox devices"""
        matches = {}

        for device_name in self.discovered_devices.keys():
            device_ip = ''
            node_details = self.discovered_devices[device_name].get('node_details', {})
            if isinstance(node_details, dict):
                device_ip = node_details.get('ip', '').strip()

            potential_matches = []
            for nb_device in netbox_devices:
                try:
                    # Match by name (case-insensitive)
                    if hasattr(nb_device, 'name') and nb_device.name:
                        if nb_device.name.lower() == device_name.lower():
                            potential_matches.append(('name', nb_device))

                    # Match by primary IP
                    if device_ip and hasattr(nb_device, 'primary_ip4') and nb_device.primary_ip4:
                        nb_ip = str(nb_device.primary_ip4).split('/')[0]
                        if nb_ip == device_ip:
                            potential_matches.append(('ip', nb_device))
                except (AttributeError, ValueError) as e:
                    # Skip devices that don't have expected attributes
                    continue

            if potential_matches:
                matches[device_name] = potential_matches

        return matches


class DeviceTableWidget(QTableWidget):
    """Custom table widget for displaying discovered devices"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()

    def setup_table(self):
        headers = [
            'Device Name', 'IP Address', 'Platform',
            'NetBox Status', 'Action', 'Site', 'Role', 'Device Type'
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

    def populate_devices_with_netbox_data(self, devices: Dict, potential_matches: Dict, netbox_data: Dict):
        """Populate table with discovered devices and NetBox data"""
        device_list = []

        # Flatten the nested structure
        for device_name, device_data in devices.items():
            node_details = device_data.get('node_details', {})
            if not isinstance(node_details, dict):
                node_details = {}

            device_list.append({
                'name': device_name,
                'ip': node_details.get('ip', '').strip(),
                'platform': node_details.get('platform', '').strip(),
                'matches': potential_matches.get(device_name, [])
            })

            # Add peer devices that aren't already in the main list
            peers = device_data.get('peers', {})
            if isinstance(peers, dict):
                for peer_name, peer_data in peers.items():
                    if peer_name not in devices:
                        if not isinstance(peer_data, dict):
                            peer_data = {}

                        device_list.append({
                            'name': peer_name,
                            'ip': peer_data.get('ip', '').strip(),
                            'platform': peer_data.get('platform', '').strip(),
                            'matches': potential_matches.get(peer_name, [])
                        })

        # Remove duplicates
        seen_names = set()
        unique_devices = []
        for device in device_list:
            if device['name'] not in seen_names and device['name'].strip():
                unique_devices.append(device)
                seen_names.add(device['name'])

        self.setRowCount(len(unique_devices))

        # Get NetBox data
        sites = netbox_data.get('sites', [])
        roles = netbox_data.get('roles', [])
        device_types = netbox_data.get('device_types', [])

        for row, device in enumerate(unique_devices):
            # Device Name
            self.setItem(row, 0, QTableWidgetItem(device['name']))

            # IP Address
            self.setItem(row, 1, QTableWidgetItem(device['ip']))

            # Platform
            self.setItem(row, 2, QTableWidgetItem(device['platform']))

            # NetBox Status
            if device['matches']:
                status_text = f"Found {len(device['matches'])} match(es)"
                status_item = QTableWidgetItem(status_text)
                status_item.setBackground(QColor(255, 255, 0))  # Yellow
                status_item.setForeground(QColor(0,0,0))

            else:
                status_item = QTableWidgetItem("New device")
                status_item.setBackground(QColor(144, 238, 144))  # Light green
                status_item.setForeground(QColor(0,0,0))
            self.setItem(row, 3, status_item)

            # Action ComboBox
            action_combo = QComboBox()
            if device['matches']:
                action_combo.addItems(['Skip', 'Update existing', 'Create new'])
            else:
                action_combo.addItems(['Create new', 'Skip'])
            self.setCellWidget(row, 4, action_combo)

            # Site ComboBox
            site_combo = QComboBox()
            site_combo.addItem("-- Select Site --", None)
            for site in sites:
                site_combo.addItem(site.name, site.id)
            self.setCellWidget(row, 5, site_combo)

            # Role ComboBox
            role_combo = QComboBox()
            role_combo.addItem("-- Select Role --", None)
            for role in roles:
                role_combo.addItem(role.name, role.id)
            self.setCellWidget(row, 6, role_combo)

            # Device Type ComboBox
            type_combo = QComboBox()
            type_combo.addItem("-- Select Device Type --", None)
            for device_type in device_types:
                manufacturer_name = getattr(device_type.manufacturer, 'name',
                                            'Unknown') if device_type.manufacturer else 'Unknown'
                type_combo.addItem(f"{manufacturer_name} - {device_type.model}", device_type.id)
            self.setCellWidget(row, 7, type_combo)

        print(
            f"Populated {len(unique_devices)} devices with {len(sites)} sites, {len(roles)} roles, {len(device_types)} device types")


class NetBoxImportWizard(QMainWindow):
    """Main wizard window for NetBox device import"""

    def __init__(self):
        super().__init__()
        self.netbox_api = None
        self.discovery_model = DeviceDiscoveryModel()
        self.netbox_data = {}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("SecureCartography - NetBox Import Wizard")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create tab widget for wizard steps
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Step 1: Connection and File Loading
        self.setup_connection_tab()

        # Step 2: Device Discovery and Mapping
        self.setup_discovery_tab()

        # Step 3: Configuration and Import
        self.setup_import_tab()

        # Status bar
        self.statusBar().showMessage("Ready")

    def setup_connection_tab(self):
        """Setup the connection and file loading tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # NetBox Connection Group
        connection_group = QGroupBox("NetBox Connection")
        connection_layout = QFormLayout(connection_group)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://netbox.example.com")
        connection_layout.addRow("NetBox URL:", self.url_input)

        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        connection_layout.addRow("API Token:", self.token_input)

        self.verify_ssl_checkbox = QCheckBox("Verify SSL Certificate")
        self.verify_ssl_checkbox.setChecked(False)
        self.verify_ssl_checkbox.setToolTip("Uncheck for self-signed certificates (common in lab environments)")
        connection_layout.addRow("SSL Verification:", self.verify_ssl_checkbox)

        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_netbox_connection)
        connection_layout.addRow(self.test_connection_btn)

        # Add progress bar for connection testing
        self.connection_progress = QProgressBar()
        self.connection_progress.setVisible(False)
        connection_layout.addRow("Progress:", self.connection_progress)

        layout.addWidget(connection_group)

        # File Loading Group
        file_group = QGroupBox("Topology File")
        file_layout = QVBoxLayout(file_group)

        file_selection_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select SecureCartography JSON file...")

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_topology_file)

        file_selection_layout.addWidget(self.file_path_input)
        file_selection_layout.addWidget(self.browse_btn)
        file_layout.addLayout(file_selection_layout)

        self.load_file_btn = QPushButton("Load Topology")
        self.load_file_btn.clicked.connect(self.load_topology_file)
        self.load_file_btn.setEnabled(False)
        file_layout.addWidget(self.load_file_btn)

        # Add progress bar for file loading
        self.file_progress = QProgressBar()
        self.file_progress.setVisible(False)
        file_layout.addWidget(self.file_progress)

        layout.addWidget(file_group)

        # Progress and Status
        self.connection_status = QLabel("Not connected")
        layout.addWidget(self.connection_status)

        layout.addStretch()

        self.tab_widget.addTab(tab, "1. Connection & File")

    def setup_discovery_tab(self):
        """Setup the device discovery and mapping tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Progress bar for discovery operations
        self.discovery_progress = QProgressBar()
        self.discovery_progress.setVisible(False)
        layout.addWidget(self.discovery_progress)

        # Device table
        self.device_table = DeviceTableWidget()
        layout.addWidget(self.device_table)

        # Mapping controls
        controls_layout = QHBoxLayout()

        self.refresh_matches_btn = QPushButton("Refresh Matches")
        self.refresh_matches_btn.clicked.connect(self.refresh_device_matches)
        controls_layout.addWidget(self.refresh_matches_btn)

        self.populate_dropdowns_btn = QPushButton("Refresh NetBox Data")
        self.populate_dropdowns_btn.clicked.connect(self.refresh_netbox_data)
        controls_layout.addWidget(self.populate_dropdowns_btn)

        self.auto_map_btn = QPushButton("Auto-Map Platforms")
        self.auto_map_btn.clicked.connect(self.auto_map_platforms)
        controls_layout.addWidget(self.auto_map_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        self.tab_widget.addTab(tab, "2. Device Discovery")

    def setup_import_tab(self):
        """Setup the import configuration and execution tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Import summary
        summary_group = QGroupBox("Import Summary")
        summary_layout = QVBoxLayout(summary_group)

        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(150)
        summary_layout.addWidget(self.summary_text)

        layout.addWidget(summary_group)

        # Import controls
        controls_layout = QHBoxLayout()

        self.validate_btn = QPushButton("Validate Configuration")
        self.validate_btn.clicked.connect(self.validate_import)
        controls_layout.addWidget(self.validate_btn)

        self.import_btn = QPushButton("Start Import")
        self.import_btn.clicked.connect(self.start_import)
        self.import_btn.setEnabled(False)
        controls_layout.addWidget(self.import_btn)

        self.cancel_import_btn = QPushButton("Cancel Import")
        self.cancel_import_btn.clicked.connect(self.cancel_import)
        self.cancel_import_btn.setEnabled(False)
        controls_layout.addWidget(self.cancel_import_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Progress bar
        self.import_progress = QProgressBar()
        layout.addWidget(self.import_progress)

        # Import log
        log_group = QGroupBox("Import Log")
        log_layout = QVBoxLayout(log_group)

        self.import_log = QTextEdit()
        log_layout.addWidget(self.import_log)

        layout.addWidget(log_group)

        self.tab_widget.addTab(tab, "3. Import")

    def test_netbox_connection(self):
        """Test connection to NetBox using threading"""
        url = self.url_input.text().strip()
        token = self.token_input.text().strip()
        verify_ssl = self.verify_ssl_checkbox.isChecked()

        if not url or not token:
            QMessageBox.warning(self, "Warning", "Please enter both URL and token")
            return

        # Show progress and disable button
        self.connection_progress.setVisible(True)
        self.connection_progress.setRange(0, 0)  # Indeterminate progress
        self.test_connection_btn.setEnabled(False)
        self.connection_status.setText("Testing connection...")
        self.connection_status.setStyleSheet("color: blue")

        # Start connection test thread
        self.connection_thread = NetBoxConnectionThread(url, token, verify_ssl)
        self.connection_thread.connection_result.connect(self.on_connection_result)
        self.connection_thread.start()

    def on_connection_result(self, success: bool, message: str, site_count: int):
        """Handle connection test result"""
        self.connection_progress.setVisible(False)
        self.test_connection_btn.setEnabled(True)

        if success:
            self.connection_status.setText(f"✓ {message}")
            self.connection_status.setStyleSheet("color: green")
            self.load_file_btn.setEnabled(True)

            # Create NetBox API instance for later use
            url = self.url_input.text().strip()
            token = self.token_input.text().strip()
            verify_ssl = self.verify_ssl_checkbox.isChecked()
            self.netbox_api = NetBoxAPI(url, token, verify_ssl)
        else:
            self.connection_status.setText(f"✗ {message}")
            self.connection_status.setStyleSheet("color: red")
            self.netbox_api = None

    def browse_topology_file(self):
        """Browse for topology JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select SecureCartography JSON file", "", "JSON files (*.json)"
        )
        if file_path:
            self.file_path_input.setText(file_path)

    def load_topology_file(self):
        """Load the topology file using threading"""
        file_path = self.file_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a file")
            return

        # Show progress
        self.file_progress.setVisible(True)
        self.file_progress.setRange(0, 100)
        self.load_file_btn.setEnabled(False)

        # Start topology loading thread
        self.topology_thread = TopologyLoadThread(file_path)
        self.topology_thread.load_complete.connect(self.on_topology_loaded)
        self.topology_thread.load_error.connect(self.on_topology_error)
        self.topology_thread.progress_update.connect(self.on_topology_progress)
        self.topology_thread.start()

    def on_topology_progress(self, message: str, percentage: int):
        """Handle topology loading progress updates"""
        self.file_progress.setValue(percentage)
        self.statusBar().showMessage(message)

    def on_topology_loaded(self, discovered_devices: Dict):
        """Handle successful topology loading"""
        self.file_progress.setVisible(False)
        self.load_file_btn.setEnabled(True)

        # Store discovered devices in model
        self.discovery_model.set_discovered_devices(discovered_devices)

        # Start loading NetBox data in background
        self.start_netbox_data_fetch()

        # Switch to discovery tab
        self.tab_widget.setCurrentIndex(1)
        self.statusBar().showMessage(f"Loaded {len(discovered_devices)} devices")

    def on_topology_error(self, error_message: str):
        """Handle topology loading error"""
        self.file_progress.setVisible(False)
        self.load_file_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to load topology file: {error_message}")
        self.statusBar().showMessage("Error loading topology file")

    def start_netbox_data_fetch(self):
        """Start fetching NetBox data in background"""
        if not self.netbox_api:
            return

        # Show progress
        self.discovery_progress.setVisible(True)
        self.discovery_progress.setRange(0, 100)

        # Start NetBox data fetch thread
        self.netbox_data_thread = NetBoxDataThread(self.netbox_api)
        self.netbox_data_thread.data_ready.connect(self.on_netbox_data_ready)
        self.netbox_data_thread.data_error.connect(self.on_netbox_data_error)
        self.netbox_data_thread.progress_update.connect(self.on_netbox_data_progress)
        self.netbox_data_thread.start()

    def on_netbox_data_progress(self, message: str, percentage: int):
        """Handle NetBox data fetch progress"""
        self.discovery_progress.setValue(percentage)
        self.statusBar().showMessage(message)

    def on_netbox_data_ready(self, netbox_data: Dict):
        """Handle successful NetBox data fetch"""
        self.discovery_progress.setVisible(False)
        self.netbox_data = netbox_data

        # Find potential matches
        potential_matches = self.discovery_model.find_potential_matches(
            netbox_data.get('existing_devices', [])
        )

        # Populate the device table
        self.device_table.populate_devices_with_netbox_data(
            self.discovery_model.discovered_devices,
            potential_matches,
            netbox_data
        )

        self.statusBar().showMessage("NetBox data loaded successfully")

    def on_netbox_data_error(self, error_message: str):
        """Handle NetBox data fetch error"""
        self.discovery_progress.setVisible(False)
        QMessageBox.warning(self, "Warning", f"Failed to fetch NetBox data: {error_message}")
        self.statusBar().showMessage("Error fetching NetBox data")

    def refresh_netbox_data(self):
        """Manually refresh NetBox data"""
        if not self.netbox_api:
            QMessageBox.warning(self, "Warning", "Not connected to NetBox")
            return

        # Clear cache to force refresh
        self.netbox_api._cache = {}
        self.start_netbox_data_fetch()

    def refresh_device_matches(self):
        """Refresh device matches against NetBox"""
        if not self.netbox_data:
            self.start_netbox_data_fetch()
        else:
            self.on_netbox_data_ready(self.netbox_data)

    def auto_map_platforms(self):
        """Automatically map platforms to device types"""
        # This would implement intelligent mapping logic
        QMessageBox.information(self, "Info", "Auto-mapping feature would be implemented here")

    def validate_import(self):
        """Validate the import configuration"""
        # Check that all required fields are filled
        validation_errors = []
        devices_to_import = []

        for row in range(self.device_table.rowCount()):
            device_name = self.device_table.item(row, 0).text()
            action_combo = self.device_table.cellWidget(row, 4)

            if action_combo.currentText() == "Create new":
                site_combo = self.device_table.cellWidget(row, 5)
                role_combo = self.device_table.cellWidget(row, 6)
                type_combo = self.device_table.cellWidget(row, 7)

                if not site_combo.currentData():
                    validation_errors.append(f"{device_name}: Site not selected")
                if not role_combo.currentData():
                    validation_errors.append(f"{device_name}: Role not selected")
                if not type_combo.currentData():
                    validation_errors.append(f"{device_name}: Device type not selected")

                if site_combo.currentData() and role_combo.currentData() and type_combo.currentData():
                    devices_to_import.append({
                        'name': device_name,
                        'site_id': site_combo.currentData(),
                        'role_id': role_combo.currentData(),
                        'type_id': type_combo.currentData()
                    })

        if validation_errors:
            error_text = "\n".join(validation_errors)
            QMessageBox.warning(self, "Validation Errors", f"Please fix the following issues:\n\n{error_text}")
            return False

        self.import_btn.setEnabled(True)
        self.devices_to_import = devices_to_import
        summary = f"Ready to import {len(devices_to_import)} devices to NetBox."
        self.summary_text.setText(summary)
        return True

    def start_import(self):
        """Start the import process using threading"""
        if not self.validate_import():
            return

        if not hasattr(self, 'devices_to_import') or not self.devices_to_import:
            QMessageBox.warning(self, "Warning", "No devices to import")
            return

        # Setup progress bar
        self.import_progress.setMaximum(len(self.devices_to_import))
        self.import_progress.setValue(0)

        # Enable cancel button, disable import button
        self.import_btn.setEnabled(False)
        self.cancel_import_btn.setEnabled(True)

        # Clear import log
        self.import_log.clear()
        self.import_log.append("Starting device import...\n")

        # Start import thread
        self.import_thread = DeviceImportThread(self.netbox_api, self.devices_to_import)
        self.import_thread.import_progress.connect(self.on_import_progress)
        self.import_thread.import_complete.connect(self.on_import_complete)
        self.import_thread.device_created.connect(self.on_device_created)
        self.import_thread.start()

    def on_import_progress(self, device_name: str, current: int, total: int):
        """Handle import progress updates"""
        self.import_progress.setValue(current)
        self.statusBar().showMessage(f"Importing device {current}/{total}: {device_name}")

    def on_device_created(self, device_name: str, success: bool, message: str):
        """Handle individual device creation result"""
        status = "✓" if success else "✗"
        color = "green" if success else "red"
        log_entry = f'<span style="color: {color};">{status} {device_name}: {message}</span><br>'
        self.import_log.append(log_entry)

    def on_import_complete(self, successful: int, failed: int):
        """Handle import completion"""
        self.import_btn.setEnabled(True)
        self.cancel_import_btn.setEnabled(False)

        total = successful + failed
        summary = f"\nImport complete: {successful}/{total} devices created successfully"
        if failed > 0:
            summary += f", {failed} failed"

        self.import_log.append(f'<br><b>{summary}</b>')
        self.statusBar().showMessage(summary)

        # Show completion message
        QMessageBox.information(self, "Import Complete", summary)

    def cancel_import(self):
        """Cancel the running import"""
        if hasattr(self, 'import_thread') and self.import_thread.isRunning():
            self.import_thread.requestInterruption()
            self.import_log.append("<br><b>Import cancelled by user</b>")
            self.import_btn.setEnabled(True)
            self.cancel_import_btn.setEnabled(False)
            self.statusBar().showMessage("Import cancelled")


def main():
    app = QApplication(sys.argv)
    wizard = NetBoxImportWizard()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()