from fastapi import FastAPI, HTTPException
import json
import os
from app.services.gmail_listener import launch_listener_thread
import app.services.gmail_listener as listener

app = FastAPI(title="Enterprise AI ERP Assistant Gateway")

LEDGER_PATH = "data/draft_ledger.json"

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

# --- NEW HUMAN IN THE LOOP LEDGER ROUTE PANELS ---

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