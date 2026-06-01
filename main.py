from fastapi import FastAPI, HTTPException
import json
import os
import time  
from app.services.gmail_listener import launch_listener_thread
import app.services.gmail_listener as listener
from app.models.document_models import DocumentExtractionOutput
from app.services.document_service import process_and_stage_document
from pydantic import BaseModel
import logging
from app.services.voice_service import process_and_stage_voice_command

class DocumentInputPayload(BaseModel):
    raw_text: str

class VoiceInputPayload(BaseModel):
    transcript: str

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
VOICE_LEDGER_PATH = "data/voice_ledger.json"

## AGENT CONTROL ROUTES — START/STOP AND STATUS CHECKS

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


# AGENT 1 ROUTES — EMAIL INTENT CLASSIFICATION LEDGER

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

# AGENT 2 ROUTES — ATTACHMENT DOCUMENT DATA EXTRACTION LEDGER

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
        service_result = process_and_stage_document(payload.raw_text)
        
        if service_result["status"] == "error":
            raise HTTPException(status_code=400, detail=service_result["message"])
            
        extracted_data_block = service_result["data"]
        
        os.makedirs(os.path.dirname(DOC_LEDGER_PATH), exist_ok=True)
        
        drafts = []
        if os.path.exists(DOC_LEDGER_PATH) and os.path.getsize(DOC_LEDGER_PATH) > 0:
            with open(DOC_LEDGER_PATH, "r", encoding="utf-8") as f:
                try:
                    drafts = json.load(f)
                except:
                    drafts = []
                    
        next_id = max([d.get("doc_id", 0) for d in drafts]) + 1 if drafts else 1
        
        draft_record = {
            "doc_id": next_id,
            "status": "Pending Review",
            "raw_input_text": payload.raw_text,
            "extracted_data": extracted_data_block,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
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



## AGENT 3 ROUTES — VOICE COMMAND INTENT CLASSIFICATION LEDGER

@app.get("/voice-drafts")
def get_all_voice_drafts():
    """Retrieves all parsed voice instructions currently sitting in the verification ledger safely."""
    if not os.path.exists(VOICE_LEDGER_PATH):
        return []
    try:
        if os.path.getsize(VOICE_LEDGER_PATH) == 0:
            return []
        with open(VOICE_LEDGER_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

@app.post("/process-voice-action")
def process_voice_action_endpoint(payload: VoiceInputPayload):
    """
    Accepts text transcripts of user verbal commands, maps intents via Gemini, 
    and packages structured actions directly into the local verification staging ledger.
    """
    try:
        service_result = process_and_stage_voice_command(payload.transcript)
        
        if service_result["status"] == "error":
            raise HTTPException(status_code=400, detail=service_result["message"])
            
        extracted_voice_block = service_result["data"]
        
        os.makedirs(os.path.dirname(VOICE_LEDGER_PATH), exist_ok=True)
        
        voice_records = []
        if os.path.exists(VOICE_LEDGER_PATH) and os.path.getsize(VOICE_LEDGER_PATH) > 0:
            with open(VOICE_LEDGER_PATH, "r", encoding="utf-8") as f:
                try: voice_records = json.load(f)
                except: voice_records = []
                    
        next_voice_id = max([v.get("voice_id", 0) for v in voice_records]) + 1 if voice_records else 1
        
        staged_record = {
            "voice_id": next_voice_id,
            "status": "Pending Review",
            "raw_transcript_text": payload.transcript,
            "extracted_action_data": extracted_voice_block,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        voice_records.append(staged_record)
        with open(VOICE_LEDGER_PATH, "w", encoding="utf-8") as f:
            json.dump(voice_records, f, indent=2)
            
        return {
            "status": "success",
            "message": f"Speech intent processed and staged under Verification ID #{next_voice_id}",
            "voice_data": staged_record
        }
        
    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        logging.error(f"Global background error tracked within Agent 3 routing controller layer: {str(err)}")
        raise HTTPException(status_code=500, detail=f"Voice-to-ERP execution failure: {str(err)}")

@app.post("/voice-drafts/action")
def update_voice_action_ledger_status(payload: dict):
    """Updates status tracking keys for voice items following explicit dashboard reviewer input confirmation."""
    voice_id = payload.get("voice_id")
    new_status = payload.get("status") # e.g., "Approved & Committed" or "Rejected"
    edited_data = payload.get("updated_data")
    
    if not os.path.exists(VOICE_LEDGER_PATH):
        raise HTTPException(status_code=404, detail="Voice storage staging database not found.")
        
    with open(VOICE_LEDGER_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
        
    updated = False
    for item in records:
        if item["voice_id"] == voice_id:
            item["status"] = new_status
            if edited_data:
                item["extracted_action_data"] = edited_data
            updated = True
            break
            
    if not updated:
        raise HTTPException(status_code=404, detail="Target voice voucher reference index not found.")
        
    with open(VOICE_LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
        
    return {"message": f"Voice Action Voucher #{voice_id} updated successfully to status: {new_status}."}