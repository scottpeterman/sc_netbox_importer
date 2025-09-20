"""
UI Components for NetBox Import Wizard
Contains the custom table widget and UI helper functions
"""
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor


class DeviceTableWidget(QTableWidget):
    """Custom table widget with checkbox selection and platform dropdown"""

    population_progress = pyqtSignal(int, int)
    population_complete = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()

        # For chunked loading
        self.population_timer = QTimer()
        self.population_timer.timeout.connect(self._populate_chunk)
        self.devices_to_populate = []
        self.netbox_data_cache = {}
        self.current_chunk_index = 0
        self.chunk_size = 50

    def setup_table(self):
        headers = [
            'Import', 'Device Name', 'IP Address', 'Discovered Platform',
            'NetBox Platform', 'NetBox Status', 'Site', 'Role', 'Device Type'
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Adjust column widths
        self.setColumnWidth(0, 60)  # Import checkbox
        self.setColumnWidth(1, 150)  # Device Name
        self.setColumnWidth(2, 120)  # IP Address
        self.setColumnWidth(3, 120)  # Discovered Platform
        self.setColumnWidth(4, 120)  # NetBox Platform
        self.setColumnWidth(5, 120)  # NetBox Status

    def populate_devices_with_netbox_data(self, devices: Dict, potential_matches: Dict, netbox_data: Dict):
        """Populate table with discovered devices using chunked loading"""
        self.setRowCount(0)

        device_list = self._prepare_device_list(devices, potential_matches)

        self.netbox_data_cache = netbox_data
        self.devices_to_populate = device_list
        self.current_chunk_index = 0

        self.setRowCount(len(device_list))

        if device_list:
            self.population_timer.start(10)

    def _prepare_device_list(self, devices: Dict, potential_matches: Dict):
        """Prepare the device list for population"""
        device_list = []

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

        return unique_devices

    def _populate_chunk(self):
        """Populate a chunk of devices"""
        if self.current_chunk_index >= len(self.devices_to_populate):
            self.population_timer.stop()
            self.population_complete.emit()
            print(f"Populated {len(self.devices_to_populate)} devices")
            return

        sites = self.netbox_data_cache.get('sites', [])
        roles = self.netbox_data_cache.get('roles', [])
        device_types = self.netbox_data_cache.get('device_types', [])
        platforms = self.netbox_data_cache.get('platforms', [])

        end_index = min(self.current_chunk_index + self.chunk_size, len(self.devices_to_populate))

        for i in range(self.current_chunk_index, end_index):
            device = self.devices_to_populate[i]
            self._populate_device_row(i, device, sites, roles, device_types, platforms)

        self.population_progress.emit(end_index, len(self.devices_to_populate))
        self.current_chunk_index = end_index

    def _populate_device_row(self, row: int, device: Dict, sites: List, roles: List, device_types: List,
                             platforms: List):
        """Populate a single device row with checkbox and platform dropdown"""

        # Import Checkbox
        import_checkbox = QCheckBox()
        import_checkbox.setChecked(False)
        if self._should_auto_select(device):
            import_checkbox.setChecked(True)
        self.setCellWidget(row, 0, import_checkbox)

        # Device Name
        self.setItem(row, 1, QTableWidgetItem(device['name']))

        # IP Address
        self.setItem(row, 2, QTableWidgetItem(device['ip']))

        # Discovered Platform (read-only)
        discovered_platform = device['platform']
        platform_item = QTableWidgetItem(discovered_platform)
        platform_item.setFlags(platform_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        platform_item.setBackground(QColor(0, 0, 0))  # Light gray background
        self.setItem(row, 3, platform_item)

        # NetBox Platform Dropdown
        platform_combo = QComboBox()
        platform_combo.addItem("-- Select Platform --", None)

        for platform in platforms:
            platform_combo.addItem(platform.name, platform.id)

        # Try to auto-match platform
        auto_matched_platform = self._find_matching_platform(discovered_platform, platforms)
        if auto_matched_platform:
            for i in range(platform_combo.count()):
                if platform_combo.itemData(i) == auto_matched_platform.id:
                    platform_combo.setCurrentIndex(i)
                    break

        self.setCellWidget(row, 4, platform_combo)

        # NetBox Status
        if device['matches']:
            status_text = f"Found {len(device['matches'])} match(es)"
            status_item = QTableWidgetItem(status_text)
            status_item.setBackground(QColor(255, 255, 0))  # Yellow
            status_item.setForeground(QColor(0, 0, 0))
        else:
            status_item = QTableWidgetItem("New device")
            status_item.setBackground(QColor(144, 238, 144))  # Light green
            status_item.setForeground(QColor(0, 0, 0))
        self.setItem(row, 5, status_item)

        # Site ComboBox
        site_combo = QComboBox()
        site_combo.addItem("-- Select Site --", None)
        for site in sites:
            site_combo.addItem(site.name, site.id)
        self.setCellWidget(row, 6, site_combo)

        # Role ComboBox
        role_combo = QComboBox()
        role_combo.addItem("-- Select Role --", None)
        for role in roles:
            role_combo.addItem(role.name, role.id)
        self.setCellWidget(row, 7, role_combo)

        # Device Type ComboBox
        type_combo = QComboBox()
        type_combo.addItem("-- Select Device Type --", None)
        for device_type in device_types:
            manufacturer_name = getattr(device_type.manufacturer, 'name',
                                        'Unknown') if device_type.manufacturer else 'Unknown'
            type_combo.addItem(f"{manufacturer_name} - {device_type.model}", device_type.id)
        self.setCellWidget(row, 8, type_combo)

    def _find_matching_platform(self, discovered_platform: str, netbox_platforms: List) -> Optional[object]:
        """Try to automatically match discovered platform to NetBox platform"""
        if not discovered_platform:
            return None

        discovered_lower = discovered_platform.lower().strip()

        # Direct name matches
        for platform in netbox_platforms:
            if platform.name.lower() == discovered_lower:
                return platform

        # Common mappings for network device platforms
        platform_mappings = {
            'cisco_ios': ['ios', 'cisco-ios', 'cisco_ios'],
            'cisco_nxos': ['nxos', 'cisco-nxos', 'cisco_nxos', 'nexus'],
            'cisco_iosxe': ['iosxe', 'cisco-iosxe', 'cisco_iosxe'],
            'arista_eos': ['eos', 'arista-eos', 'arista_eos', 'arista'],
            'juniper_junos': ['junos', 'juniper-junos', 'juniper_junos', 'juniper'],
            'panos': ['palo-alto', 'paloalto', 'pan-os'],
            'fortios': ['fortinet', 'fortigate'],
            'linux': ['ubuntu', 'centos', 'rhel', 'debian'],
            'windows': ['win', 'microsoft']
        }

        # Try to find matches using mappings
        for platform in netbox_platforms:
            platform_name_lower = platform.name.lower()

            # Check if discovered platform matches any known aliases
            for netbox_name, aliases in platform_mappings.items():
                if platform_name_lower == netbox_name:
                    if discovered_lower in aliases or any(alias in discovered_lower for alias in aliases):
                        return platform

            # Partial string matching as fallback
            if discovered_lower in platform_name_lower or platform_name_lower in discovered_lower:
                return platform

        return None

    def _should_auto_select(self, device: Dict) -> bool:
        """Determine if device should be auto-selected"""
        has_ip = device.get('ip') and device['ip'].strip()
        has_platform = device.get('platform') and device['platform'].strip()

        if device.get('matches'):
            return False

        return has_ip and has_platform

    def get_selected_devices_for_import(self):
        """Get list of devices selected for import with their configuration"""
        devices_to_import = []

        for row in range(self.rowCount()):
            import_checkbox = self.cellWidget(row, 0)
            if import_checkbox and import_checkbox.isChecked():
                device_name = self.item(row, 1).text()
                platform_combo = self.cellWidget(row, 4)
                site_combo = self.cellWidget(row, 6)
                role_combo = self.cellWidget(row, 7)
                type_combo = self.cellWidget(row, 8)

                devices_to_import.append({
                    'name': device_name,
                    'platform_id': platform_combo.currentData() if platform_combo else None,
                    'site_id': site_combo.currentData() if site_combo else None,
                    'role_id': role_combo.currentData() if role_combo else None,
                    'type_id': type_combo.currentData() if type_combo else None
                })

        return devices_to_import

    def select_all_devices(self, checked: bool = True):
        """Select or deselect all devices"""
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(checked)

    def select_devices_by_discovered_platform(self, platform: str, checked: bool = True):
        """Select devices by their discovered platform"""
        for row in range(self.rowCount()):
            platform_item = self.item(row, 3)  # Discovered Platform column
            if platform_item and platform_item.text() == platform:
                checkbox = self.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(checked)

    def apply_defaults_to_selected(self, site_id=None, role_id=None, platform_id=None):
        """Apply default site/role/platform to selected devices"""
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():

                if site_id:
                    site_combo = self.cellWidget(row, 6)
                    if site_combo:
                        for i in range(site_combo.count()):
                            if site_combo.itemData(i) == site_id:
                                site_combo.setCurrentIndex(i)
                                break

                if role_id:
                    role_combo = self.cellWidget(row, 7)
                    if role_combo:
                        for i in range(role_combo.count()):
                            if role_combo.itemData(i) == role_id:
                                role_combo.setCurrentIndex(i)
                                break

                if platform_id:
                    platform_combo = self.cellWidget(row, 4)
                    if platform_combo:
                        for i in range(platform_combo.count()):
                            if platform_combo.itemData(i) == platform_id:
                                platform_combo.setCurrentIndex(i)
                                break


def create_combo_with_items(items: List, default_text: str = "-- Select --", id_attr: str = "id",
                            name_attr: str = "name") -> QComboBox:
    """Helper function to create combo boxes with NetBox data"""
    combo = QComboBox()
    combo.addItem(default_text, None)

    for item in items:
        item_id = getattr(item, id_attr, None)
        item_name = getattr(item, name_attr, str(item))
        combo.addItem(item_name, item_id)

    return combo


def populate_combo_from_netbox_data(combo: QComboBox, items: List, default_text: str = "-- Select --",
                                    id_attr: str = "id", name_attr: str = "name"):
    """Helper function to populate existing combo boxes with NetBox data"""
    combo.clear()
    combo.addItem(default_text, None)

    for item in items:
        item_id = getattr(item, id_attr, None)
        item_name = getattr(item, name_attr, str(item))
        combo.addItem(item_name, item_id)


def set_combo_by_data(combo: QComboBox, data_value):
    """Helper function to set combo box selection by data value"""
    for i in range(combo.count()):
        if combo.itemData(i) == data_value:
            combo.setCurrentIndex(i)
            return True
    return False


def get_table_selection_count(table: QTableWidget, checkbox_column: int = 0) -> int:
    """Helper function to count selected checkboxes in a table"""
    count = 0
    for row in range(table.rowCount()):
        checkbox = table.cellWidget(row, checkbox_column)
        if checkbox and checkbox.isChecked():
            count += 1
    return count