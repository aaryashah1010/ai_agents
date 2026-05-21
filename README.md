# AI Enterprise ERP Assistant

This project is a multi-agent system designed to handle incoming company emails. It reads the email content, figures out the business intent, and maps it to a specific ERP action automatically. 



---
Agent 1 (Email Classification) :

## Implementation and Working

The system is split into three main layers: a frontend dashboard, a backend API gateway, and the AI agent core logic.

### 1. Data Input & Dashboard (Streamlit)
* **Single Runs:** You can select a pre-loaded test case from a dropdown menu or write an email manually. Clicking the run button bundles the metadata (sender name, email, subject, body, and attachments) into a JSON payload and sends it to the backend via an HTTP POST request.

### 2. Backend Validation & Routing (FastAPI & Pydantic)
* The FastAPI backend intercepts the incoming payload and passes it through a Pydantic model (`EmailInput`). This acts as a gatekeeper, making sure data types are correct before any AI code runs. 
* If a file reload or manual entry leaves the tracking ID empty (`None`), the router safely converts it to a standard integer index (`0` or `1`) so downstream processing never throws validation errors.

### 3. Agent Processing & Self-Healing (Gemini & Regex)
* **Prompt Engineering:** The agent reads an enterprise instruction template, injects the email details dynamically, and asks Gemini 2.5 Flash for a structured JSON block containing the category, a tight summary, a recommended ERP action, and a human-review flag.
* **Self-Healing Loop:** To prevent system crashes, the agent checks the raw text response from the API. If Gemini gets cut off mid-sentence due to free-tier output limitations, a regular expression (Regex) pattern automatically cuts in, extracts whatever variables were successfully generated, patches the missing JSON brackets on the fly, and flags the transaction for a human reviewer.
* **Rate-Limit Control:** The API client script wraps requests in an exponential backoff retry loop. If a 429 quota exhaustion error is detected, the code automatically pauses for 20 seconds to let the rolling free-tier window reset instead of crashing the pipeline.

---

## Tech Stack
* **FastAPI:** Core backend framework and API endpoints.
* **Streamlit:** Frontend data interface and testing panels.
* **Google GenAI SDK:** Model connection to utilize Gemini 2.5 Flash.
* **Pydantic (v2):** Structured data enforcement and JSON validation.

---

## How to Setup and Run

1. Add your API credentials to a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   DEV_MODE=false

2. Open a terminal and start the FastAPI backend:
   python -m uvicorn main:app --reload

3. Open a second terminal and launch the Streamlit interface:
python -m streamlit run dashboard.py