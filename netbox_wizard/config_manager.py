# config_manager.py
import json
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

from PyQt6.QtWidgets import QMessageBox, QPushButton, QHBoxLayout, QLineEdit, QVBoxLayout, QLabel, QDialog, QCheckBox, \
    QComboBox

from helpers.credslib import SecureCredentials


@dataclass
class NetBoxConnection:
    """Configuration for a NetBox connection"""
    name: str
    url: str
    verify_ssl: bool = False
    last_used: str = ""


@dataclass
class AppPreferences:
    """User preferences for the application"""
    window_width: int = 1400
    window_height: int = 900
    last_file_path: str = ""
    default_site_id: Optional[int] = None
    default_role_id: Optional[int] = None
    auto_refresh_netbox_data: bool = True


class ConfigManager:
    """Manages application configuration and secure credential storage"""

    def __init__(self, app_name: str = "NetBoxImportWizard"):
        self.app_name = app_name
        self.credentials = SecureCredentials(app_name)
        self.config_file = self.credentials.config_dir / "config.json"
        self._connections: List[NetBoxConnection] = []
        self._preferences = AppPreferences()

    def is_initialized(self) -> bool:
        """Check if credential system is initialized"""
        return self.credentials.is_initialized

    def setup_master_password(self, password: str) -> bool:
        """Initialize the credential system with master password"""
        return self.credentials.setup_new_credentials(password)

    def unlock(self, password: str) -> bool:
        """Unlock the credential manager"""
        success = self.credentials.unlock(password)
        if success:
            self._load_config()
        return success

    def _load_config(self):
        """Load non-sensitive configuration from file"""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)

            # Load connections (without tokens)
            self._connections = [
                NetBoxConnection(**conn) for conn in data.get('connections', [])
            ]

            # Load preferences
            prefs_data = data.get('preferences', {})
            self._preferences = AppPreferences(**prefs_data)

        except Exception as e:
            print(f"Error loading config: {e}")

    def _save_config(self):
        """Save non-sensitive configuration to file"""
        if not self.credentials.is_unlocked():
            return

        data = {
            'connections': [asdict(conn) for conn in self._connections],
            'preferences': asdict(self._preferences)
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def add_connection(self, name: str, url: str, token: str, verify_ssl: bool = False) -> bool:
        """Add a new NetBox connection"""
        if not self.credentials.is_unlocked():
            return False

        # Check if connection already exists
        existing = self.get_connection(name)
        if existing:
            return self.update_connection(name, url, token, verify_ssl)

        # Create new connection
        connection = NetBoxConnection(name=name, url=url, verify_ssl=verify_ssl)
        self._connections.append(connection)

        # Store token securely
        try:
            token_key = f"netbox_token_{name}"
            encrypted_token = self.credentials.encrypt_value(token)

            # Save to credentials file
            creds_file = self.credentials.config_dir / "credentials.yaml"
            current_creds = self.credentials.load_credentials(creds_file)

            # Update or add token
            token_found = False
            for cred in current_creds:
                if cred.get('key') == token_key:
                    cred['password'] = token
                    token_found = True
                    break

            if not token_found:
                current_creds.append({
                    'key': token_key,
                    'password': token,
                    'type': 'netbox_api_token'
                })

            self.credentials.save_credentials(current_creds, creds_file)
            self._save_config()
            return True

        except Exception as e:
            print(f"Error storing token: {e}")
            return False

    def update_connection(self, name: str, url: str, token: str, verify_ssl: bool = False) -> bool:
        """Update an existing connection"""
        connection = self.get_connection(name)
        if not connection:
            return False

        connection.url = url
        connection.verify_ssl = verify_ssl

        # Update token
        try:
            creds_file = self.credentials.config_dir / "credentials.yaml"
            current_creds = self.credentials.load_credentials(creds_file)

            token_key = f"netbox_token_{name}"
            for cred in current_creds:
                if cred.get('key') == token_key:
                    cred['password'] = token
                    break

            self.credentials.save_credentials(current_creds, creds_file)
            self._save_config()
            return True

        except Exception as e:
            print(f"Error updating token: {e}")
            return False

    def get_connection(self, name: str) -> Optional[NetBoxConnection]:
        """Get connection by name"""
        for conn in self._connections:
            if conn.name == name:
                return conn
        return None

    def get_connection_token(self, name: str) -> Optional[str]:
        """Get API token for connection"""
        if not self.credentials.is_unlocked():
            return None

        try:
            creds_file = self.credentials.config_dir / "credentials.yaml"
            current_creds = self.credentials.load_credentials(creds_file)

            token_key = f"netbox_token_{name}"
            for cred in current_creds:
                if cred.get('key') == token_key:
                    return cred.get('password')

        except Exception as e:
            print(f"Error retrieving token: {e}")

        return None

    def list_connections(self) -> List[NetBoxConnection]:
        """Get all configured connections"""
        return self._connections.copy()

    def delete_connection(self, name: str) -> bool:
        """Delete a connection and its token"""
        if not self.credentials.is_unlocked():
            return False

        # Remove from connections list
        self._connections = [conn for conn in self._connections if conn.name != name]

        # Remove token from credentials
        try:
            creds_file = self.credentials.config_dir / "credentials.yaml"
            current_creds = self.credentials.load_credentials(creds_file)

            token_key = f"netbox_token_{name}"
            current_creds = [cred for cred in current_creds if cred.get('key') != token_key]

            self.credentials.save_credentials(current_creds, creds_file)
            self._save_config()
            return True

        except Exception as e:
            print(f"Error deleting token: {e}")
            return False

    def update_preferences(self, **kwargs):
        """Update user preferences"""
        for key, value in kwargs.items():
            if hasattr(self._preferences, key):
                setattr(self._preferences, key, value)
        self._save_config()

    def get_preferences(self) -> AppPreferences:
        """Get current preferences"""
        return self._preferences

    def update_connection_last_used(self, name: str):
        """Update the last used timestamp for a connection"""
        from datetime import datetime

        connection = self.get_connection(name)
        if connection:
            connection.last_used = datetime.now().isoformat()
            self._save_config()


# Dialog classes for password management (moved here to avoid circular imports)
class MasterPasswordDialog(QDialog):
    """Dialog for entering master password"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Unlock Credential Storage")
        self.setModal(True)
        self.setFixedSize(400, 150)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Enter master password to unlock saved credentials:"))

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.accept)
        layout.addWidget(self.password_input)

        buttons = QHBoxLayout()
        self.ok_btn = QPushButton("Unlock")
        self.cancel_btn = QPushButton("Cancel")

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn.setDefault(True)

        buttons.addWidget(self.ok_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

        # Focus on password input
        self.password_input.setFocus()

    def get_password(self) -> str:
        return self.password_input.text()


class MasterPasswordSetupDialog(QDialog):
    """Dialog for setting up master password"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Setup Credential Storage")
        self.setModal(True)
        self.setFixedSize(450, 200)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Create a master password to securely store NetBox credentials:"))

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Master password (min 8 characters)...")
        layout.addWidget(self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Confirm password...")
        self.confirm_input.returnPressed.connect(self.validate_and_accept)
        layout.addWidget(self.confirm_input)

        # Password strength indicator
        self.strength_label = QLabel("Password strength: ")
        layout.addWidget(self.strength_label)

        buttons = QHBoxLayout()
        self.ok_btn = QPushButton("Create")
        self.cancel_btn = QPushButton("Cancel")

        self.ok_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn.setDefault(True)

        buttons.addWidget(self.ok_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

        # Connect password change to strength indicator
        self.password_input.textChanged.connect(self.update_strength)

    def update_strength(self, password: str):
        """Update password strength indicator"""
        if len(password) == 0:
            self.strength_label.setText("Password strength: ")
            self.strength_label.setStyleSheet("")
        elif len(password) < 8:
            self.strength_label.setText("Password strength: Too short")
            self.strength_label.setStyleSheet("color: red")
        elif len(password) < 12:
            self.strength_label.setText("Password strength: Good")
            self.strength_label.setStyleSheet("color: orange")
        else:
            self.strength_label.setText("Password strength: Strong")
            self.strength_label.setStyleSheet("color: green")

    def validate_and_accept(self):
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not password:
            QMessageBox.warning(self, "Error", "Password cannot be empty")
            return

        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        if len(password) < 8:
            QMessageBox.warning(self, "Error", "Password must be at least 8 characters")
            return

        self.accept()

    def get_password(self) -> str:
        return self.password_input.text()