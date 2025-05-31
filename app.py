#!/usr/bin/env python3
"""
Cloud Clipboard - Combined Backend + Tray Client
Single executable that runs both server and client
"""

import threading
import time
import socket
import sys
import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

# FastAPI Backend imports
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Tray Client imports
import pystray
import pyperclip
import requests
from PIL import Image

# Find available port automatically
def find_available_port():
    """Find an available port for the embedded server"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

# Global configuration
API_PORT = find_available_port()
API_URL = f"http://localhost:{API_PORT}"
API_KEY = "embedded-clipboard-api-key-2024"

print(f"Starting Cloud Clipboard on port {API_PORT}")

# ===== BACKEND CODE =====
app = FastAPI(title="Cloud Clipboard API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

security = HTTPBearer()
session_storage: Dict[str, Dict] = {}

class ClipboardItem(BaseModel):
    content: str
    hostname: Optional[str] = None
    timestamp: Optional[datetime] = None
    id: Optional[str] = None

class ClipboardResponse(BaseModel):
    id: str
    content: str
    timestamp: datetime
    hostname: Optional[str] = None

class SessionStatus(BaseModel):
    session_id: str
    created_at: datetime
    last_activity: datetime
    hostnames: List[str]
    item_count: int

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

def cleanup_expired_sessions():
    """Remove sessions older than 24 hours"""
    now = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in session_storage.items():
        if now - session_data["last_activity"] > timedelta(hours=24):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del session_storage[session_id]
    
    return len(expired_sessions)

def get_or_create_session(session_id: str, hostname: Optional[str] = None):
    """Get existing session or create new one"""
    cleanup_expired_sessions()
    
    if session_id not in session_storage:
        session_storage[session_id] = {
            "items": [],
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "hostnames": []
        }
    
    session_storage[session_id]["last_activity"] = datetime.now()
    
    if hostname and hostname not in session_storage[session_id]["hostnames"]:
        session_storage[session_id]["hostnames"].append(hostname)
    
    return session_storage[session_id]

def generate_session_code():
    """Generate a unique 6-digit session code"""
    while True:
        code = str(random.randint(100000, 999999))
        if code not in session_storage:
            return code

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Cloud Clipboard API v2.0 is running"}

@app.get("/admin")
async def admin_dashboard():
    """Serve the admin dashboard with correct API port"""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Clipboard Admin</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f7;
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            margin: 0;
            color: #1d1d1f;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #007AFF;
        }}
        
        .stat-label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        
        .sessions {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .sessions-header {{
            padding: 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .refresh-btn {{
            background: #007AFF;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
        }}
        
        .session-item {{
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .session-item:last-child {{
            border-bottom: none;
        }}
        
        .session-id {{
            font-family: monospace;
            font-size: 18px;
            font-weight: bold;
            color: #007AFF;
        }}
        
        .session-info {{
            flex-grow: 1;
            margin-left: 20px;
        }}
        
        .hostnames {{
            font-size: 14px;
            color: #333;
        }}
        
        .activity {{
            font-size: 12px;
            color: #999;
        }}
        
        .end-btn {{
            background: #FF3B30;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }}
        
        .empty {{
            padding: 40px;
            text-align: center;
            color: #666;
        }}
        
        .error {{
            background: #FF3B30;
            color: white;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Cloud Clipboard Admin</h1>
            <div id="status">Loading...</div>
        </div>
        
        <div id="error" class="error" style="display: none;"></div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="total-sessions">-</div>
                <div class="stat-label">Active Sessions</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-hosts">-</div>
                <div class="stat-label">Connected Hosts</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="total-items">-</div>
                <div class="stat-label">Clipboard Items</div>
            </div>
        </div>
        
        <div class="sessions">
            <div class="sessions-header">
                <h2>Active Sessions</h2>
                <button class="refresh-btn" onclick="loadSessions()">Refresh</button>
            </div>
            <div id="sessions-list">
                <div class="empty">Loading...</div>
            </div>
        </div>
    </div>

    <script>
        const API_URL = 'http://localhost:{API_PORT}';
        const API_KEY = '{API_KEY}';
        
        function showError(message) {{
            const errorEl = document.getElementById('error');
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }}
        
        function hideError() {{
            document.getElementById('error').style.display = 'none';
        }}
        
        async function apiCall(endpoint, method = 'GET') {{
            const response = await fetch(`${{API_URL}}${{endpoint}}`, {{
                method,
                headers: {{
                    'Authorization': `Bearer ${{API_KEY}}`,
                    'Content-Type': 'application/json'
                }}
            }});
            
            if (!response.ok) {{
                throw new Error(`HTTP ${{response.status}}`);
            }}
            
            return await response.json();
        }}
        
        function formatTime(timestamp) {{
            const date = new Date(timestamp);
            const now = new Date();
            const diff = Math.floor((now - date) / 1000);
            
            if (diff < 60) return `${{diff}}s ago`;
            if (diff < 3600) return `${{Math.floor(diff/60)}}m ago`;
            return `${{Math.floor(diff/3600)}}h ago`;
        }}
        
        async function endSession(sessionId) {{
            if (!confirm(`End session ${{sessionId}}?`)) return;
            
            try {{
                await apiCall(`/session/${{sessionId}}/end`, 'DELETE');
                loadSessions();
            }} catch (error) {{
                showError(`Failed to end session: ${{error.message}}`);
            }}
        }}
        
        async function loadSessions() {{
            hideError();
            
            try {{
                const sessions = await apiCall('/sessions/active');
                
                // Update stats
                document.getElementById('total-sessions').textContent = sessions.length;
                
                const allHosts = new Set();
                let totalItems = 0;
                
                sessions.forEach(session => {{
                    session.hostnames.forEach(host => allHosts.add(host));
                    totalItems += session.item_count;
                }});
                
                document.getElementById('total-hosts').textContent = allHosts.size;
                document.getElementById('total-items').textContent = totalItems;
                
                // Update sessions list
                const sessionsList = document.getElementById('sessions-list');
                
                if (sessions.length === 0) {{
                    sessionsList.innerHTML = '<div class="empty">No active sessions</div>';
                }} else {{
                    const html = sessions.map(session => `
                        <div class="session-item">
                            <div>
                                <div class="session-id">${{session.session_id}}</div>
                            </div>
                            <div class="session-info">
                                <div class="hostnames">${{session.hostnames.join(', ') || 'No hosts'}}</div>
                                <div class="activity">Last: ${{formatTime(session.last_activity)}} • ${{session.item_count}} items</div>
                            </div>
                            <button class="end-btn" onclick="endSession('${{session.session_id}}')">End</button>
                        </div>
                    `).join('');
                    sessionsList.innerHTML = html;
                }}
                
                document.getElementById('status').textContent = `Updated: ${{new Date().toLocaleTimeString()}}`;
                
            }} catch (error) {{
                showError(`Error: ${{error.message}}`);
                document.getElementById('sessions-list').innerHTML = '<div class="empty">Failed to load</div>';
            }}
        }}
        
        // Load on start
        loadSessions();
        
        // Auto-refresh every 10 seconds
        setInterval(loadSessions, 10000);
    </script>
</body>
</html>"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

@app.post("/session/start")
async def start_session(api_key: str = Depends(verify_api_key)):
    cleanup_expired_sessions()
    session_id = generate_session_code()
    session_storage[session_id] = {
        "items": [],
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
        "hostnames": []
    }
    return {"session_id": session_id}

@app.post("/session/{session_id}/clipboard", response_model=ClipboardResponse)
async def add_clipboard_item(
    session_id: str,
    item: ClipboardItem, 
    api_key: str = Depends(verify_api_key)
):
    session_data = get_or_create_session(session_id, item.hostname)
    
    item_id = f"clip_{session_id}_{len(session_data['items']) + 1}"
    timestamp = datetime.now()
    
    clipboard_entry = {
        "id": item_id,
        "content": item.content,
        "timestamp": timestamp,
        "hostname": item.hostname or "unknown"
    }
    
    session_data["items"].append(clipboard_entry)
    
    if len(session_data["items"]) > 10:
        session_data["items"].pop(0)
    
    return ClipboardResponse(**clipboard_entry)

@app.get("/session/{session_id}/clipboard/latest", response_model=ClipboardResponse)
async def get_latest_clipboard(
    session_id: str,
    hostname: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    session_data = get_or_create_session(session_id, hostname)
    
    if not session_data["items"]:
        raise HTTPException(status_code=404, detail="No clipboard items found in session")
    
    latest_item = session_data["items"][-1]
    return ClipboardResponse(**latest_item)

@app.get("/session/{session_id}/clipboard/history", response_model=List[ClipboardResponse])
async def get_clipboard_history(
    session_id: str,
    hostname: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    session_data = get_or_create_session(session_id, hostname)
    return [ClipboardResponse(**item) for item in session_data["items"]]

@app.delete("/session/{session_id}/end")
async def end_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    if session_id in session_storage:
        del session_storage[session_id]
        return {"message": f"Session {session_id} ended and data cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions/active", response_model=List[SessionStatus])
async def get_active_sessions(api_key: str = Depends(verify_api_key)):
    cleanup_expired_sessions()
    sessions = []
    for session_id, session_data in session_storage.items():
        sessions.append(SessionStatus(
            session_id=session_id,
            created_at=session_data["created_at"],
            last_activity=session_data["last_activity"],
            hostnames=session_data["hostnames"],
            item_count=len(session_data["items"])
        ))
    return sessions

# ===== TRAY CLIENT CODE =====
class CloudClipboardTray:
    def __init__(self):
        self.api_url = API_URL
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        self.icon = None
        self.last_status = "Ready"
        self.session_id = None
        self.hostname = socket.gethostname()
        self.config_file = "clipboard_config.json"
        
        self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.session_id = config.get("session_id")
        except Exception as e:
            print(f"Could not load config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {"session_id": self.session_id}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Could not save config: {e}")
    
    def start_session(self, icon=None, item=None):
        """Generate new 6-digit session code"""
        try:
            response = requests.post(
                f"{self.api_url}/session/start",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data["session_id"]
                self.save_config()
                self.show_notification(f"✓ Session {self.session_id} started")
                print(f"\n=== NEW SESSION STARTED ===")
                print(f"Session Code: {self.session_id}")
                print(f"Share this code with the other machine")
                print(f"==============================")
                if self.icon:
                    self.icon.menu = self.create_menu()
                return True
            else:
                self.show_notification(f"✗ Start failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.show_notification(f"✗ Start error: {str(e)[:30]}")
            return False
    
    def join_session(self, icon=None, item=None):
        """Join existing session by entering session code"""
        print(f"\n--- Join Session ---")
        print(f"Current session: {self.session_id or 'None'}")
        print(f"Hostname: {self.hostname}")
        
        try:
            session_code = input("Enter 6-digit session code: ").strip()
            if session_code and len(session_code) == 6 and session_code.isdigit():
                # Test if session exists
                response = requests.get(
                    f"{self.api_url}/sessions/active",
                    headers=self.headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    sessions = response.json()
                    session_exists = any(s["session_id"] == session_code for s in sessions)
                    
                    if session_exists:
                        self.session_id = session_code
                        self.save_config()
                        self.show_notification(f"✓ Joined session {self.session_id}")
                        print(f"Successfully joined session: {self.session_id}")
                        if self.icon:
                            self.icon.menu = self.create_menu()
                    else:
                        print("Session not found or expired")
                        self.show_notification("Session not found")
                else:
                    print("Could not check session status")
                    self.show_notification("Connection error")
            else:
                print("Invalid session code (must be 6 digits)")
                self.show_notification("Invalid session code")
        except (KeyboardInterrupt, EOFError):
            print("Join cancelled")
            self.show_notification("Join cancelled")
        except Exception as e:
            print(f"Error joining session: {e}")
            self.show_notification(f"Join error: {str(e)[:30]}")
    
    def create_icon_image(self):
        """Create simple tray icon"""
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, 'assets', 'paper-clip.png')
            
            # Load and resize the image
            image = Image.open(icon_path)
            # Resize to 64x64 if needed
            image = image.resize((64, 64), Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            print(f"Warning: Could not load icon file: {e}")
            # Fallback to a simple colored square
            image = Image.new('RGBA', (64, 64), (70, 130, 180, 255))
            return image
    
    def send_clipboard(self, icon=None, item=None):
        """Send current clipboard content to cloud"""
        if not self.session_id:
            self.show_notification("No session active")
            return False
            
        try:
            content = pyperclip.paste()
            if not content.strip():
                self.show_notification("Clipboard is empty")
                return False
            
            response = requests.post(
                f"{self.api_url}/session/{self.session_id}/clipboard",
                headers=self.headers,
                json={"content": content, "hostname": self.hostname},
                timeout=5
            )
            
            if response.status_code == 200:
                self.show_notification(f"✓ Sent {len(content)} chars")
                return True
            else:
                self.show_notification(f"✗ Send failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.show_notification(f"✗ Send error: {str(e)[:30]}")
            return False
    
    def get_clipboard(self, icon=None, item=None):
        """Get latest clipboard content from cloud"""
        if not self.session_id:
            self.show_notification("No session active")
            return False
            
        try:
            response = requests.get(
                f"{self.api_url}/session/{self.session_id}/clipboard/latest",
                headers=self.headers,
                params={"hostname": self.hostname},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["content"]
                pyperclip.copy(content)
                from_host = data.get("hostname", "unknown")
                self.show_notification(f"✓ Got {len(content)} chars from {from_host}")
                return True
            elif response.status_code == 404:
                self.show_notification("No clipboard items in session")
                return False
            else:
                self.show_notification(f"✗ Get failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.show_notification(f"✗ Get error: {str(e)[:30]}")
            return False
    
    def end_session(self, icon=None, item=None):
        """End current session and clear cloud data"""
        if not self.session_id:
            self.show_notification("No active session")
            return
            
        try:
            response = requests.delete(
                f"{self.api_url}/session/{self.session_id}/end",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                self.show_notification(f"✓ Session {self.session_id} ended")
                print(f"Session {self.session_id} ended")
                self.session_id = None
                self.save_config()
                if self.icon:
                    self.icon.menu = self.create_menu()
            else:
                self.show_notification(f"✗ End session failed: {response.status_code}")
                
        except Exception as e:
            self.show_notification(f"✗ End session error: {str(e)[:30]}")
    
    def show_notification(self, message):
        """Update the icon tooltip with status message"""
        self.last_status = message
        if self.icon:
            session_info = f"Session: {self.session_id}" if self.session_id else "No Session"
            self.icon.title = f"Cloud Clipboard - {session_info} - {message}"
    
    def create_menu(self):
        """Create the system tray menu"""
        menu_items = []
        
        if self.session_id:
            menu_items.extend([
                pystray.MenuItem(f"Session: {self.session_id}", None, enabled=False),
                pystray.MenuItem(f"Host: {self.hostname}", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Send Clipboard", self.send_clipboard),
                pystray.MenuItem("Get Clipboard", self.get_clipboard),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("End Session", self.end_session),
            ])
        else:
            menu_items.extend([
                pystray.MenuItem("No Active Session", None, enabled=False),
                pystray.Menu.SEPARATOR,
            ])
        
        menu_items.extend([
            pystray.MenuItem("Start New Session", self.start_session),
            pystray.MenuItem("Join Session", self.join_session),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"Status: {self.last_status}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app)
        ])
        
        return pystray.Menu(*menu_items)
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        print("Shutting down Cloud Clipboard...")
        if self.icon:
            self.icon.stop()
        os._exit(0)  # Force exit to stop uvicorn server
    
    def run(self):
        """Start the system tray application"""
        print("Starting Cloud Clipboard tray...")
        print(f"Hostname: {self.hostname}")
        
        if self.session_id:
            print(f"Resuming session: {self.session_id}")
        else:
            print("No active session - use tray menu to start or join one")
            
        print("The app will run in the system tray.")
        
        # Create the icon
        image = self.create_icon_image()
        session_info = f"Session: {self.session_id}" if self.session_id else "No Session"
        self.icon = pystray.Icon(
            "cloud_clipboard",
            image,
            f"Cloud Clipboard - {session_info}",
            self.create_menu()
        )
        
        # Run the icon (this blocks until quit)
        self.icon.run()

def start_backend_server():
    """Start the FastAPI backend server in a separate thread"""
    print(f"Starting backend server on port {API_PORT}...")
    uvicorn.run(app, host="127.0.0.1", port=API_PORT, log_level="error")

def main():
    """Main entry point - start both backend and tray client"""
    print("=== Cloud Clipboard Starting ===")
    print(f"Admin dashboard: http://localhost:{API_PORT}/admin")
    
    # Start backend server in background thread
    backend_thread = threading.Thread(target=start_backend_server, daemon=True)
    backend_thread.start()
    
    # Give server time to start
    time.sleep(2)
    
    # Start tray client (this blocks until quit)
    tray_app = CloudClipboardTray()
    try:
        tray_app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()