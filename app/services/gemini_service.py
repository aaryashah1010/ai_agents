import os
import time
import google.generativeai as genai
from dotenv import load_dotenv
import logging

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

if not os.path.exists("logs"):
    os.makedirs("logs")

INPUT_COST_PER_TOKEN = 0.075 / 1_000_000
OUTPUT_COST_PER_TOKEN = 0.30 / 1_000_000

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
                    response_mime_type="application/json",
                )
            )

            #COST CALCULATION ENGINE
            try:
                metadata = response.usage_metadata
                input_tokens = metadata.prompt_token_count
                output_tokens = metadata.candidates_token_count
                
                #final cost
                total_cost = (input_tokens * INPUT_COST_PER_TOKEN) + (output_tokens * OUTPUT_COST_PER_TOKEN)
                
                logging.info(f"API Cost Log - Input Tokens: {input_tokens}, Output Tokens: {output_tokens}, Cost: ${total_cost:.6f}")
            except Exception as meta_err:
                logging.warning(f"Failed to calculate transaction tokens usage metadata: {meta_err}")

            return response.text
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg and attempt < max_retries - 1:
                logging.warning(f"Gemini API 429 Rate Limit Exhausted. Commencing {retry_delay}s cooldown phase. Attempt {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
                continue
            else:
                logging.error(f"Critical connection breakdown inside Gemini API core client handler: {error_msg}")
                raise e
            
def call_gemini_api(prompt: str) -> str:
    """
    Unified standard wrapper function used by independent agent files 
    across the repository structure to communicate safely with the Gemini model core.
    """
    return generate_structured_response(prompt)