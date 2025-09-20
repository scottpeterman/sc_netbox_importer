
def setup_connection_tab(self):
    """Setup the connection and file loading tab with config integration"""
    tab = QWidget()
    layout = QVBoxLayout(tab)

    # NetBox Connection Group
    self.connection_group = QGroupBox("NetBox Connection")
    connection_layout = QFormLayout(self.connection_group)

    # Connection dropdown (will be populated after config init)
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
    self.verify_ssl_checkbox.setToolTip("Uncheck for self-signed certificates (common in lab environments)")
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

    # Add progress bar for connection testing
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
    """Setup the device discovery and mapping tab with platform support"""
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

    # Bulk selection controls
    bulk_group = QGroupBox("Bulk Selection & Configuration")
    bulk_layout = QVBoxLayout(bulk_group)

    # Row 1: Selection controls
    selection_layout = QHBoxLayout()

    self.select_all_btn = QPushButton("Select All")
    self.select_all_btn.clicked.connect(lambda: self.device_table.select_all_devices(True))
    selection_layout.addWidget(self.select_all_btn)

    self.select_none_btn = QPushButton("Select None")
    self.select_none_btn.clicked.connect(lambda: self.device_table.select_all_devices(False))
    selection_layout.addWidget(self.select_none_btn)

    # Platform-based selection
    selection_layout.addWidget(QLabel("|"))
    selection_layout.addWidget(QLabel("By Discovered Platform:"))

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

    # Row 2: Default configuration
    config_layout = QHBoxLayout()
    config_layout.addWidget(QLabel("Apply to Selected Devices:"))

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

    # Status/count display
    self.selection_status = QLabel("0 devices selected for import")
    layout.addWidget(self.selection_status)

    # Individual controls
    controls_layout = QHBoxLayout()

    self.refresh_matches_btn = QPushButton("Refresh Matches")
    self.refresh_matches_btn.clicked.connect(self.refresh_device_matches)
    controls_layout.addWidget(self.refresh_matches_btn)

    self.populate_dropdowns_btn = QPushButton("Refresh NetBox Data")
    self.populate_dropdowns_btn.clicked.connect(self.refresh_netbox_data)
    controls_layout.addWidget(self.populate_dropdowns_btn)

    self.auto_map_platforms_btn = QPushButton("Auto-Map All Platforms")
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


def populate_connection_dropdown(self):
    """Populate the connection dropdown with saved connections"""
    if not hasattr(self, 'connection_combo'):
        return

    self.connection_combo.clear()
    self.connection_combo.addItem("-- New Connection --", None)

    if self.config.credentials.is_unlocked():
        for conn in self.config.list_connections():
            self.connection_combo.addItem(conn.name, conn)


def on_connection_selected(self, connection_name: str):
    """Handle connection selection from dropdown"""
    if connection_name == "-- New Connection --":
        self.clear_connection_fields()
        return

    # Find the selected connection
    selected_conn = None
    for i in range(self.connection_combo.count()):
        if self.connection_combo.itemText(i) == connection_name:
            selected_conn = self.connection_combo.itemData(i)
            break

    if selected_conn:
        self.url_input.setText(selected_conn.url)
        self.verify_ssl_checkbox.setChecked(selected_conn.verify_ssl)
        if hasattr(self, 'connection_name_input'):
            self.connection_name_input.setText(selected_conn.name)

        # Load token
        token = self.config.get_connection_token(selected_conn.name)
        if token:
            self.token_input.setText(token)


def clear_connection_fields(self):
    """Clear connection input fields"""
    if hasattr(self, 'url_input'):
        self.url_input.clear()
    if hasattr(self, 'token_input'):
        self.token_input.clear()
    if hasattr(self, 'verify_ssl_checkbox'):
        self.verify_ssl_checkbox.setChecked(False)
    if hasattr(self, 'connection_name_input'):
        self.connection_name_input.clear()


