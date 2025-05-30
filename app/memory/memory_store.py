import json
import sqlite3
import fakeredis
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

class MemoryStore:
    """
    Shared memory store for all agents to read/write data.
    Uses fakeredis for in-memory storage and SQLite for persistent storage.
    """
    
    def __init__(self):
        # Initialize fakeredis for in-memory storage
        self.redis = fakeredis.FakeStrictRedis()
        
        # Initialize SQLite for persistent storage
        self.db_path = "memory.db"
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create requests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            timestamp TEXT,
            status TEXT,
            input_source TEXT,
            input_data TEXT,
            classification TEXT,
            processing_result TEXT,
            action_result TEXT,
            error TEXT
        )
        ''')
        
        # Create traces table for detailed agent traces
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            timestamp TEXT,
            agent TEXT,
            action TEXT,
            data TEXT,
            FOREIGN KEY (request_id) REFERENCES requests (request_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def initialize_request(self, request_id: str, timestamp: str):
        """Initialize a new request in memory and database"""
        # Initialize in Redis
        request_data = {
            "request_id": request_id,
            "timestamp": timestamp,
            "status": "initialized",
            "traces": []
        }
        self.redis.set(f"request:{request_id}", json.dumps(request_data))
        
        # Initialize in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO requests (request_id, timestamp, status) VALUES (?, ?, ?)",
            (request_id, timestamp, "initialized")
        )
        conn.commit()
        conn.close()
        
        return request_id
    
    def store_input_data(self, request_id: str, input_source: str, input_data: Any):
        """Store input data for a request"""
        # Update in Redis
        request_data = json.loads(self.redis.get(f"request:{request_id}"))
        request_data["input_source"] = input_source
        request_data["input_data"] = input_data
        request_data["status"] = "input_received"
        self.redis.set(f"request:{request_id}", json.dumps(request_data))
        
        # Update in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE requests SET input_source = ?, input_data = ?, status = ? WHERE request_id = ?",
            (input_source, json.dumps(input_data), "input_received", request_id)
        )
        conn.commit()
        conn.close()
        
        # Add trace
        self.add_trace(request_id, "system", "input_received", {
            "input_source": input_source,
            "timestamp": datetime.now().isoformat()
        })
    
    def store_classification(self, request_id: str, classification: Dict[str, Any]):
        """Store classification results for a request"""
        # Update in Redis
        request_data = json.loads(self.redis.get(f"request:{request_id}"))
        request_data["classification"] = classification
        request_data["status"] = "classified"
        self.redis.set(f"request:{request_id}", json.dumps(request_data))
        
        # Update in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE requests SET classification = ?, status = ? WHERE request_id = ?",
            (json.dumps(classification), "classified", request_id)
        )
        conn.commit()
        conn.close()
        
        # Add trace
        self.add_trace(request_id, "classifier_agent", "classification_completed", classification)
    
    def store_processing_result(self, request_id: str, agent: str, result: Dict[str, Any]):
        """Store processing results from an agent"""
        # Update in Redis
        request_data = json.loads(self.redis.get(f"request:{request_id}"))
        request_data["processing_result"] = result
        request_data["status"] = "processed"
        self.redis.set(f"request:{request_id}", json.dumps(request_data))
        
        # Update in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE requests SET processing_result = ?, status = ? WHERE request_id = ?",
            (json.dumps(result), "processed", request_id)
        )
        conn.commit()
        conn.close()
        
        # Add trace
        self.add_trace(request_id, agent, "processing_completed", result)
    
    def store_action_result(self, request_id: str, action_result: Dict[str, Any]):
        """Store action routing results"""
        # Update in Redis
        request_data = json.loads(self.redis.get(f"request:{request_id}"))
        request_data["action_result"] = action_result
        request_data["status"] = "action_completed"
        self.redis.set(f"request:{request_id}", json.dumps(request_data))
        
        # Update in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE requests SET action_result = ?, status = ? WHERE request_id = ?",
            (json.dumps(action_result), "action_completed", request_id)
        )
        conn.commit()
        conn.close()
        
        # Add trace
        self.add_trace(request_id, "action_router", "action_completed", action_result)
    
    def store_error(self, request_id: str, error: str):
        """Store error information for a request"""
        # Update in Redis
        request_data = json.loads(self.redis.get(f"request:{request_id}"))
        request_data["error"] = error
        request_data["status"] = "error"
        self.redis.set(f"request:{request_id}", json.dumps(request_data))
        
        # Update in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE requests SET error = ?, status = ? WHERE request_id = ?",
            (error, "error", request_id)
        )
        conn.commit()
        conn.close()
        
        # Add trace
        self.add_trace(request_id, "system", "error", {"error": error})
    
    def add_trace(self, request_id: str, agent: str, action: str, data: Dict[str, Any]):
        """Add a trace entry for a request"""
        timestamp = datetime.now().isoformat()
        
        # Add to Redis
        request_data = json.loads(self.redis.get(f"request:{request_id}"))
        if "traces" not in request_data:
            request_data["traces"] = []
        
        trace = {
            "timestamp": timestamp,
            "agent": agent,
            "action": action,
            "data": data
        }
        request_data["traces"].append(trace)
        self.redis.set(f"request:{request_id}", json.dumps(request_data))
        
        # Add to SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO traces (request_id, timestamp, agent, action, data) VALUES (?, ?, ?, ?, ?)",
            (request_id, timestamp, agent, action, json.dumps(data))
        )
        conn.commit()
        conn.close()
    
    def get_request_data(self, request_id: str) -> Dict[str, Any]:
        """Get all data for a request"""
        # Get from Redis for faster access
        request_data = self.redis.get(f"request:{request_id}")
        if request_data:
            return json.loads(request_data)
        
        # If not in Redis, get from SQLite
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get request data
        cursor.execute("SELECT * FROM requests WHERE request_id = ?", (request_id,))
        request_row = cursor.fetchone()
        if not request_row:
            return None
        
        request_data = dict(request_row)
        
        # Parse JSON fields
        for field in ["input_data", "classification", "processing_result", "action_result"]:
            if request_data[field]:
                request_data[field] = json.loads(request_data[field])
        
        # Get traces
        cursor.execute("SELECT * FROM traces WHERE request_id = ? ORDER BY timestamp", (request_id,))
        traces = []
        for trace_row in cursor.fetchall():
            trace = dict(trace_row)
            trace["data"] = json.loads(trace["data"])
            traces.append(trace)
        
        request_data["traces"] = traces
        conn.close()
        
        # Cache in Redis for future access
        self.redis.set(f"request:{request_id}", json.dumps(request_data))
        
        return request_data
    
    def get_all_requests(self) -> List[Dict[str, Any]]:
        """Get summary of all requests"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT request_id, timestamp, status FROM requests ORDER BY timestamp DESC")
        requests = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return requests
