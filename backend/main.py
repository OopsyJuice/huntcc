from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import os

app = FastAPI(title="Cloud Clipboard API", version="1.0.0")
security = HTTPBearer()

# Simple API key authentication
API_KEY = os.getenv("API_KEY", "your-secret-api-key-change-this")

# In-memory storage (will be replaced with database later)
clipboard_storage = []

class ClipboardItem(BaseModel):
    content: str
    timestamp: datetime = None
    id: Optional[str] = None

class ClipboardResponse(BaseModel):
    id: str
    content: str
    timestamp: datetime

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

@app.get("/")
async def root():
    return {"message": "Cloud Clipboard API is running"}

@app.post("/clipboard", response_model=ClipboardResponse)
async def add_clipboard_item(
    item: ClipboardItem, 
    api_key: str = Depends(verify_api_key)
):
    # Generate simple ID and timestamp
    item_id = f"clip_{len(clipboard_storage) + 1}"
    timestamp = datetime.now()
    
    clipboard_entry = {
        "id": item_id,
        "content": item.content,
        "timestamp": timestamp
    }
    
    clipboard_storage.append(clipboard_entry)
    
    # Keep only last 10 items
    if len(clipboard_storage) > 10:
        clipboard_storage.pop(0)
    
    return ClipboardResponse(**clipboard_entry)

@app.get("/clipboard/latest", response_model=ClipboardResponse)
async def get_latest_clipboard(api_key: str = Depends(verify_api_key)):
    if not clipboard_storage:
        raise HTTPException(status_code=404, detail="No clipboard items found")
    
    latest_item = clipboard_storage[-1]
    return ClipboardResponse(**latest_item)

@app.get("/clipboard/history", response_model=List[ClipboardResponse])
async def get_clipboard_history(api_key: str = Depends(verify_api_key)):
    if not clipboard_storage:
        return []
    
    return [ClipboardResponse(**item) for item in clipboard_storage]

@app.delete("/clipboard/clear")
async def clear_clipboard_history(api_key: str = Depends(verify_api_key)):
    clipboard_storage.clear()
    return {"message": "Clipboard history cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)