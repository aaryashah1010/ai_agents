import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

def generate_structured_response(prompt: str) -> str:
    """
    Requests a raw JSON string from Gemini without restrictive schema parameters,
    preventing mid-generation token truncation errors.
    """
    max_retries = 3
    retry_delay = 20
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    # We remove the response_schema here to stop the API from choking mid-string
                    response_mime_type="application/json",
                )
            )
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg and attempt < max_retries - 1:
                print(f"\n[RATE LIMIT] Cooling down for {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            else:
                raise e