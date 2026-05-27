from fastapi import FastAPI, HTTPException
import json
import os
import time  # 👑 FIX: Imported missing time module to prevent runtime crash
from app.services.gmail_listener import launch_listener_thread
import app.services.gmail_listener as listener
from app.models.document_models import DocumentExtractionOutput
# 👑 FIX: Route directly through your isolated service layer
from app.services.document_service import process_and_stage_document
from pydantic import BaseModel
import logging

## INPUT MODEL FOR AGENT 2 ENDPOINT
class DocumentInputPayload(BaseModel):
    raw_text: str

# Establish centralized file logging configurations
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    filename="logs/app.log",                 
    level=logging.INFO,                     
    format="%(asctime)s [%(levelname)s] %(message)s",  
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.info("FastAPI Server Gateway Initialization Started.")

app = FastAPI(title="Enterprise AI ERP Assistant Gateway")

LEDGER_PATH = "data/draft_ledger.json"
DOC_LEDGER_PATH = "data/document_ledger.json"

@app.on_event("startup")
def on_startup():
    launch_listener_thread()

@app.get("/agent-status")
def get_agent_status():
    return {"status": "active" if listener.is_agent_active else "inactive"}

@app.post("/agent-toggle")
def toggle_agent(action: dict):
    target_state = action.get("command", "").lower()
    if target_state == "start":
        listener.is_agent_active = True
        return {"message": "Agent activated."}
    elif target_state == "stop":
        listener.is_agent_active = False
        return {"message": "Agent deactivated."}

# =========================================================================
# AGENT 1 ROUTES — EMAIL INTENT CLASSIFICATION LEDGER
# =========================================================================

@app.get("/drafts")
def get_all_drafts():
    """Retrieves all documents currently saved in the staging ledger."""
    if not os.path.exists(LEDGER_PATH):
        return []
    with open(LEDGER_PATH, "r") as f:
        return json.load(f)

@app.post("/drafts/action")
def update_draft_status(payload: dict):
    """Updates a draft's status following a manual confirmation or rejection."""
    draft_id = payload.get("draft_id")
    new_status = payload.get("status") # e.g., "Approved & Committed" or "Rejected"
    
    if not os.path.exists(LEDGER_PATH):
        raise HTTPException(status_code=404, detail="Staging data file empty.")
        
    with open(LEDGER_PATH, "r") as f:
        drafts = json.load(f)
        
    updated = False
    for item in drafts:
        if item["draft_id"] == draft_id:
            item["status"] = new_status
            updated = True
            break
            
    if not updated:
        raise HTTPException(status_code=404, detail="Target draft item not found.")
        
    with open(LEDGER_PATH, "w") as f:
        json.dump(drafts, f, indent=2)
        
    return {"message": f"Draft state updated successfully to {new_status}."}

# =========================================================================
# AGENT 2 ROUTES — ATTACHMENT DOCUMENT DATA EXTRACTION LEDGER
# =========================================================================

@app.get("/document-drafts")
def get_all_document_drafts():
    """Retrieves all extracted document drafts currently saved in the staging ledger safely."""
    if not os.path.exists(DOC_LEDGER_PATH):
        return []
        
    try:
        if os.path.getsize(DOC_LEDGER_PATH) == 0:
            return []
            
        with open(DOC_LEDGER_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
            
    except json.JSONDecodeError:
        return []

@app.post("/extract-document")
def process_document_extraction(payload: DocumentInputPayload):
    """
    Accepts raw unstructured document text strings, routes them through the isolated
    service layer, and commits the structured evaluation into the staging ledger database.
    """
    try:
        # 1. Route the request through your isolated document service layer
        service_result = process_and_stage_document(payload.raw_text)
        
        if service_result["status"] == "error":
            raise HTTPException(status_code=400, detail=service_result["message"])
            
        # Extract the verified core dictionary data object
        extracted_data_block = service_result["data"]
        
        # 2. Ensure staging data storage file directory exists
        os.makedirs(os.path.dirname(DOC_LEDGER_PATH), exist_ok=True)
        
        # 3. Load up existing data logs
        drafts = []
        if os.path.exists(DOC_LEDGER_PATH) and os.path.getsize(DOC_LEDGER_PATH) > 0:
            with open(DOC_LEDGER_PATH, "r", encoding="utf-8") as f:
                try:
                    drafts = json.load(f)
                except:
                    drafts = []
                    
        # 4. Generate an incremental index ID tracker
        next_id = max([d.get("doc_id", 0) for d in drafts]) + 1 if drafts else 1
        
        # 5. Package the record into the database schema ledger frame
        draft_record = {
            "doc_id": next_id,
            "status": "Pending Review",
            "raw_input_text": payload.raw_text,
            "extracted_data": extracted_data_block,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Append and write back to storage cache ledger file
        drafts.append(draft_record)
        with open(DOC_LEDGER_PATH, "w", encoding="utf-8") as f:
            json.dump(drafts, f, indent=2)
            
        return {
            "status": "success",
            "message": f"Document successfully parsed and staged under Draft ID #{next_id}",
            "draft_data": draft_record
        }
        
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logging.error(f"Global backend breakdown inside document parser router: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document agent extraction failure: {str(e)}")

@app.post("/document-drafts/action")
def update_document_draft_status(payload: dict):
    """Updates a document draft status following manual review validation processing updates."""
    doc_id = payload.get("doc_id")
    new_status = payload.get("status") # e.g., "Approved & Committed" or "Rejected"
    edited_data = payload.get("updated_data") # Contains any final human text modifications
    
    if not os.path.exists(DOC_LEDGER_PATH):
        raise HTTPException(status_code=404, detail="Staging data repository missing.")
        
    with open(DOC_LEDGER_PATH, "r", encoding="utf-8") as f:
        drafts = json.load(f)
        
    updated = False
    for item in drafts:
        if item["doc_id"] == doc_id:
            item["status"] = new_status
            if edited_data:
                item["extracted_data"] = edited_data
            updated = True
            break
            
    if not updated:
        raise HTTPException(status_code=404, detail="Target document reference ID not found.")
        
    with open(DOC_LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2)
        
    return {"message": f"Document Draft #{doc_id} updated successfully to status: {new_status}."}