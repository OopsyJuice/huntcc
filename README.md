# Cloud Clipboard

A session-based cloud clipboard sharing tool for remote support operations.

## Overview

Cloud Clipboard enables technicians to share clipboard content across machines during remote support sessions using simple 6-digit session codes. Each session is completely isolated, allowing multiple techs to work simultaneously without interference.

## Features

- **6-digit session codes** - Easy to share session IDs like TeamViewer/SOS tools
- **Session isolation** - Multiple techs can work simultaneously without interference  
- **System tray integration** - Clean menu-driven interface, no terminal commands needed
- **Hostname tracking** - See which machines are connected to each session
- **Embedded admin dashboard** - Built-in web interface for session management
- **24-hour auto-expiry** - Sessions automatically clean up
- **Cross-platform** - macOS and Windows support via Python

## Quick Start

### Installation and Setup
```bash
git clone https://github.com/OopsyJuice/huntcc.git
cd huntcc
bash install.sh
```

### Running the Application
```bash
python3 app.py
```

The app will start and appear in your system tray. The admin dashboard URL will be displayed in the terminal.

## Usage

### Remote Support Workflow
1. **Tech starts session**: Right-click tray icon → "Start New Session" → get 6-digit code (e.g., "123456")
2. **Share session code**: Tech gives the 6-digit code to client
3. **Client joins session**: Target machine runs the same app → "Join Session" → enter "123456"  
4. **Share clipboard**: Copy/paste syncs automatically between machines via tray menu
5. **End session**: Either machine clicks "End Session" or auto-expires in 24 hours

### Tray Menu Options
- **Start New Session** - Generate new 6-digit session code
- **Join Session** - Enter existing 6-digit code to connect
- **Send Clipboard** - Push current clipboard to cloud session
- **Get Clipboard** - Pull latest clipboard from cloud session
- **End Session** - Terminate session and clear cloud data

### Admin Dashboard

When the app starts, it displays an admin dashboard URL in the terminal:
```
Admin dashboard: http://localhost:52431/admin
```

Open this URL in your browser to:
- **View all active sessions** with hostnames and activity
- **End sessions remotely** if needed
- **Monitor clipboard activity** across all sessions

The dashboard auto-refreshes every 10 seconds and uses the same API as the tray application.

## Architecture

- **Combined Application** - Single `app.py` file runs both backend API and tray client
- **Session-based** - Each 6-digit code creates isolated clipboard sharing
- **In-memory storage** - No database required, automatic 24-hour cleanup
- **Local API** - Backend runs on random local port, no external server needed
- **Embedded dashboard** - Admin interface served directly by the app

## Requirements

- Python 3.8+
- macOS (primary target) or Windows  
- Dependencies installed via `install.sh`

## Project Structure

```
huntcc/
├── app.py              # Combined backend + tray client (main file)
├── requirements.txt    # All dependencies
├── install.sh         # One-click installer
├── assets/            # Tray icon resources (paperclip image)
├── legacy/            # Original separate components (for reference)
│   ├── backend/       # Original FastAPI backend
│   ├── client/        # Original tray client
│   └── admin/         # Original standalone admin dashboard
└── README.md
```

## For Developers

### Running Legacy Components Separately
For development purposes, you can still run the original backend and client separately:

```bash
# Backend only
cd legacy/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Client only (in another terminal)
cd legacy/client
python clipboard_tray.py
```

### Legacy Admin Dashboard
```bash
cd legacy/admin
python3 -m http.server 8080
# Open http://localhost:8080/dashboard.html
```

Note: The legacy admin dashboard won't work with the combined app since it expects the API on port 8000. Use the embedded dashboard instead.

## Security Considerations

- Bearer token authentication on all API endpoints
- Session isolation prevents cross-session data leakage
- Automatic session expiry limits data exposure window
- Local-only API server (not exposed to internet)
- No persistent storage - all data cleared on app restart

