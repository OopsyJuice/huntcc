# Cloud Clipboard

A session-based cloud clipboard sharing tool for remote support operations.

## Overview

Cloud Clipboard enables technicians to share clipboard content across machines during remote support sessions using simple 6-digit session codes. Each session is completely isolated, allowing multiple techs to work simultaneously without interference.

## Features

- **6-digit session codes** - Easy to share session IDs like TeamViewer/SOS tools
- **Session isolation** - Multiple techs can work simultaneously without interference  
- **System tray integration** - Clean menu-driven interface, no terminal commands needed
- **Hostname tracking** - See which machines are connected to each session
- **Admin dashboard** - Web-based monitoring of all active sessions
- **24-hour auto-expiry** - Sessions automatically clean up
- **Cross-platform** - macOS and Windows support via Python

## Quick Start

### Backend Server Setup
```bash
git clone https://github.com/yourorg/cloud-clipboard.git
cd cloud-clipboard/backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Client Installation
```bash
cd cloud-clipboard/client
source ../backend/venv/bin/activate  # On Windows: ..\backend\venv\Scripts\activate
python clipboard_tray.py
```

### Admin Dashboard
```bash
cd admin
python3 -m http.server 8080
# Open http://localhost:8080/dashboard.html
```

## Usage

### Remote Support Workflow
1. **Tech starts session**: Open system tray app → "Start New Session" → get 6-digit code (e.g., "123456")
2. **Share session code**: Tech gives the 6-digit code to client
3. **Client joins session**: Target machine opens tray app → "Join Session" → enter "123456"  
4. **Share clipboard**: Copy/paste syncs automatically between machines via tray menu
5. **End session**: Either machine clicks "End Session" or auto-expires in 24 hours

### Tray Menu Options
- **Start New Session** - Generate new 6-digit session code
- **Join Session** - Enter existing 6-digit code to connect
- **Send Clipboard** - Push current clipboard to cloud session
- **Get Clipboard** - Pull latest clipboard from cloud session
- **Show History** - View clipboard history for current session
- **End Session** - Terminate session and clear cloud data

## Architecture

- **Backend**: FastAPI REST API with session-based storage and CORS support
- **Client**: Python system tray application using pystray and pyperclip
- **Admin**: Simple HTML dashboard with real-time session monitoring
- **Storage**: In-memory with automatic 24-hour cleanup
- **Authentication**: Bearer token API authentication

## API Endpoints

### Session Management
- `POST /session/start` - Generate new 6-digit session code
- `GET /session/{id}/status` - Get session info and connected hostnames
- `DELETE /session/{id}/end` - End session and clear data

### Clipboard Operations  
- `POST /session/{id}/clipboard` - Add clipboard content to session
- `GET /session/{id}/clipboard/latest` - Get most recent clipboard item
- `GET /session/{id}/clipboard/history` - Get full session clipboard history

### Admin Operations
- `GET /sessions/active` - List all active sessions (admin dashboard)
- `DELETE /sessions/clear` - Clear all sessions (admin only)

## Requirements

- Python 3.8+
- macOS (primary target) or Windows  
- Internet connection for cloud sync
- Modern web browser for admin dashboard

## Security Considerations

- Bearer token authentication on all API endpoints
- Session isolation prevents cross-session data leakage
- Automatic session expiry limits data exposure window
- CORS enabled for admin dashboard web access
- No persistent storage - all data cleared on server restart

## Contributing

This is an internal tool. Contact the development team for access and contribution guidelines.

## License

Internal use only - not for public distribution.