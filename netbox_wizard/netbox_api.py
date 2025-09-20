"""
NetBox API wrapper and utilities
"""
from typing import Dict, List, Optional
import pynetbox


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