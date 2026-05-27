import os
import json
import re
from app.services.gemini_service import call_gemini_api
from app.models.document_models import DocumentExtractionOutput
import logging

PROMPT_FILE_PATH = "app/prompts/document_prompts.txt"

def extract_document_data(raw_text: str) -> DocumentExtractionOutput:
    """
    Reads the prompt framework template from the .txt file, pushes it along with 
    the raw document text to Gemini, and validates the incoming extraction payload.
    """
    # 1. Read the instructions from your new text file safely
    if not os.path.exists(PROMPT_FILE_PATH):
        raise FileNotFoundError(f"Missing mandatory instruction prompt template file at: {PROMPT_FILE_PATH}")
        
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
        prompt_template = f.read()
        
    # 2. Inject your unstructured raw document text into the prompt placeholder
    final_prompt = prompt_template.replace("{document_text}", raw_text)
    
    # 3. Dispatch the payload string over to your reliable Gemini service runner
    raw_response = call_gemini_api(final_prompt)
    
    # Clean up standard code-block markers if the model accidentally includes them
    cleaned_response = raw_response.strip().replace("```json", "").replace("```", "").strip()
    
    # 4. Attempt to parse the text directly into our strict Pydantic model structure
    try:
        json_data = json.loads(cleaned_response)
        return DocumentExtractionOutput(**json_data)
        
    except Exception as parse_error:
        logging.info(f"[RECOVERY TRIGGERED] Direct JSON parsing failed. Invoking Regex recovery engine: {parse_error}")
        
        # --- SELF-HEALING REGEX FALLBACK ZONE ---
        # If the output got cut off mid-sentence, rescue whatever structural attributes survived
        recovered_data = {
            "documentType": "Unknown",
            "confidence": 50,
            "missingFields": ["JSON Parse Failure Recovery Active"],
            "warnings": [f"Raw text structural anomaly caught during execution processing: {str(parse_error)}"],
            "requiresHumanReview": True
        }
        
        # Pull Document Type out via regex patterns if possible
        doc_type_match = re.search(r'"documentType"\s*:\s*"([^"]+)"', cleaned_response)
        if doc_type_match:
            recovered_data["documentType"] = doc_type_match.group(1)
            
        # Pull Financial Totals out via regex pattern matches if they exist
        total_match = re.search(r'"totalAmount"\s*:\s*([0-9.]+)', cleaned_response)
        if total_match:
            recovered_data["document"] = {"totalAmount": float(total_match.group(1))}
            
        return DocumentExtractionOutput(**recovered_data)