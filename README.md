# SecureCartography - NetBox Import Wizard

A PyQt6-based GUI wizard for importing network topology data from SecureCartography JSON files into NetBox DCIM (Data Center Infrastructure Management) systems.

## Overview

The NetBox Import Wizard bridges the gap between network discovery tools and NetBox inventory management by providing an intuitive interface for importing discovered network devices, their connections, and metadata into NetBox. This significantly reduces the manual effort required to populate NetBox with real-world network topology data.

## Current Status: Production Ready - Core Functions Complete

### ✅ Working Features

**Multi-threaded Architecture:**
- Non-blocking UI with proper threading for all long-running operations
- Dedicated threads for NetBox connection testing, topology loading, data fetching, and device import
- Progress bars and status updates for all major operations
- Cancellation support for import operations

**Connection Management:**
- NetBox API connection with configurable SSL verification
- Self-signed certificate support (disabled SSL verification by default)
- Threaded connection testing with detailed feedback
- Token-based authentication with connection caching

**Topology File Loading:**
- Robust JSON parsing with comprehensive error recovery
- Threaded file loading with progress indication
- Support for dynamic topology files with varying data completeness
- Device deduplication and peer device discovery
- Platform and connection data extraction with validation

**Device Discovery & Mapping:**
- Automatic device matching against existing NetBox inventory
- Match detection by device name and IP address (case-insensitive)
- Visual status indicators (yellow for existing matches, green for new devices)
- Smart action defaulting (Skip for existing, Create new for discovered)
- Comprehensive peer device extraction and flattening

**NetBox Integration:**
- Threaded data population from NetBox API (sites, device roles, device types, manufacturers, platforms)
- Live dropdown combo boxes populated with current NetBox configuration
- Comprehensive caching system for improved performance
- Full CRUD operations support for device creation

**User Interface:**
- Three-tab wizard workflow (Connection → Discovery → Import)
- Sortable device table with real-time status indicators
- Progress bars for all long-running operations with percentage completion
- Manual refresh and population controls
- Comprehensive status bar feedback and error messaging
- Import validation and execution with detailed logging

**Import System:**
- Complete device import functionality with threaded execution
- Real-time progress tracking and logging
- Validation system for required fields before import
- Import cancellation support
- Detailed success/failure reporting with color-coded results

### 🚧 Known Issues & Limitations

**Data Processing:**
- Platform data is fetched from NetBox but dropdown implementation is incomplete (displays as text field)
- Auto-platform mapping logic not yet implemented  
- No bulk operations for site/role assignment

**Advanced Features:**
- Cable/connection creation not yet supported
- Device interface creation not implemented
- No rack assignment logic
- IP address assignment from topology data not supported

**UI Polish:**
- Some unused space in discovery tab
- Limited filtering and search capabilities
- No export functionality for device lists

## Technical Architecture

### Dependencies
- **PyQt6**: Modern Qt6-based GUI framework with threading support
- **pynetbox**: NetBox API client library
- **urllib3**: HTTP library with SSL warning suppression
- **requests**: HTTP session management for SSL configuration

### Key Components

**Threading Classes:**
- **NetBoxConnectionThread**: Non-blocking connection testing
- **TopologyLoadThread**: Asynchronous file loading with progress
- **NetBoxDataThread**: Background NetBox data fetching
- **DeviceImportThread**: Threaded device creation with cancellation support

**Core Classes:**
- **NetBoxAPI**: Wrapper around pynetbox with SSL configuration and caching
- **DeviceDiscoveryModel**: JSON topology parsing, validation, and device matching
- **DeviceTableWidget**: Custom table with embedded combo boxes and status visualization
- **NetBoxImportWizard**: Main application coordinating all components

### Threading Architecture
The application uses Qt's threading system to prevent UI blocking:
- All API calls run in separate QThread instances
- Progress signals provide real-time feedback
- Proper thread lifecycle management with cleanup
- UI remains responsive during all operations

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
   - `dcim.view_platform`
   - `dcim.add_device` (for import functionality)

2. **SSL Configuration**: For lab environments with self-signed certificates, leave "Verify SSL Certificate" unchecked

### Usage
```bash
python nbwiz.py
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
- All fields are optional with comprehensive error handling
- Missing `node_details`, `peers`, or connection data handled gracefully
- Platform strings extracted for device type mapping
- IP addresses enable device matching in NetBox
- Peer devices automatically discovered and added to device list

## Roadmap & TODO

### High Priority (Next Release)

**UI Improvements:**
- [ ] Convert Platform column to dropdown with auto-population
- [ ] Add device filtering and search functionality
- [ ] Implement bulk selection and operations
- [ ] Add export functionality (CSV/Excel)

**Advanced Features:**
- [ ] Auto-platform mapping intelligence with configurable rules
- [ ] Cable and connection import from topology data
- [ ] Device interface creation and mapping
- [ ] Rack assignment based on naming conventions

### Medium Priority

**Enhanced Matching:**
- [ ] Fuzzy name matching algorithms
- [ ] MAC address-based device matching
- [ ] Serial number correlation
- [ ] Multiple matching criteria with weighting

**Data Management:**
- [ ] IP address assignment from discovered data
- [ ] Custom field mapping support
- [ ] Import rollback and error recovery
- [ ] Configuration templates and presets

### Low Priority (Future Versions)

**Integration & Advanced Features:**
- [ ] Integration with other DCIM tools
- [ ] Scheduled import capabilities
- [ ] Multi-file batch processing
- [ ] Import history and audit logging
- [ ] REST API for programmatic access

## Performance Characteristics

**Tested Scale:**
- NetBox instances with 384+ sites, 50+ device roles, 367+ device types
- Topology files with 25+ network devices
- Mixed vendor platforms (Cisco, Juniper, etc.)
- Self-signed SSL certificate environments

**Threading Benefits:**
- UI remains responsive during large file processing
- Real-time progress feedback for all operations
- Graceful handling of API timeouts and errors
- Proper resource cleanup and memory management

## Contributing

The project is in active development. Key areas for contribution:

1. **Platform Intelligence**: Develop smart mapping between discovered platforms and NetBox device types
2. **Connection Processing**: Implement cable/interface creation from topology data
3. **UI Enhancement**: Add advanced filtering, search, and bulk operations
4. **Error Handling**: Improve validation and recovery mechanisms

## Architecture Decisions

**Threading Model**: Uses Qt's QThread system for true parallelism while maintaining thread safety and proper UI updates.

**SSL Handling**: Defaults to disabled SSL verification to support common lab environments while maintaining production security options.

**Caching Strategy**: Aggressive caching of NetBox API responses with manual refresh capability to balance performance and data freshness.

**Error Recovery**: Comprehensive validation and normalization throughout the data pipeline to handle real-world topology files with inconsistent data.

**Progress Feedback**: Multi-level progress indication from file operations through API calls to provide transparency in long-running operations.

## Testing Environment

Successfully validated against:
- NetBox 3.x instances with production-scale data
- Complex network topologies with mixed vendor equipment
- Self-signed SSL certificates in lab environments
- Large topology files (100+ devices)
- Concurrent operations and stress testing

The wizard provides a robust, production-ready solution for bulk NetBox device import with comprehensive error handling and user feedback.