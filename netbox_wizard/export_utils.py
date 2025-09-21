"""
Export utilities for NetBox Import Wizard
Handles CSV export from the device discovery table
"""
import csv
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTableWidget
from PyQt6.QtCore import QStandardPaths


def export_device_table_to_csv(table_widget: QTableWidget, parent_widget=None) -> bool:
    """Export current device table to CSV"""
    if table_widget.rowCount() == 0:
        QMessageBox.information(parent_widget, "No Data", "No devices to export")
        return False

    # Get default documents directory
    documents_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"netbox_devices_discovery_{timestamp}.csv"
    default_path = str(Path(documents_dir) / default_filename)

    # Open file dialog
    file_path, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Export Device Discovery to CSV",
        default_path,
        "CSV files (*.csv)"
    )

    if not file_path:
        return False

    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            headers = [
                'Selected for Import',
                'Device Name',
                'IP Address',
                'Discovered Platform',
                'NetBox Platform',
                'NetBox Status',
                'Site',
                'Role',
                'Device Type'
            ]
            writer.writerow(headers)

            # Write data rows
            for row in range(table_widget.rowCount()):
                row_data = []

                # Import checkbox
                import_checkbox = table_widget.cellWidget(row, 0)
                row_data.append('Yes' if import_checkbox and import_checkbox.isChecked() else 'No')

                # Device Name, IP, Discovered Platform (regular items)
                for col in [1, 2, 3]:
                    item = table_widget.item(row, col)
                    row_data.append(item.text() if item else '')

                # NetBox Platform (combo box)
                platform_combo = table_widget.cellWidget(row, 4)
                if platform_combo and platform_combo.currentData():
                    row_data.append(platform_combo.currentText())
                else:
                    row_data.append('-- Not Selected --')

                # NetBox Status (regular item)
                status_item = table_widget.item(row, 5)
                row_data.append(status_item.text() if status_item else '')

                # Site, Role, Device Type (combo boxes)
                for col in [6, 7, 8]:
                    combo = table_widget.cellWidget(row, col)
                    if combo and combo.currentData():
                        row_data.append(combo.currentText())
                    else:
                        row_data.append('-- Not Selected --')

                writer.writerow(row_data)

        QMessageBox.information(
            parent_widget,
            "Export Complete",
            f"Device discovery data exported to:\n{file_path}\n\n{table_widget.rowCount()} devices exported"
        )
        return True

    except Exception as e:
        QMessageBox.critical(
            parent_widget,
            "Export Error",
            f"Failed to export data:\n{str(e)}"
        )
        return False


def get_device_table_summary(table_widget: QTableWidget) -> dict:
    """Get summary statistics for the device table"""
    total_devices = table_widget.rowCount()
    selected_devices = 0
    configured_devices = 0
    new_devices = 0
    existing_devices = 0

    for row in range(total_devices):
        # Count selected
        import_checkbox = table_widget.cellWidget(row, 0)
        if import_checkbox and import_checkbox.isChecked():
            selected_devices += 1

        # Count configured (has platform, site, role, type)
        platform_combo = table_widget.cellWidget(row, 4)
        site_combo = table_widget.cellWidget(row, 6)
        role_combo = table_widget.cellWidget(row, 7)
        type_combo = table_widget.cellWidget(row, 8)

        if (platform_combo and platform_combo.currentData() and
                site_combo and site_combo.currentData() and
                role_combo and role_combo.currentData() and
                type_combo and type_combo.currentData()):
            configured_devices += 1

        # Count new vs existing
        status_item = table_widget.item(row, 5)
        if status_item:
            if "New device" in status_item.text():
                new_devices += 1
            elif "match" in status_item.text():
                existing_devices += 1

    return {
        'total': total_devices,
        'selected': selected_devices,
        'configured': configured_devices,
        'new': new_devices,
        'existing': existing_devices
    }