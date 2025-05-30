from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import os
import uuid
from datetime import datetime
import json

from app.agents.classifier_agent import ClassifierAgent
from app.agents.email_agent import EmailAgent
from app.agents.json_agent import JSONAgent
from app.agents.pdf_agent import PDFAgent
from app.memory.memory_store import MemoryStore
from app.router.action_router import ActionRouter
from app.utils.file_utils import save_upload_file, get_file_content, get_file_extension

# Initialize FastAPI app
app = FastAPI(
    title="FlowbitAI Multi-Agent System",
    description="A multi-agent system that processes inputs from Email, JSON, and PDF, classifies format and business intent, and routes to specialized agents.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
memory_store = MemoryStore()
classifier_agent = ClassifierAgent(memory_store)
email_agent = EmailAgent(memory_store)
json_agent = JSONAgent(memory_store)
pdf_agent = PDFAgent(memory_store)
action_router = ActionRouter(memory_store)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Welcome to FlowbitAI Multi-Agent System"}

@app.post("/process")
async def process_input(
    file: UploadFile = File(None),
    json_data: str = Form(None),
    email_data: str = Form(None)
):
    """
    Process input data from various formats (file upload, JSON data, or email data)
    """
    request_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Initialize request in memory store
    memory_store.initialize_request(request_id, timestamp)
    
    try:
        # Determine input source and extract content
        if file:
            file_path = save_upload_file(file, "uploads")
            file_extension = get_file_extension(file.filename)
            content = get_file_content(file_path, file_extension)
            input_source = "file"
        elif json_data:
            content = json.loads(json_data)
            input_source = "json"
        elif email_data:
            content = email_data
            input_source = "email"
        else:
            raise HTTPException(status_code=400, detail="No input provided")
        
        # Store input data in memory - convert bytes to string representation if needed
        if isinstance(content, bytes):
            # For binary content like PDFs, store a reference instead of the raw content
            file_path = f"uploads/{request_id}.pdf" if file_extension == "pdf" else f"uploads/{request_id}.bin"
            with open(file_path, "wb") as f:
                f.write(content)
            # Store the file path instead of the binary content
            memory_store.store_input_data(request_id, input_source, {"file_path": file_path})  
        else:
            memory_store.store_input_data(request_id, input_source, content)
        
        # Classify input
        classification = classifier_agent.classify(request_id, content, input_source)
        
        # Process with appropriate agent based on classification
        if classification["format"] == "EMAIL":
            result = email_agent.process(request_id, content)
        elif classification["format"] == "JSON":
            result = json_agent.process(request_id, content)
        elif classification["format"] == "PDF":
            result = pdf_agent.process(request_id, content)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {classification['format']}")
        
        # Route to appropriate action based on processing results
        action_result = action_router.route_action(request_id, classification, result)
        
        # Get full processing trace from memory
        processing_trace = memory_store.get_request_data(request_id)
        
        return JSONResponse(content={
            "request_id": request_id,
            "classification": classification,
            "processing_result": result,
            "action_result": action_result,
            "processing_trace": processing_trace
        })
        
    except Exception as e:
        # Log error in memory store
        memory_store.store_error(request_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{request_id}")
async def get_status(request_id: str):
    """
    Get the status and results of a processed request
    """
    try:
        data = memory_store.get_request_data(request_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Request ID {request_id} not found")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simulated external API endpoints
@app.post("/crm/tickets")
async def create_crm_ticket(ticket_data: dict):
    """
    Simulated CRM ticket creation endpoint
    """
    ticket_id = str(uuid.uuid4())
    return {"ticket_id": ticket_id, "status": "created", "data": ticket_data}

@app.post("/risk/alerts")
async def create_risk_alert(alert_data: dict):
    """
    Simulated risk alert creation endpoint
    """
    alert_id = str(uuid.uuid4())
    return {"alert_id": alert_id, "status": "created", "data": alert_data}

@app.post("/compliance/logs")
async def log_compliance_issue(compliance_data: dict):
    """
    Simulated compliance logging endpoint
    """
    log_id = str(uuid.uuid4())
    return {"log_id": log_id, "status": "logged", "data": compliance_data}

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
