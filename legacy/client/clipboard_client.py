import requests
import pyperclip
import json
import sys
from datetime import datetime

class CloudClipboard:
    def __init__(self, api_url="http://localhost:8000", api_key="your-secret-api-key-change-this"):
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def send_clipboard(self):
        """Send current clipboard content to cloud"""
        try:
            # Get current clipboard content
            content = pyperclip.paste()
            if not content.strip():
                print("Clipboard is empty")
                return False
            
            # Send to API
            response = requests.post(
                f"{self.api_url}/clipboard",
                headers=self.headers,
                json={"content": content}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Sent to cloud: {len(content)} characters")
                return True
            else:
                print(f"✗ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error sending clipboard: {e}")
            return False
    
    def get_clipboard(self):
        """Get latest clipboard content from cloud"""
        try:
            response = requests.get(
                f"{self.api_url}/clipboard/latest",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["content"]
                
                # Set local clipboard
                pyperclip.copy(content)
                print(f"✓ Retrieved from cloud: {len(content)} characters")
                print(f"Content: {content[:50]}{'...' if len(content) > 50 else ''}")
                return True
            elif response.status_code == 404:
                print("No clipboard items found in cloud")
                return False
            else:
                print(f"✗ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error getting clipboard: {e}")
            return False
    
    def show_history(self):
        """Show clipboard history"""
        try:
            response = requests.get(
                f"{self.api_url}/clipboard/history",
                headers=self.headers
            )
            
            if response.status_code == 200:
                items = response.json()
                if not items:
                    print("No clipboard history found")
                    return
                
                print(f"\nClipboard History ({len(items)} items):")
                print("-" * 50)
                for item in reversed(items):  # Show newest first
                    timestamp = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                    content_preview = item["content"][:40] + "..." if len(item["content"]) > 40 else item["content"]
                    print(f"{timestamp.strftime('%H:%M:%S')}: {content_preview}")
                    
            else:
                print(f"✗ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"✗ Error getting history: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python clipboard_client.py send    # Send current clipboard to cloud")
        print("  python clipboard_client.py get     # Get latest from cloud")
        print("  python clipboard_client.py history # Show clipboard history")
        return
    
    clipboard = CloudClipboard()
    command = sys.argv[1].lower()
    
    if command == "send":
        clipboard.send_clipboard()
    elif command == "get":
        clipboard.get_clipboard()
    elif command == "history":
        clipboard.show_history()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()