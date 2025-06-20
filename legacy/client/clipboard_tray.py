import pystray
import pyperclip
import requests
import keyboard
import threading
import sys
import os
import json
import socket
from PIL import Image, ImageDraw
from datetime import datetime
import time

class CloudClipboardTray:
    def __init__(self, api_url="http://localhost:8000", api_key="your-secret-api-key-change-this"):
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.icon = None
        self.last_status = "Ready"
        self.session_id = None
        self.hostname = socket.gethostname()
        self.config_file = "clipboard_config.json"
        
        # Load saved session ID if exists
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
                # Update menu
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
                # Test if session exists by trying to get its status
                response = requests.get(
                    f"{self.api_url}/session/{session_code}/status",
                    headers=self.headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    self.session_id = session_code
                    self.save_config()
                    self.show_notification(f"✓ Joined session {self.session_id}")
                    print(f"Successfully joined session: {self.session_id}")
                    # Update menu
                    if self.icon:
                        self.icon.menu = self.create_menu()
                else:
                    print("Session not found or expired")
                    self.show_notification("Session not found")
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
        """Load paperclip icon from file"""
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, '..', 'assets', 'paper-clip.png')
            
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
                # Update menu
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
    
    def setup_hotkeys(self):
        """Setup global hotkeys"""
        try:
            # Cmd+Shift+C to send clipboard (Ctrl+Shift+C on Windows/Linux)
            keyboard.add_hotkey('cmd+shift+c', self.send_clipboard)
            # Cmd+Shift+V to get clipboard (Ctrl+Shift+V on Windows/Linux)  
            keyboard.add_hotkey('cmd+shift+v', self.get_clipboard)
            print("Hotkeys registered:")
            print("  Cmd+Shift+C: Send clipboard to cloud")
            print("  Cmd+Shift+V: Get clipboard from cloud")
        except Exception as e:
            print(f"Warning: Could not register hotkeys: {e}")
            print("You can still use the system tray menu")
    
    def create_menu(self):
        """Create the system tray menu"""
        menu_items = []
        
        # Session info and controls
        if self.session_id:
            menu_items.extend([
                pystray.MenuItem(f"Session: {self.session_id}", None, enabled=False),
                pystray.MenuItem(f"Host: {self.hostname}", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Send Clipboard", self.send_clipboard),
                pystray.MenuItem("Get Clipboard", self.get_clipboard),
                pystray.MenuItem("Show History", self.show_history),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("End Session", self.end_session),
            ])
        else:
            menu_items.extend([
                pystray.MenuItem("No Active Session", None, enabled=False),
                pystray.Menu.SEPARATOR,
            ])
        
        # Session management (always available)
        menu_items.extend([
            pystray.MenuItem("Start New Session", self.start_session),
            pystray.MenuItem("Join Session", self.join_session),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"Status: {self.last_status}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app)
        ])
        
        return pystray.Menu(*menu_items)
    
    def show_history(self, icon=None, item=None):
        """Show clipboard history in console"""
        if not self.session_id:
            print("No session active")
            return
            
        try:
            response = requests.get(
                f"{self.api_url}/session/{self.session_id}/clipboard/history",
                headers=self.headers,
                params={"hostname": self.hostname},
                timeout=5
            )
            
            if response.status_code == 200:
                items = response.json()
                if not items:
                    print(f"No clipboard history found in session {self.session_id}")
                    return
                
                print(f"\nSession {self.session_id} History ({len(items)} items):")
                print("-" * 60)
                for item in reversed(items):
                    timestamp = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                    content_preview = item["content"][:40] + "..." if len(item["content"]) > 40 else item["content"]
                    hostname = item.get("hostname", "unknown")
                    print(f"{timestamp.strftime('%H:%M:%S')} [{hostname}]: {content_preview}")
                print()
                    
        except Exception as e:
            print(f"Error getting history: {e}")
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        print("Shutting down Cloud Clipboard...")
        if self.icon:
            self.icon.stop()
    
    def run(self):
        """Start the system tray application"""
        print("Starting Cloud Clipboard...")
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
        
        # Setup hotkeys in a separate thread
        hotkey_thread = threading.Thread(target=self.setup_hotkeys, daemon=True)
        hotkey_thread.start()
        
        # Run the icon (this blocks until quit)
        self.icon.run()

def main():
    app = CloudClipboardTray()
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()