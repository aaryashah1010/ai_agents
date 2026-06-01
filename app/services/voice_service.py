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

# 👑 CORE ERP BUSINESS KEYWORDS & PEER GROUP CONTEXT INDEX
ERP_CORE_KEYWORDS = [
    "quote", "quotation", "sales", "purchase", "order", "bill", "invoice", 
    "lead", "prospect", "stock", "inventory", "warehouse", "item", "product", 
    "balance", "owe", "receivable", "account", "buy", "send", "create"
]

ERP_KNOWN_PARTIES = [
    "ishti", "patel", "pal", "kaneria", "namra", "sanandiya", 
    "jaimin", "hadvani", "rishank", "dudhat", "raj", "bhanderi", "abc", "matrix"
]

def process_and_stage_voice_command(raw_transcript_content: str) -> dict:
    """
    Independent wrapper service that orchestrates raw spoken transcript parsing,
    intercepts nonsensical text via local pre-LLM sanitation rules to save tokens,
    and manages local log captures.
    """
    voice_logger.info("Initializing Agent 3 Voice Command Ingestion Sequence.")
    
    # 1. Clean and check for completely empty inputs
    clean_text = raw_transcript_content.strip().lower()
    if not clean_text:
        voice_logger.warning("Empty voice transcript payload passed to parser.")
        return {"status": "error", "message": "Spoken text transcription content cannot be blank."}
        
    # =========================================================================
    # 👑 PRE-LLM LOCAL SANITATION GUARDRAILS (TOKEN SAVER ZONE)
    # =========================================================================
    words_list = clean_text.split()
    
    # Rule A: Length Check - Reject if the phrase is under 3 words long
    if len(words_list) < 3:
        voice_logger.warning(f"Pre-LLM Intercept: Input too short to carry business logic ('{raw_transcript_content}'). Dropped.")
        return {
            "status": "error", 
            "message": "⚠️ Command too vague or short. Please state a clear ERP action (e.g., 'Check stock for item x')."
        }
        
    # Rule B: Context Match Check - Ensure it contains an ERP keyword or known party name
    has_keyword = any(keyword in clean_text for keyword in ERP_CORE_KEYWORDS)
    has_party = any(party in clean_text for party in ERP_KNOWN_PARTIES)
    
    if not (has_keyword or has_party):
        voice_logger.warning(f"Pre-LLM Intercept: Random/Vague string sequence detected ('{raw_transcript_content}'). Dropped.")
        return {
            "status": "error",
            "message": "❌ Speech content rejected. No valid business intent, inventory items, or system entity names recognized."
        }
    
    # =========================================================================
    # 2. CORE PROCESSING ZONE (Only reached if the input passes sanitation)
    # =========================================================================
    try:
        voice_logger.info(f"Payload successfully passed local sanitation. Routing text to Gemini API.")
        
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