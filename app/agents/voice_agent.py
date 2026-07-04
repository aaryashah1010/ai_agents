import os
import json
import re
import logging
from app.services.gemini_service import call_gemini_api
from app.models.voice_models import VoiceActionOutput

PROMPT_FILE_PATH = "app/prompts/voice_prompts.txt"

def extract_voice_action_data(raw_transcript: str) -> VoiceActionOutput:
    """
    Reads the system instruction blueprint layout, injects the user's spoken 
    transcript string, dispatches it to Gemini, and enforces validation boundaries.
    """
    if not os.path.exists(PROMPT_FILE_PATH):
        raise FileNotFoundError(f"Missing mandatory instruction prompt template file at: {PROMPT_FILE_PATH}")
        
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
        prompt_template = f.read()
        
    final_prompt = prompt_template.replace("{voice_transcript}", raw_transcript)
    
    raw_response = call_gemini_api(final_prompt)
    
    cleaned_response = raw_response.strip().replace("```json", "").replace("```", "").strip()
    
    try:
        json_data = json.loads(cleaned_response)
        return VoiceActionOutput(**json_data)
        
    except Exception as parse_error:
        logging.info(f"[AGENT 3 RECOVERY] Direct JSON parsing failed. Invoking Regex recovery engine: {parse_error}")
        
        # --- FALLBACK ZONE ---
        # If the output got cut off or corrupted, rescue whatever structural attributes survived
        recovered_data = {
            "intent": "Unknown",
            "confidence": 30,
            "suggestedERPAction": "Open General Dashboard View",
            "missingFields": ["JSON Transcript Parse Failure Recovery Active"],
            "warnings": [f"Spoken text structural anomaly caught during execution processing: {str(parse_error)}"],
            "confirmationRequired": True,
            "items": []
        }
        
        intent_match = re.search(r'"intent"\s*:\s*"([^"]+)"', cleaned_response)
        if intent_match:
            recovered_data["intent"] = intent_match.group(1)
         
        customer_match = re.search(r'"customerName"\s*:\s*"([^"]+)"', cleaned_response)
        if customer_match:
            recovered_data["customerName"] = customer_match.group(1)
            
        vendor_match = re.search(r'"vendorName"\s*:\s*"([^"]+)"', cleaned_response)
        if vendor_match:
            recovered_data["vendorName"] = vendor_match.group(1)
            
        contact_match = re.search(r'"contactInfo"\s*:\s*"([^"]+)"', cleaned_response)
        if contact_match:
            recovered_data["contactInfo"] = contact_match.group(1)
         
        missing_fields_match = re.search(r'"missingFields"\s*:\s*\[(.*?)\]', cleaned_response, re.DOTALL)
        if missing_fields_match:
            raw_array_str = missing_fields_match.group(1)
            # Find all string values inside quotes within the bracket block
            found_fields = re.findall(r'"([^"]+)"', raw_array_str)
            if found_fields:
                recovered_data["missingFields"] = found_fields
        
        # If we still didn't find missing fields, append a standard warning
        if not recovered_data["missingFields"]:
            recovered_data["missingFields"] = ["JSON Transcript Parse Failure Recovery Active"]
            
        return VoiceActionOutput(**recovered_data)