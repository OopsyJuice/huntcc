# Cloud Clipboard

A session-based cloud clipboard sharing tool for MSP remote support operations.

## Overview

Cloud Clipboard allows multiple technicians to share clipboard content across machines during remote support sessions. Each tech gets their own isolated session identified by a numeric session ID.

## Features

- **Session-based isolation** - Multiple techs can work simultaneously without interference
- **System tray integration** - No terminal commands needed during operation
- **Cross-platform clipboard sync** - macOS and Windows support
- **24-hour auto-expiry** - Sessions automatically clean up
- **Admin dashboard** - Monitor active sessions and manage tech assignments

## Quick Start

### Current Development Setup
```bash
git clone https://github.com/yourorg/cloud-clipboard.git
cd cloud-clipboard/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Client Installation (Target Machines)
```bash
cd cloud-clipboard/client
source ../backend/venv/bin/activate
python clipboard_tray.py
```

*Note: Simple install script coming soon for production deployment*

## Usage

1. **Tech starts session**: Open system tray app, enter session ID (e.g., "1234")
2. **Connect target machine**: User opens tray app, enters same session ID
3. **Share clipboard**: Copy/paste syncs automatically between machines
4. **End session**: Tech clicks "End Session" or auto-expires in 24 hours

## Architecture

- **Backend**: FastAPI REST API with session management
- **Client**: Python system tray application using pystray
- **Deployment**: Cloud server + git clone workflow
- **Distribution**: Simple install script (planned)
- **Storage**: In-memory with automatic cleanup

## Development Status

- Basic clipboard sync functionality
- System tray integration
- Authentication and API structure
- Multi-session support (in progress)
- Admin dashboard (planned)
- Simple install script (planned)

## Requirements

- Python 3.8+
- macOS (primary target) or Windows
- Internet connection for cloud sync

## Contributing

This is an internal MSP tool. Contact the development team for access and contribution guidelines.

## License

Internal use only - not for public distribution.