def save_current_connection(self):
    """Save the current connection if checkbox is checked"""
    if not self.config.credentials.is_unlocked():
        return

    if not hasattr(self, 'save_connection_checkbox') or not self.save_connection_checkbox.isChecked():
        return

    name = ""
    if hasattr(self, 'connection_name_input'):
        name = self.connection_name_input.text().strip()

    if not name:
        name = f"NetBox-{len(self.config.list_connections()) + 1}"

    url = self.url_input.text().strip()
    token = self.token_input.text().strip()
    verify_ssl = self.verify_ssl_checkbox.isChecked()

    if url and token:
        success = self.config.add_connection(name, url, token, verify_ssl)
        if success:
            self.config.update_connection_last_used(name)
            self.populate_connection_dropdown()
            self.statusBar().showMessage(f"Connection '{name}' saved successfully")


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

        # Save successful connection
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
        # Save the file path
        self.config.update_preferences(last_file_path=file_path)


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

    # Show table population progress
    self.table_progress.setVisible(True)
    self.table_progress_label.setVisible(True)
    self.table_progress.setValue(0)

    # Find potential matches
    potential_matches = self.discovery_model.find_potential_matches(
        netbox_data.get('existing_devices', [])
    )

    # Start chunked table population
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


def populate_bulk_controls(self):
    """Populate the bulk control dropdowns"""
    if not self.netbox_data:
        return

    # Populate discovered platform filter
    discovered_platforms = set()
    for row in range(self.device_table.rowCount()):
        platform_item = self.device_table.item(row, 3)  # Discovered Platform column
        if platform_item and platform_item.text().strip():
            discovered_platforms.add(platform_item.text().strip())

    self.discovered_platform_combo.clear()
    self.discovered_platform_combo.addItem("-- Select Platform --")
    for platform in sorted(discovered_platforms):
        self.discovered_platform_combo.addItem(platform)

    # Populate default site combo
    sites = self.netbox_data.get('sites', [])
    self.default_site_combo.clear()
    self.default_site_combo.addItem("-- Site --", None)
    for site in sites:
        self.default_site_combo.addItem(site.name, site.id)

    # Populate default role combo
    roles = self.netbox_data.get('roles', [])
    self.default_role_combo.clear()
    self.default_role_combo.addItem("-- Role --", None)
    for role in roles:
        self.default_role_combo.addItem(role.name, role.id)

    # Populate default platform combo
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
        # Get discovered platform
        discovered_item = self.device_table.item(row, 3)
        if not discovered_item:
            continue

        discovered_platform = discovered_item.text()
        if not discovered_platform:
            continue

        # Get NetBox platform combo
        platform_combo = self.device_table.cellWidget(row, 4)
        if not platform_combo:
            continue

        # Skip if already has a selection
        if platform_combo.currentData() is not None:
            continue

        # Try to find a match
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
    selected_devices = self.device_table.get_selected_devices_for_import()
    count = len(selected_devices)
    self.selection_status.setText(f"{count} devices selected for import")


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


def validate_import(self):
    """Updated validate method to include platform validation"""
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


def closeEvent(self, event):
    """Save preferences when closing"""
    if self.config.credentials.is_unlocked():
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
    QHeaderView, QDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor
import pynetbox
from config_manager import ConfigManager, NetBoxConnection, AppPreferences, MasterPasswordDialog, \
    MasterPasswordSetupDialog

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
        platform_item.setBackground(QColor(245, 245, 245))  # Light gray background
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


class NetBoxImportWizard(QMainWindow):
    """Consolidated NetBox Import Wizard with Configuration Management"""

    def __init__(self):
        super().__init__()

        # Initialize basic components first
        self.netbox_api = None
        self.discovery_model = DeviceDiscoveryModel()
        self.netbox_data = {}

        # Initialize configuration
        self.config = ConfigManager()

        # Setup UI
        self.setup_ui()

        # Initialize configuration system after UI is ready
        self.initialize_config()

    def initialize_config(self) -> bool:
        """Initialize configuration system"""
        try:
            if not self.config.is_initialized():
                # First time setup
                dialog = MasterPasswordSetupDialog(self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    password = dialog.get_password()
                    if not self.config.setup_master_password(password):
                        QMessageBox.critical(self, "Error", "Failed to initialize credential storage")
                        return False
                else:
                    return False
            else:
                # Unlock existing
                dialog = MasterPasswordDialog(self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    password = dialog.get_password()
                    if not self.config.unlock(password):
                        QMessageBox.warning(self, "Warning",
                                            "Incorrect password. Continuing without saved credentials.")
                        return False
                else:
                    return False

            # After successful unlock, populate UI with saved data
            self.populate_connection_dropdown()

            # Load window preferences
            preferences = self.config.get_preferences()
            self.resize(preferences.window_width, preferences.window_height)

            # Load last used file path
            if preferences.last_file_path:
                self.file_path_input.setText(preferences.last_file_path)

            return True
        except Exception as e:
            QMessageBox.warning(self, "Warning",
                                f"Configuration error: {str(e)}\nContinuing without saved credentials.")
            return False