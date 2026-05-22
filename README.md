# AI Enterprise ERP Assistant Suite

An event-driven, multi-agent AI system that captures incoming company emails from a live Gmail mailbox, analyzes business intent using Gemini, and creates staging drafts for manual verification via a **Human-in-the-Loop (HITL)** layout.

---
# Agent 1: Email Classification Agent

## Architecture Flow
[ Live Gmail Inbox ] ──► (IMAP Listener Thread) ──► [ Gemini 2.5 Agent ]
                                                            │
                                                            ▼
[ Streamlit UI Panel ] ◄── (Auto-Refresh Fragment) ◄── [ draft_ledger.json ]

1. **IMAP Listener:** Background thread checks your inbox every 3 seconds for `UNSEEN` mail and extracts text and attachment variables.
2. **Staging Cache:** FastAPI validates data via Pydantic and saves records into `data/draft_ledger.json` as `Pending Review`.
3. **Agent & Recovery:** Processes intent via `Gemini 2.5 Flash`. Employs a Regex self-healing layer to handle token cutoffs and manages rate limits via an exponential backoff loop.
4. **Dashboard Panel:** Streamlit uses `@st.fragment` to auto-refresh and display unapproved drafts every 3 seconds without losing active user text focus.

---

## Installation & Run

1. Environment Configuration (`.env`)
```env
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop   # 16-character Google App Password
DEV_MODE=false
```
2. File Initialization (data/draft_ledger.json)
[]

3. Execution Commands
# Terminal 1: Run Backend Gateway
```python -m uvicorn main:app --reload```

# Terminal 2: Run UI Workspace
```python -m streamlit run dashboard.py```

--- 
## Demo Steps
Open http://localhost:8501 and click ▶️ Start Agent.

Send an email to your registered GMAIL_USER address.

The dashboard dropdown menu will auto-refresh within 3 seconds to reveal the unapproved draft.

Audit the parameters, edit fields if required, and click "Approve & Commit to ERP"!
