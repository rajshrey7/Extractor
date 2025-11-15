"""
Mock MOSIP Server for Local Development
Simulates MOSIP APIs for testing without real credentials
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import random
import sqlite3
import json
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mock MOSIP Server",
    description="Simulates MOSIP APIs for local development",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLite database
def init_db():
    """Initialize SQLite database for storing mock data"""
    conn = sqlite3.connect('mock_mosip.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pre_registrations (
            pre_reg_id TEXT PRIMARY KEY,
            data TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            registration_id TEXT PRIMARY KEY,
            pre_reg_id TEXT,
            data TEXT,
            status TEXT,
            uin TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (pre_reg_id) REFERENCES pre_registrations (pre_reg_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS biometric_captures (
            capture_id TEXT PRIMARY KEY,
            type TEXT,
            data TEXT,
            quality_score REAL,
            device_id TEXT,
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            device_type TEXT,
            device_info TEXT,
            registered_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token TEXT PRIMARY KEY,
            client_id TEXT,
            expires_at TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()


class AuthRequest(BaseModel):
    """Authentication request model"""
    id: str
    version: str
    requesttime: str
    request: Dict[str, Any]


class PreRegRequest(BaseModel):
    """Pre-registration request model"""
    id: str
    version: str
    requesttime: str
    request: Dict[str, Any]


class RegistrationRequest(BaseModel):
    """Registration request model"""
    id: str
    version: str
    requesttime: str
    request: Dict[str, Any]


class BiometricRequest(BaseModel):
    """Biometric capture request model"""
    id: str
    version: str
    requesttime: str
    request: Dict[str, Any]


class DeviceRequest(BaseModel):
    """Device registration request model"""
    id: str
    version: str
    requesttime: str
    request: Dict[str, Any]


class SyncRequest(BaseModel):
    """Data sync request model"""
    id: str
    version: str
    requesttime: str
    request: Dict[str, Any]


def generate_id(prefix: str = "") -> str:
    """Generate unique ID"""
    unique_id = str(uuid.uuid4()).split('-')[0].upper()
    return f"{prefix}{unique_id}" if prefix else unique_id


def get_db_connection():
    """Get database connection"""
    return sqlite3.connect('mock_mosip.db')


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Mock MOSIP Server",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/v1/authmanager/authenticate")
async def authenticate(auth_req: AuthRequest):
    """Mock authentication endpoint"""
    logger.info(f"Authentication request from client: {auth_req.request.get('clientId')}")
    
    # Generate mock auth token
    token = f"mock-token-{generate_id()}"
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Store token in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO auth_tokens (token, client_id, expires_at, created_at)
        VALUES (?, ?, ?, ?)
    ''', (token, auth_req.request.get('clientId'), expires_at.isoformat(), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    
    return {
        "id": auth_req.id,
        "version": auth_req.version,
        "responsetime": datetime.utcnow().isoformat(),
        "response": {
            "token": token,
            "expiresIn": 3600,
            "refreshToken": f"refresh-{token}"
        },
        "errors": None
    }


@app.post("/preregistration/v1/applications")
async def create_pre_registration(pre_reg_req: PreRegRequest):
    """Mock pre-registration creation"""
    logger.info("Creating new pre-registration")
    
    # Generate pre-registration ID
    pre_reg_id = f"PRE{generate_id()}"
    
    # Store in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO pre_registrations (pre_reg_id, data, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        pre_reg_id,
        json.dumps(pre_reg_req.request),
        "PENDING",
        datetime.utcnow().isoformat(),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    
    return {
        "id": pre_reg_req.id,
        "version": pre_reg_req.version,
        "responsetime": datetime.utcnow().isoformat(),
        "response": {
            "preRegistrationId": pre_reg_id,
            "status": "PENDING",
            "createdDateTime": datetime.utcnow().isoformat(),
            "demographicDetails": pre_reg_req.request.get("demographicDetails", {})
        },
        "errors": None
    }


@app.put("/preregistration/v1/applications/{pre_reg_id}")
async def update_pre_registration(pre_reg_id: str, update_req: PreRegRequest):
    """Mock pre-registration update"""
    logger.info(f"Updating pre-registration: {pre_reg_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if pre-registration exists
    cursor.execute("SELECT * FROM pre_registrations WHERE pre_reg_id = ?", (pre_reg_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Pre-registration {pre_reg_id} not found")
    
    # Update pre-registration
    cursor.execute('''
        UPDATE pre_registrations
        SET data = ?, updated_at = ?
        WHERE pre_reg_id = ?
    ''', (json.dumps(update_req.request), datetime.utcnow().isoformat(), pre_reg_id))
    conn.commit()
    conn.close()
    
    return {
        "id": update_req.id,
        "version": update_req.version,
        "responsetime": datetime.utcnow().isoformat(),
        "response": {
            "preRegistrationId": pre_reg_id,
            "status": "UPDATED",
            "updatedDateTime": datetime.utcnow().isoformat()
        },
        "errors": None
    }


@app.get("/preregistration/v1/applications/{pre_reg_id}")
async def get_pre_registration(pre_reg_id: str):
    """Mock get pre-registration"""
    logger.info(f"Getting pre-registration: {pre_reg_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pre_registrations WHERE pre_reg_id = ?", (pre_reg_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Pre-registration {pre_reg_id} not found")
    
    data = json.loads(row[1]) if row[1] else {}
    
    return {
        "id": "mosip.pre-registration.get",
        "version": "1.0",
        "responsetime": datetime.utcnow().isoformat(),
        "response": {
            "preRegistrationId": pre_reg_id,
            "status": row[2],
            "demographicDetails": data.get("demographicDetails", {}),
            "createdDateTime": row[3],
            "updatedDateTime": row[4]
        },
        "errors": None
    }


@app.post("/registrationprocessor/v1/registrationtransaction")
async def create_registration(reg_req: RegistrationRequest):
    """Mock registration creation"""
    logger.info("Creating new registration")
    
    # Generate registration ID and UIN
    registration_id = reg_req.request.get("registrationId", f"REG{generate_id()}")
    uin = f"UIN{random.randint(100000000000, 999999999999)}"
    
    # Simulate processing delay
    status = random.choice(["IN_PROGRESS", "IN_PROGRESS", "IN_PROGRESS", "COMPLETED"])
    
    # Store in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO registrations (registration_id, pre_reg_id, data, status, uin, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        registration_id,
        reg_req.request.get("preRegistrationId"),
        json.dumps(reg_req.request),
        status,
        uin if status == "COMPLETED" else None,
        datetime.utcnow().isoformat(),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    
    response_data = {
        "registrationId": registration_id,
        "status": status,
        "submittedDateTime": datetime.utcnow().isoformat()
    }
    
    if status == "COMPLETED":
        response_data["uin"] = uin
        response_data["acknowledgement"] = f"ACK{generate_id()}"
    
    return {
        "id": reg_req.id,
        "version": reg_req.version,
        "responsetime": datetime.utcnow().isoformat(),
        "response": response_data,
        "errors": None
    }


@app.get("/registrationprocessor/v1/registrationstatus/{registration_id}")
async def get_registration_status(registration_id: str):
    """Mock registration status"""
    logger.info(f"Getting registration status: {registration_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE registration_id = ?", (registration_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        # Simulate processing - return IN_PROGRESS for unknown IDs
        return {
            "id": "mosip.registration.status",
            "version": "1.0",
            "responsetime": datetime.utcnow().isoformat(),
            "response": {
                "registrationId": registration_id,
                "registrationStatus": "IN_PROGRESS",
                "statusMessage": "Registration is being processed",
                "lastUpdatedTime": datetime.utcnow().isoformat()
            },
            "errors": None
        }
    
    # Simulate status progression
    current_status = row[3]
    if current_status == "IN_PROGRESS" and random.random() > 0.5:
        # 50% chance to complete
        new_status = "COMPLETED"
        uin = f"UIN{random.randint(100000000000, 999999999999)}"
        
        cursor.execute('''
            UPDATE registrations
            SET status = ?, uin = ?, updated_at = ?
            WHERE registration_id = ?
        ''', (new_status, uin, datetime.utcnow().isoformat(), registration_id))
        conn.commit()
        
        current_status = new_status
        row = cursor.execute("SELECT * FROM registrations WHERE registration_id = ?", (registration_id,)).fetchone()
    
    conn.close()
    
    response_data = {
        "registrationId": registration_id,
        "registrationStatus": row[3],
        "statusMessage": f"Registration is {row[3].lower()}",
        "lastUpdatedTime": row[6]
    }
    
    if row[3] == "COMPLETED" and row[4]:
        response_data["uin"] = row[4]
        response_data["acknowledgement"] = f"ACK{generate_id()}"
    
    return {
        "id": "mosip.registration.status",
        "version": "1.0",
        "responsetime": datetime.utcnow().isoformat(),
        "response": response_data,
        "errors": None
    }


@app.post("/bioapi/v1/capture")
async def capture_biometric(bio_req: BiometricRequest):
    """Mock biometric capture"""
    logger.info(f"Capturing biometric: {bio_req.request.get('type')}")
    
    # Generate capture ID
    capture_id = f"CAP{generate_id()}"
    
    # Store in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO biometric_captures (capture_id, type, data, quality_score, device_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        capture_id,
        bio_req.request.get("type"),
        bio_req.request.get("data", "")[:100],  # Store first 100 chars for mock
        bio_req.request.get("qualityScore", 0.0),
        bio_req.request.get("deviceId"),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    
    return {
        "id": bio_req.id,
        "version": bio_req.version,
        "responsetime": datetime.utcnow().isoformat(),
        "response": {
            "captureId": capture_id,
            "status": "SUCCESS",
            "qualityScore": bio_req.request.get("qualityScore", 0.0),
            "capturedDateTime": datetime.utcnow().isoformat()
        },
        "errors": None
    }


@app.post("/devicemanager/v1/devices/register")
async def register_device(device_req: DeviceRequest):
    """Mock device registration"""
    logger.info(f"Registering device: {device_req.request.get('deviceId')}")
    
    device_id = device_req.request.get("deviceId", f"DEV{generate_id()}")
    
    # Store in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO devices (device_id, device_type, device_info, registered_at)
        VALUES (?, ?, ?, ?)
    ''', (
        device_id,
        device_req.request.get("deviceType"),
        json.dumps(device_req.request.get("deviceInfo", {})),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    
    return {
        "id": device_req.id,
        "version": device_req.version,
        "responsetime": datetime.utcnow().isoformat(),
        "response": {
            "deviceId": device_id,
            "status": "REGISTERED",
            "registeredDateTime": datetime.utcnow().isoformat()
        },
        "errors": None
    }


@app.post("/sync/v1/registrations")
async def sync_registrations(sync_req: SyncRequest):
    """Mock registration sync"""
    logger.info("Syncing registration data")
    
    sync_id = f"SYNC{generate_id()}"
    
    return {
        "id": sync_req.id,
        "version": sync_req.version,
        "responsetime": datetime.utcnow().isoformat(),
        "response": {
            "syncId": sync_id,
            "status": "SYNCED",
            "syncedRecords": len(sync_req.request.get("records", [])),
            "syncedDateTime": datetime.utcnow().isoformat()
        },
        "errors": None
    }


@app.post("/registrationprocessor/v1/packetreceiver/registrationpackets")
async def upload_packet(request: Request):
    """Mock packet upload"""
    logger.info("Uploading registration packet")
    
    packet_id = f"PKT{generate_id()}"
    
    return {
        "id": "mosip.packet.upload",
        "version": "1.0",
        "responsetime": datetime.utcnow().isoformat(),
        "response": {
            "packetId": packet_id,
            "status": "UPLOADED",
            "uploadedDateTime": datetime.utcnow().isoformat()
        },
        "errors": None
    }


@app.get("/admin/reset")
async def reset_database():
    """Reset the mock database (for testing)"""
    logger.info("Resetting mock database")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear all tables
    cursor.execute("DELETE FROM pre_registrations")
    cursor.execute("DELETE FROM registrations")
    cursor.execute("DELETE FROM biometric_captures")
    cursor.execute("DELETE FROM devices")
    cursor.execute("DELETE FROM auth_tokens")
    
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "message": "Mock database reset successfully",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/admin/stats")
async def get_stats():
    """Get mock database statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {
        "pre_registrations": cursor.execute("SELECT COUNT(*) FROM pre_registrations").fetchone()[0],
        "registrations": cursor.execute("SELECT COUNT(*) FROM registrations").fetchone()[0],
        "completed_registrations": cursor.execute("SELECT COUNT(*) FROM registrations WHERE status = 'COMPLETED'").fetchone()[0],
        "biometric_captures": cursor.execute("SELECT COUNT(*) FROM biometric_captures").fetchone()[0],
        "devices": cursor.execute("SELECT COUNT(*) FROM devices").fetchone()[0],
        "active_tokens": cursor.execute(
            "SELECT COUNT(*) FROM auth_tokens WHERE expires_at > ?",
            (datetime.utcnow().isoformat(),)
        ).fetchone()[0]
    }
    
    conn.close()
    
    return {
        "statistics": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)