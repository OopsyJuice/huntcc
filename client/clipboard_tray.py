import pystray
import pyperclip
import requests
import keyboard
import threading
import sys
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
        
    def create_icon_image(self):
        """Create a paperclip icon"""
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a paperclip shape
        # Main curve (outer)
        draw.arc([15, 10, 45, 40], 180, 360, fill=(70, 130, 180, 255), width=4)
        # Inner curve  
        draw.arc([20, 15, 40, 35], 180, 360, fill=(70, 130, 180, 255), width=3)
        # Straight parts
        draw.line([30, 40, 30, 55], fill=(70, 130, 180, 255), width=4)
        draw.line([15, 25, 15, 45], fill=(70, 130, 180, 255), width=4)
        # Bottom curve
        draw.arc([15, 40, 35, 60], 90, 180, fill=(70, 130, 180, 255), width=4)
        
        # Add a small highlight for 3D effect
        draw.arc([17, 12, 43, 38], 200, 340, fill=(135, 185, 230, 255), width=2)
        
        return image
    
    def send_clipboard(self):
        """Send current clipboard content to cloud"""
        try:
            content = pyperclip.paste()
            if not content.strip():
                self.show_notification("Clipboard is empty")
                return False
            
            response = requests.post(
                f"{self.api_url}/clipboard",
                headers=self.headers,
                json={"content": content},
                timeout=5
            )
            
            if response.status_code == 200:
                self.show_notification(f"✓ Sent {len(content)} chars to cloud")
                return True
            else:
                self.show_notification(f"✗ Send failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.show_notification(f"✗ Send error: {str(e)[:30]}")
            return False
    
    def get_clipboard(self):
        """Get latest clipboard content from cloud"""
        try:
            response = requests.get(
                f"{self.api_url}/clipboard/latest",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["content"]
                pyperclip.copy(content)
                self.show_notification(f"✓ Got {len(content)} chars from cloud")
                return True
            elif response.status_code == 404:
                self.show_notification("No clipboard items in cloud")
                return False
            else:
                self.show_notification(f"✗ Get failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.show_notification(f"✗ Get error: {str(e)[:30]}")
            return False
    
    def show_notification(self, message):
        """Update the icon tooltip with status message"""
        self.last_status = message
        if self.icon:
            # Update the menu to show latest status
            self.icon.title = f"Cloud Clipboard - {message}"
    
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
        return pystray.Menu(
            pystray.MenuItem("Send Clipboard", self.send_clipboard),
            pystray.MenuItem("Get Clipboard", self.get_clipboard),
            pystray.MenuItem("Show History", self.show_history),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"Status: {self.last_status}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app)
        )
    
    def show_history(self, icon=None, item=None):
        """Show clipboard history in console"""
        try:
            response = requests.get(
                f"{self.api_url}/clipboard/history",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                items = response.json()
                if not items:
                    print("No clipboard history found")
                    return
                
                print(f"\nClipboard History ({len(items)} items):")
                print("-" * 50)
                for item in reversed(items):
                    timestamp = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                    content_preview = item["content"][:40] + "..." if len(item["content"]) > 40 else item["content"]
                    print(f"{timestamp.strftime('%H:%M:%S')}: {content_preview}")
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
        print("The app will run in the system tray.")
        
        # Create the icon
        image = self.create_icon_image()
        self.icon = pystray.Icon(
            "cloud_clipboard",
            image,
            "Cloud Clipboard - Ready",
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