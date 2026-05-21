import json
import re
import os
from app.models.email_models import EmailInput, EmailClassificationOutput
from app.services.gemini_service import generate_structured_response

PROMPT_PATH = "app/prompts/email_classifier_prompt.txt"

def classify_email(email_data: EmailInput) -> EmailClassificationOutput:
    # Set up safe ID tracking variables
    fallback_id = email_data.id if (hasattr(email_data, 'id') and email_data.id is not None) else 0
    prompt_id = email_data.id if (hasattr(email_data, 'id') and email_data.id is not None) else 1

    if os.getenv("DEV_MODE", "false").lower() == "true":
        return EmailClassificationOutput(
            id=fallback_id,
            category="Customer Purchase Order",
            confidence=95,
            suggestedERPAction="Create Sales Order",
            summary="Mock processing active: Loaded sample case verified successfully.",
            requiresHumanReview=False
        )

    with open(PROMPT_PATH, "r") as file:
        base_prompt = file.read()

    final_prompt = f"""
    {base_prompt}

    --- Incoming Email Metadata ---
    Target Verification ID: {prompt_id} 
    From Name: {email_data.fromName}
    From Email: {email_data.fromEmail}
    Attachments: {", ".join(email_data.attachmentNames) if email_data.attachmentNames else "None"}
    Subject: {email_data.subject}

    Body:
    {email_data.body}
    """

    try:
        # Get raw response text from our clean service
        raw_response = generate_structured_response(final_prompt)
        
        print("\n===== DEBUG: RAW LLM RETURN =====")
        print(raw_response)
        print("=================================\n")

        # Extract the JSON block using a robust regex filter text extraction
        json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if json_match:
            clean_json_string = json_match.group(0)
        else:
            clean_json_string = raw_response.strip()

        # Parse and inject our explicit runtime fallback ID to be absolutely safe
        parsed_dict = json.loads(clean_json_string)
        parsed_dict["id"] = fallback_id

        # Validate the keys natively against our output schema model
        return EmailClassificationOutput(**parsed_dict)

    except Exception as e:
        print(f"\n===== CRITICAL PIPELINE EXCEPTION =====\n{str(e)}")
        return EmailClassificationOutput(
            id=fallback_id,
            category="General Email",
            confidence=0,
            suggestedERPAction="No ERP Action",
            summary=f"System parser successfully handled an exception. Trace: {str(e)[:60]}",
            requiresHumanReview=True,
        )