"""
NetBox Import Wizard - Main Application
Reduced main file using modularized components
"""
import sys
import urllib3
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QLabel, QTabWidget, QGroupBox,
    QProgressBar, QCheckBox, QFileDialog, QMessageBox,
    QLineEdit, QTextEdit, QComboBox, QFormLayout, QDialog
)
from PyQt6.QtCore import Qt

# Import our modularized components
from config_manager import (
    ConfigManager, NetBoxConnection, AppPreferences,
    MasterPasswordDialog, MasterPasswordSetupDialog
)
from threading_classes import (
    NetBoxConnectionThread, TopologyLoadThread,
    NetBoxDataThread, DeviceImportThread
)
from netbox_api import NetBoxAPI, DeviceDiscoveryModel
from ui_components import DeviceTableWidget, get_table_selection_count

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NetBoxImportWizard(QMainWindow):
    """Main NetBox Import Wizard Application"""

    def __init__(self):
        super().__init__()

        # Initialize basic components
        self.netbox_api = None
        self.discovery_model = DeviceDiscoveryModel()
        self.netbox_data = {}
        self.devices_to_import = []

        # Initialize configuration
        self.config = ConfigManager()

        # Setup UI
        self.setup_ui()

        # Initialize configuration system
        self.initialize_config()

    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("SecureCartography - NetBox Import Wizard")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create tab widget for wizard steps
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Setup all tabs
        self.setup_connection_tab()
        self.setup_discovery_tab()
        self.setup_import_tab()

        # Status bar
        self.statusBar().showMessage("Ready")

    def setup_connection_tab(self):
        """Setup the connection and file loading tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # NetBox Connection Group
        self.connection_group = QGroupBox("NetBox Connection")
        connection_layout = QFormLayout(self.connection_group)

        # Connection dropdown
        self.connection_combo = QComboBox()
        self.connection_combo.addItem("-- New Connection --", None)
        self.connection_combo.currentTextChanged.connect(self.on_connection_selected)
        connection_layout.addRow("Saved Connections:", self.connection_combo)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://netbox.example.com")
        connection_layout.addRow("NetBox URL:", self.url_input)

        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        connection_layout.addRow("API Token:", self.token_input)

        self.verify_ssl_checkbox = QCheckBox("Verify SSL Certificate")
        self.verify_ssl_checkbox.setChecked(False)
        self.verify_ssl_checkbox.setToolTip("Uncheck for self-signed certificates")
        connection_layout.addRow("SSL Verification:", self.verify_ssl_checkbox)

        # Save connection controls
        self.save_connection_checkbox = QCheckBox("Save this connection")
        self.save_connection_checkbox.setChecked(True)
        connection_layout.addRow("", self.save_connection_checkbox)

        self.connection_name_input = QLineEdit()
        self.connection_name_input.setPlaceholderText("Connection name...")
        connection_layout.addRow("Connection Name:", self.connection_name_input)

        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_netbox_connection)
        connection_layout.addRow(self.test_connection_btn)

        self.connection_progress = QProgressBar()
        self.connection_progress.setVisible(False)
        connection_layout.addRow("Progress:", self.connection_progress)

        layout.addWidget(self.connection_group)

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

        self.file_progress = QProgressBar()
        self.file_progress.setVisible(False)
        file_layout.addWidget(self.file_progress)

        layout.addWidget(file_group)

        # Status
        self.connection_status = QLabel("Not connected")
        layout.addWidget(self.connection_status)

        layout.addStretch()
        self.tab_widget.addTab(tab, "1. Connection & File")

    def setup_discovery_tab(self):
        """Setup the device discovery and mapping tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Progress bars
        self.discovery_progress = QProgressBar()
        self.discovery_progress.setVisible(False)
        layout.addWidget(self.discovery_progress)

        self.table_progress = QProgressBar()
        self.table_progress.setVisible(False)
        self.table_progress_label = QLabel("Populating device table...")
        self.table_progress_label.setVisible(False)
        layout.addWidget(self.table_progress_label)
        layout.addWidget(self.table_progress)

        # Bulk controls
        bulk_group = QGroupBox("Bulk Selection & Configuration")
        bulk_layout = QVBoxLayout(bulk_group)

        # Selection controls
        selection_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(lambda: self.device_table.select_all_devices(True))
        selection_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("Select None")
        self.select_none_btn.clicked.connect(lambda: self.device_table.select_all_devices(False))
        selection_layout.addWidget(self.select_none_btn)

        selection_layout.addWidget(QLabel("|"))
        selection_layout.addWidget(QLabel("By Platform:"))

        self.discovered_platform_combo = QComboBox()
        self.discovered_platform_combo.addItem("-- Select Platform --")
        selection_layout.addWidget(self.discovered_platform_combo)

        self.select_platform_btn = QPushButton("Select")
        self.select_platform_btn.clicked.connect(self.select_by_discovered_platform)
        selection_layout.addWidget(self.select_platform_btn)

        self.deselect_platform_btn = QPushButton("Deselect")
        self.deselect_platform_btn.clicked.connect(self.deselect_by_discovered_platform)
        selection_layout.addWidget(self.deselect_platform_btn)

        selection_layout.addStretch()
        bulk_layout.addLayout(selection_layout)

        # Default configuration
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("Apply to Selected:"))

        self.default_site_combo = QComboBox()
        self.default_site_combo.addItem("-- Site --", None)
        config_layout.addWidget(self.default_site_combo)

        self.default_role_combo = QComboBox()
        self.default_role_combo.addItem("-- Role --", None)
        config_layout.addWidget(self.default_role_combo)

        self.default_platform_combo = QComboBox()
        self.default_platform_combo.addItem("-- Platform --", None)
        config_layout.addWidget(self.default_platform_combo)

        self.apply_defaults_btn = QPushButton("Apply Defaults")
        self.apply_defaults_btn.clicked.connect(self.apply_defaults_to_selected)
        config_layout.addWidget(self.apply_defaults_btn)

        config_layout.addStretch()
        bulk_layout.addLayout(config_layout)

        layout.addWidget(bulk_group)

        # Device table
        self.device_table = DeviceTableWidget()
        self.device_table.population_progress.connect(self.on_table_population_progress)
        self.device_table.population_complete.connect(self.on_table_population_complete)
        layout.addWidget(self.device_table)

        # Status
        self.selection_status = QLabel("0 devices selected for import")
        layout.addWidget(self.selection_status)

        # Controls
        controls_layout = QHBoxLayout()
        self.refresh_matches_btn = QPushButton("Refresh Matches")
        self.refresh_matches_btn.clicked.connect(self.refresh_device_matches)
        controls_layout.addWidget(self.refresh_matches_btn)

        self.populate_dropdowns_btn = QPushButton("Refresh NetBox Data")
        self.populate_dropdowns_btn.clicked.connect(self.refresh_netbox_data)
        controls_layout.addWidget(self.populate_dropdowns_btn)

        self.auto_map_platforms_btn = QPushButton("Auto-Map Platforms")
        self.auto_map_platforms_btn.clicked.connect(self.auto_map_all_platforms)
        controls_layout.addWidget(self.auto_map_platforms_btn)

        self.update_count_btn = QPushButton("Update Count")
        self.update_count_btn.clicked.connect(self.update_selection_count)
        controls_layout.addWidget(self.update_count_btn)

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

    # Configuration Management Methods
    def initialize_config(self) -> bool:
        """Initialize configuration system"""
        try:
            if not self.config.is_initialized():
                dialog = MasterPasswordSetupDialog(self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    password = dialog.get_password()
                    if not self.config.setup_master_password(password):
                        QMessageBox.critical(self, "Error", "Failed to initialize credential storage")
                        return False
                else:
                    return False
            else:
                dialog = MasterPasswordDialog(self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    password = dialog.get_password()
                    if not self.config.unlock(password):
                        QMessageBox.warning(self, "Warning",
                                          "Incorrect password. Continuing without saved credentials.")
                        return False
                else:
                    return False

            self.populate_connection_dropdown()
            preferences = self.config.get_preferences()
            self.resize(preferences.window_width, preferences.window_height)

            if preferences.last_file_path:
                self.file_path_input.setText(preferences.last_file_path)

            return True
        except Exception as e:
            QMessageBox.warning(self, "Warning",
                              f"Configuration error: {str(e)}\nContinuing without saved credentials.")
            return False

    def populate_connection_dropdown(self):
        """Populate the connection dropdown with saved connections"""
        self.connection_combo.clear()
        self.connection_combo.addItem("-- New Connection --", None)

        if self.config.is_credentials_unlocked():
            for conn in self.config.list_connections():
                self.connection_combo.addItem(conn.name, conn)

    def on_connection_selected(self, connection_name: str):
        """Handle connection selection from dropdown"""
        if connection_name == "-- New Connection --":
            self.clear_connection_fields()
            return

        selected_conn = None
        for i in range(self.connection_combo.count()):
            if self.connection_combo.itemText(i) == connection_name:
                selected_conn = self.connection_combo.itemData(i)
                break

        if selected_conn:
            self.url_input.setText(selected_conn.url)
            self.verify_ssl_checkbox.setChecked(selected_conn.verify_ssl)
            self.connection_name_input.setText(selected_conn.name)

            token = self.config.get_connection_token(selected_conn.name)
            if token:
                self.token_input.setText(token)

    def clear_connection_fields(self):
        """Clear connection input fields"""
        self.url_input.clear()
        self.token_input.clear()
        self.verify_ssl_checkbox.setChecked(False)
        self.connection_name_input.clear()

    def save_current_connection(self):
        """Save the current connection using config manager"""
        if not self.save_connection_checkbox.isChecked():
            return

        name = self.connection_name_input.text().strip()
        url = self.url_input.text().strip()
        token = self.token_input.text().strip()
        verify_ssl = self.verify_ssl_checkbox.isChecked()

        if url and token:
            success = self.config.save_connection_if_enabled(
                name, url, token, verify_ssl, True
            )
            if success:
                actual_name = name if name else f"NetBox-{len(self.config.list_connections())}"
                self.config.update_connection_last_used(actual_name)
                self.populate_connection_dropdown()
                self.statusBar().showMessage(f"Connection '{actual_name}' saved successfully")

    # Connection and File Loading Methods
    def test_netbox_connection(self):
        """Test connection to NetBox using threading"""
        url = self.url_input.text().strip()
        token = self.token_input.text().strip()
        verify_ssl = self.verify_ssl_checkbox.isChecked()

        if not url or not token:
            QMessageBox.warning(self, "Warning", "Please enter both URL and token")
            return

        self.connection_progress.setVisible(True)
        self.connection_progress.setRange(0, 0)
        self.test_connection_btn.setEnabled(False)
        self.connection_status.setText("Testing connection...")
        self.connection_status.setStyleSheet("color: blue")

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

            url = self.url_input.text().strip()
            token = self.token_input.text().strip()
            verify_ssl = self.verify_ssl_checkbox.isChecked()
            self.netbox_api = NetBoxAPI(url, token, verify_ssl)

            self.save_current_connection()
        else:
            self.connection_status.setText(f"✗ {message}")
            self.connection_status.setStyleSheet("color: red")
            self.netbox_api = None

    def browse_topology_file(self):
        """Browse for topology JSON file"""
        preferences = self.config.get_preferences()
        start_dir = str(preferences.last_file_path) if preferences.last_file_path else ""

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select SecureCartography JSON file", start_dir, "JSON files (*.json)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
            self.config.update_preferences(last_file_path=file_path)

    def load_topology_file(self):
        """Load the topology file using threading"""
        file_path = self.file_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a file")
            return

        self.file_progress.setVisible(True)
        self.file_progress.setRange(0, 100)
        self.load_file_btn.setEnabled(False)

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

        self.discovery_model.set_discovered_devices(discovered_devices)
        self.start_netbox_data_fetch()
        self.tab_widget.setCurrentIndex(1)
        self.statusBar().showMessage(f"Loaded {len(discovered_devices)} devices")

    def on_topology_error(self, error_message: str):
        """Handle topology loading error"""
        self.file_progress.setVisible(False)
        self.load_file_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to load topology file: {error_message}")
        self.statusBar().showMessage("Error loading topology file")

    # NetBox Data Management Methods
    def start_netbox_data_fetch(self):
        """Start fetching NetBox data in background"""
        if not self.netbox_api:
            return

        self.discovery_progress.setVisible(True)
        self.discovery_progress.setRange(0, 100)

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

        self.table_progress.setVisible(True)
        self.table_progress_label.setVisible(True)
        self.table_progress.setValue(0)

        potential_matches = self.discovery_model.find_potential_matches(
            netbox_data.get('existing_devices', [])
        )

        self.device_table.populate_devices_with_netbox_data(
            self.discovery_model.discovered_devices,
            potential_matches,
            netbox_data
        )

    def on_netbox_data_error(self, error_message: str):
        """Handle NetBox data fetch error"""
        self.discovery_progress.setVisible(False)
        QMessageBox.warning(self, "Warning", f"Failed to fetch NetBox data: {error_message}")
        self.statusBar().showMessage("Error fetching NetBox data")

    def on_table_population_progress(self, current: int, total: int):
        """Handle table population progress"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.table_progress.setValue(percentage)
            self.table_progress_label.setText(f"Populating device table... {current}/{total}")
            self.statusBar().showMessage(f"Populating device table: {current}/{total} devices")

    def on_table_population_complete(self):
        """Handle table population completion"""
        self.table_progress.setVisible(False)
        self.table_progress_label.setVisible(False)
        self.populate_bulk_controls()
        self.update_selection_count()
        self.statusBar().showMessage("NetBox data loaded successfully")

    # Device Management Methods
    def populate_bulk_controls(self):
        """Populate the bulk control dropdowns"""
        if not self.netbox_data:
            return

        # Populate discovered platform filter
        discovered_platforms = set()
        for row in range(self.device_table.rowCount()):
            platform_item = self.device_table.item(row, 3)
            if platform_item and platform_item.text().strip():
                discovered_platforms.add(platform_item.text().strip())

        self.discovered_platform_combo.clear()
        self.discovered_platform_combo.addItem("-- Select Platform --")
        for platform in sorted(discovered_platforms):
            self.discovered_platform_combo.addItem(platform)

        # Populate default combos
        sites = self.netbox_data.get('sites', [])
        self.default_site_combo.clear()
        self.default_site_combo.addItem("-- Site --", None)
        for site in sites:
            self.default_site_combo.addItem(site.name, site.id)

        roles = self.netbox_data.get('roles', [])
        self.default_role_combo.clear()
        self.default_role_combo.addItem("-- Role --", None)
        for role in roles:
            self.default_role_combo.addItem(role.name, role.id)

        platforms = self.netbox_data.get('platforms', [])
        self.default_platform_combo.clear()
        self.default_platform_combo.addItem("-- Platform --", None)
        for platform in platforms:
            self.default_platform_combo.addItem(platform.name, platform.id)

    def select_by_discovered_platform(self):
        """Select all devices of the chosen discovered platform"""
        platform = self.discovered_platform_combo.currentText()
        if platform != "-- Select Platform --":
            self.device_table.select_devices_by_discovered_platform(platform, True)
            self.update_selection_count()

    def deselect_by_discovered_platform(self):
        """Deselect all devices of the chosen discovered platform"""
        platform = self.discovered_platform_combo.currentText()
        if platform != "-- Select Platform --":
            self.device_table.select_devices_by_discovered_platform(platform, False)
            self.update_selection_count()

    def apply_defaults_to_selected(self):
        """Apply default site/role/platform to selected devices"""
        site_id = self.default_site_combo.currentData()
        role_id = self.default_role_combo.currentData()
        platform_id = self.default_platform_combo.currentData()

        if site_id or role_id or platform_id:
            self.device_table.apply_defaults_to_selected(site_id, role_id, platform_id)
            applied = []
            if site_id: applied.append("site")
            if role_id: applied.append("role")
            if platform_id: applied.append("platform")
            QMessageBox.information(self, "Applied", f"Default {', '.join(applied)} applied to selected devices")

    def auto_map_all_platforms(self):
        """Auto-map platforms for all devices in the table"""
        platforms = self.netbox_data.get('platforms', [])
        mapped_count = 0

        for row in range(self.device_table.rowCount()):
            discovered_item = self.device_table.item(row, 3)
            if not discovered_item:
                continue

            discovered_platform = discovered_item.text()
            if not discovered_platform:
                continue

            platform_combo = self.device_table.cellWidget(row, 4)
            if not platform_combo:
                continue

            if platform_combo.currentData() is not None:
                continue

            matched_platform = self.device_table._find_matching_platform(discovered_platform, platforms)
            if matched_platform:
                for i in range(platform_combo.count()):
                    if platform_combo.itemData(i) == matched_platform.id:
                        platform_combo.setCurrentIndex(i)
                        mapped_count += 1
                        break

        if mapped_count > 0:
            QMessageBox.information(self, "Auto-Mapping Complete",
                                  f"Successfully mapped {mapped_count} platforms")
        else:
            QMessageBox.information(self, "Auto-Mapping Complete",
                                  "No additional platform mappings found")

    def update_selection_count(self):
        """Update the selection count display"""
        count = get_table_selection_count(self.device_table)
        self.selection_status.setText(f"{count} devices selected for import")

    def refresh_netbox_data(self):
        """Manually refresh NetBox data"""
        if not self.netbox_api:
            QMessageBox.warning(self, "Warning", "Not connected to NetBox")
            return

        self.netbox_api._cache = {}
        self.start_netbox_data_fetch()

    def refresh_device_matches(self):
        """Refresh device matches against NetBox"""
        if not self.netbox_data:
            self.start_netbox_data_fetch()
        else:
            self.on_netbox_data_ready(self.netbox_data)

    # Import Methods
    def validate_import(self):
        """Validate import configuration"""
        devices_to_import = self.device_table.get_selected_devices_for_import()
        validation_errors = []

        for device in devices_to_import:
            device_name = device['name']

            if not device['site_id']:
                validation_errors.append(f"{device_name}: Site not selected")
            if not device['role_id']:
                validation_errors.append(f"{device_name}: Role not selected")
            if not device['type_id']:
                validation_errors.append(f"{device_name}: Device type not selected")

        if validation_errors:
            error_text = "\n".join(validation_errors)
            QMessageBox.warning(self, "Validation Errors", f"Please fix the following issues:\n\n{error_text}")
            return False

        if not devices_to_import:
            QMessageBox.warning(self, "No Devices Selected", "Please select at least one device to import")
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

        if not self.devices_to_import:
            QMessageBox.warning(self, "Warning", "No devices to import")
            return

        self.import_progress.setMaximum(len(self.devices_to_import))
        self.import_progress.setValue(0)

        self.import_btn.setEnabled(False)
        self.cancel_import_btn.setEnabled(True)

        self.import_log.clear()
        self.import_log.append("Starting device import...\n")

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

        QMessageBox.information(self, "Import Complete", summary)

    def cancel_import(self):
        """Cancel the running import"""
        if hasattr(self, 'import_thread') and self.import_thread.isRunning():
            self.import_thread.requestInterruption()
            self.import_log.append("<br><b>Import cancelled by user</b>")
            self.import_btn.setEnabled(True)
            self.cancel_import_btn.setEnabled(False)
            self.statusBar().showMessage("Import cancelled")

    def closeEvent(self, event):
        """Save preferences when closing"""
        if self.config.is_credentials_unlocked():
            self.config.update_preferences(
                window_width=self.width(),
                window_height=self.height()
            )
        event.accept()


def main():
    app = QApplication(sys.argv)
    wizard = NetBoxImportWizard()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()