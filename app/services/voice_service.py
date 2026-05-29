import os
import logging
from app.models.voice_models import VoiceActionOutput
from app.agents.voice_agent import extract_voice_action_data

# Ensure tracking folders are ready
if not os.path.exists("logs"):
    os.makedirs("logs")

# Configure a clean, separate logger interface for Agent 3
voice_logger = logging.getLogger("voice_agent_logger")
if not voice_logger.handlers:
    file_handler = logging.FileHandler("logs/voice_processing.log")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    voice_logger.addHandler(file_handler)
    voice_logger.setLevel(logging.INFO)

def process_and_stage_voice_command(raw_transcript_content: str) -> dict:
    """
    Independent wrapper service that orchestrates raw spoken transcript parsing,
    runs semantic intent classification, and manages local log captures.
    """
    voice_logger.info("Initializing Agent 3 Voice Command Parsing Sequence.")
    
    if not raw_transcript_content.strip():
        voice_logger.warning("Empty voice transcript payload passed to parser.")
        return {"status": "error", "message": "Spoken text transcription content cannot be blank."}
        
    try:
        # Execute extraction agent workflow
        extracted_payload: VoiceActionOutput = extract_voice_action_data(raw_transcript_content)
        
        voice_logger.info(
            f"Successfully executed Agent 3 parsing. Mapped Intent: {extracted_payload.intent} | "
            f"Confidence: {extracted_payload.confidence}%"
        )
        
        return {
            "status": "success",
            "data": extracted_payload.dict()
        }
        
    except Exception as service_err:
        voice_logger.error(f"Critical execution error in Voice Action Service Layer: {str(service_err)}")
        return {
            "status": "error",
            "message": f"Voice execution subsystem error: {str(service_err)}"
        }