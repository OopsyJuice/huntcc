from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import os
import socket
import random

app = FastAPI(title="Cloud Clipboard API", version="2.0.0")

# CORS middleware - MUST be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Simple API key authentication
API_KEY = os.getenv("API_KEY", "your-secret-api-key-change-this")

# Session-based storage: {session_id: {items: [], created_at: timestamp, last_activity: timestamp, hostnames: []}}
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
    
    # Update activity timestamp
    session_storage[session_id]["last_activity"] = datetime.now()
    
    # Add hostname if provided and not already tracked
    if hostname and hostname not in session_storage[session_id]["hostnames"]:
        session_storage[session_id]["hostnames"].append(hostname)
    
    return session_storage[session_id]

def generate_session_code():
    """Generate a unique 6-digit session code"""
    while True:
        code = str(random.randint(100000, 999999))
        if code not in session_storage:
            return code

@app.post("/session/start")
async def start_session(api_key: str = Depends(verify_api_key)):
    """Generate new 6-digit session code"""
    cleanup_expired_sessions()
    
    session_id = generate_session_code()
    session_storage[session_id] = {
        "items": [],
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
        "hostnames": []
    }
    
    return {"session_id": session_id}

@app.get("/")
async def root():
    return {"message": "Cloud Clipboard API v2.0 is running"}

@app.post("/session/{session_id}/clipboard", response_model=ClipboardResponse)
async def add_clipboard_item(
    session_id: str,
    item: ClipboardItem, 
    api_key: str = Depends(verify_api_key)
):
    session_data = get_or_create_session(session_id, item.hostname)
    
    # Generate simple ID and timestamp
    item_id = f"clip_{session_id}_{len(session_data['items']) + 1}"
    timestamp = datetime.now()
    
    clipboard_entry = {
        "id": item_id,
        "content": item.content,
        "timestamp": timestamp,
        "hostname": item.hostname or "unknown"
    }
    
    session_data["items"].append(clipboard_entry)
    
    # Keep only last 10 items per session
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
    
    if not session_data["items"]:
        return []
    
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

@app.get("/session/{session_id}/status", response_model=SessionStatus)
async def get_session_status(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    cleanup_expired_sessions()
    
    if session_id not in session_storage:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = session_storage[session_id]
    return SessionStatus(
        session_id=session_id,
        created_at=session_data["created_at"],
        last_activity=session_data["last_activity"],
        hostnames=session_data["hostnames"],
        item_count=len(session_data["items"])
    )

@app.get("/sessions/active", response_model=List[SessionStatus])
async def get_active_sessions(api_key: str = Depends(verify_api_key)):
    """Admin endpoint to list all active sessions"""
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

@app.delete("/sessions/clear")
async def clear_all_sessions(api_key: str = Depends(verify_api_key)):
    """Admin endpoint to clear all sessions"""
    session_count = len(session_storage)
    session_storage.clear()
    return {"message": f"Cleared {session_count} sessions"}

# Legacy endpoints for backward compatibility
@app.post("/clipboard", response_model=ClipboardResponse)
async def add_clipboard_item_legacy(
    item: ClipboardItem, 
    api_key: str = Depends(verify_api_key)
):
    """Legacy endpoint - uses default session"""
    return await add_clipboard_item("default", item, api_key)

@app.get("/clipboard/latest", response_model=ClipboardResponse)
async def get_latest_clipboard_legacy(api_key: str = Depends(verify_api_key)):
    """Legacy endpoint - uses default session"""
    return await get_latest_clipboard("default", None, api_key)

@app.get("/clipboard/history", response_model=List[ClipboardResponse])
async def get_clipboard_history_legacy(api_key: str = Depends(verify_api_key)):
    """Legacy endpoint - uses default session"""
    return await get_clipboard_history("default", None, api_key)

@app.delete("/clipboard/clear")
async def clear_clipboard_history_legacy(api_key: str = Depends(verify_api_key)):
    """Legacy endpoint - uses default session"""
    return await end_session("default", api_key)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)