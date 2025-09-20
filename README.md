# SecureCartography - NetBox Import Wizard

A PyQt6-based GUI wizard for importing network topology data from SecureCartography JSON files into NetBox DCIM (Data Center Infrastructure Management) systems.

## Overview

The NetBox Import Wizard bridges the gap between network discovery tools and NetBox inventory management by providing an intuitive interface for importing discovered network devices, their connections, and metadata into NetBox. This significantly reduces the manual effort required to populate NetBox with real-world network topology data.

## Current Status: Alpha - Core Functions Working

### ✅ Working Features

**Connection Management:**
- NetBox API connection with configurable SSL verification
- Self-signed certificate support (disabled SSL verification by default)
- Connection testing and validation
- Token-based authentication

**Topology File Loading:**
- Robust JSON parsing with error recovery for missing/malformed fields
- Support for dynamic topology files with varying data completeness
- Device deduplication and peer device discovery
- Platform and connection data extraction

**Device Discovery & Mapping:**
- Automatic device matching against existing NetBox inventory
- Match detection by device name and IP address
- Visual status indicators (yellow for existing matches, green for new devices)
- Smart action defaulting (Skip for existing, Create new for discovered)

**NetBox Integration:**
- Live data population from NetBox API (sites, device roles, device types, manufacturers)
- Dropdown combo boxes populated with current NetBox configuration
- Caching for improved performance
- Support for 384+ sites, 50+ roles, 367+ device types (as shown in testing)

**User Interface:**
- Three-tab wizard workflow (Connection → Discovery → Import)
- Sortable device table with real-time status
- Manual refresh and population controls
- Status bar feedback and error messaging

### 🚧 Known Issues & Limitations

**Performance Issues:**
- **CRITICAL**: Topology loading is synchronous and blocks UI thread
- Large topology files cause application freeze during processing
- No progress indication during NetBox API calls

**UI/UX Gaps:**
- Platform field should be dropdown instead of read-only text
- Missing progress bars for long-running operations
- No status text during loading operations
- Tab 2 has unused space that could accommodate progress indicators

**Incomplete Features:**
- Import validation logic exists but import execution is not implemented
- Cable/connection creation not yet supported
- No bulk operations (site assignment, role assignment)
- Auto-platform mapping logic not implemented

## Technical Architecture

### Dependencies
- **PyQt6.5**: Modern Qt6-based GUI framework
- **pynetbox**: NetBox API client library
- **urllib3**: HTTP library with SSL warning suppression
- **requests**: HTTP session management for SSL configuration

### Key Components

**NetBoxAPI Class:**
- Wrapper around pynetbox with SSL configuration
- Caching layer for performance optimization
- Error handling for API failures

**DeviceDiscoveryModel:**
- JSON topology parsing and validation
- Device matching algorithm implementation
- Data structure normalization

**DeviceTableWidget:**
- Custom QTableWidget with embedded combo boxes
- Dynamic NetBox data population
- Real-time device status visualization

**NetBoxImportWizard:**
- Main application window with tab-based workflow
- Connection management and file loading
- Coordinated data flow between components

## Installation & Setup

### Prerequisites
```bash
pip install PyQt6 pynetbox requests urllib3
```

### Configuration
1. **NetBox Setup**: Ensure NetBox API is accessible and API token has appropriate permissions:
   - `dcim.view_site`
   - `dcim.view_devicerole`
   - `dcim.view_devicetype`
   - `dcim.view_manufacturer`
   - `dcim.view_device`
   - `dcim.add_device` (for import functionality)

2. **SSL Configuration**: For lab environments with self-signed certificates, leave "Verify SSL Certificate" unchecked

### Usage
```bash
python netbox_import_wizard.py
```

## Topology File Format

The wizard expects JSON files with the following structure:

```json
{
  "device-name": {
    "node_details": {
      "ip": "10.1.1.1",
      "platform": "C9407R"
    },
    "peers": {
      "peer-device": {
        "ip": "10.1.1.2", 
        "platform": "C9200L-48P-4X",
        "connections": [
          ["Gi1/0/1", "Te1/1/4"],
          ["Gi1/0/2", "Te1/1/3"]
        ]
      }
    }
  }
}
```

**Field Requirements:**
- All fields are optional (robust error handling)
- Missing `node_details`, `peers`, or connection data is handled gracefully
- Platform strings are used for device type mapping
- IP addresses enable device matching in NetBox

## Roadmap & TODO

### High Priority (Next Release)

**Threading & Performance:**
- [ ] Implement QThread for topology file loading
- [ ] Add progress bars during NetBox API operations
- [ ] Implement async NetBox data fetching with progress indicators
- [ ] Add loading status text and cancellation support

**UI Improvements:**
- [ ] Convert Platform column to dropdown with discovered platforms
- [ ] Add progress bar to Tab 1 during connection testing
- [ ] Implement progress indicators in Tab 2 unused space
- [ ] Add bulk selection and operations

**Core Functionality:**
- [ ] Complete import execution logic (device creation in NetBox)
- [ ] Implement validation system for required fields
- [ ] Add auto-platform mapping intelligence
- [ ] Support for bulk site/role assignment

### Medium Priority

**Advanced Features:**
- [ ] Cable and connection import from topology data
- [ ] Device interface creation and mapping
- [ ] Rack assignment based on naming conventions
- [ ] IP address assignment from discovered data
- [ ] Import rollback and error recovery

**Enhanced Matching:**
- [ ] Fuzzy name matching algorithms
- [ ] MAC address-based device matching
- [ ] Serial number correlation
- [ ] Multiple matching criteria weighting

### Low Priority (Future Versions)

**Integration & Export:**
- [ ] Export device lists to CSV/Excel
- [ ] Integration with other DCIM tools
- [ ] Custom field mapping support
- [ ] Scheduled import capabilities

**Advanced UI:**
- [ ] Device filtering and search
- [ ] Import history and logging
- [ ] Configuration templates
- [ ] Multi-file batch processing

## Contributing

The project is in active development. Key areas needing attention:

1. **Threading Implementation**: Replace blocking operations with QThread-based async processing
2. **Progress Indication**: Add comprehensive progress feedback throughout the workflow
3. **Import Logic**: Complete the actual NetBox device creation functionality
4. **Platform Intelligence**: Develop smart mapping between discovered platforms and NetBox device types

## Architecture Decisions

**SSL Handling**: Defaults to disabled SSL verification to support common lab environments with self-signed certificates while maintaining option for production security.

**Caching Strategy**: Aggressive caching of NetBox API responses to minimize network calls and improve responsiveness.

**Error Recovery**: Comprehensive validation and normalization of input data to handle real-world topology files with missing or inconsistent data.

**Widget Management**: Integrated combo box population during table creation to avoid dynamic reference issues in PyQt6.

## Testing Environment

Validated against:
- NetBox instance with 384 sites, 50 device roles, 367 device types
- Topology files with 25+ network devices
- Mixed Cisco platforms (C9407R, C9200L-48P-4X, WS-series)
- Self-signed SSL certificates

The wizard successfully loads complex network topologies and provides intuitive device management workflows for NetBox population.