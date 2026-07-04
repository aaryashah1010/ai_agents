# AI Enterprise ERP Assistant Suite

An event-driven, multi-agent AI system that captures business emails, document attachments, and conversational voice transcripts, processes them into structured financial data via Gemini, and tracks them through an interactive **Human-in-the-Loop (HITL)** validation dashboard.

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
4. **Dashboard Panel:** Streamlit uses dynamic keys and structural filters to display unapproved email drafts safely without resetting user text focus.

---

# Agent 2: Document Data Extraction Engine

## Architecture Flow
[ Email PDF Stream / Manual Upload ] ──► (PyPDF Reader) ──► [ Gemini 2.5 Agent ]
                                                                   │
                                                                   ▼
[ Streamlit UI Panel ] ◄───── (Dynamic ID State) ◄───── [ document_ledger.json ]

1. **Text Extraction:** PyPDF service reads binary bytes from email attachments or manual dashboard uploads to extract raw layout strings.
2. **Staging Cache:** FastAPI validates financial summaries and maps tabular arrays into `data/document_ledger.json`.
3. **Agent & Recovery:** Processes complex invoice matrices via Gemini. Employs a fallback schema recovery model to catch variable type crashes.
4. **Dashboard Panel:** Streamlit renders an interactive data editor grid. Uses dynamic keys tied to the document ID to prevent cross-record data leaking.

---

# Agent 3: Voice-to-ERP Action Assistant

## Architecture Flow
[ Browser Mic / Text Fallback ] ──► (Speech-to-Text) ──► [ Gemini 2.5 Agent ]
                                                                 │
                                                                 ▼
[ Streamlit UI Panel ] ◄──── (Isolated Fragment) ◄──── [ voice_ledger.json ]

1. **Audio Ingestion:** Browser-native speech recorder captures verbal commands and decodes them into conversational text streams.
2. **Staging Cache:** FastAPI packages structured operational records and logs exceptions inside `data/voice_ledger.json`.
3. **Agent & Recovery:** Maps intents to exact actions via Gemini. Automatically isolates spoken relative timeframes into text attributes.
4. **Dashboard Panel:** Renders telemetry metrics and prefilled transactional fields. Runs audio parsing inside an isolated fragment to preserve text entries.

---

## 🚀 Installation & Execution

### 1. Environment Configuration (`.env`)
```env
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop   # 16-character Google App Password
DEV_MODE=false
```

2. File Initialization
  (data/
    draft_ledger.json
    document_ledger.json
    voice_ledger.json)

[]

3. Execution Commands
# Terminal 1: Run Backend Gateway
```python -m uvicorn main:app --reload```

# Terminal 2: Run UI Workspace
```python -m streamlit run dashboard.py```

--- 
## Demo Steps
**Email Classification:** Open the dashboard, go to Agent 1, and hit ▶️ Start Agent. Send a business email with a PDF to your inbox. The drop-down updates within 3 seconds, showing the summary and attachment flags.

**Document Extraction:** Click over to Agent 2. The auto-handed file attachment text appears in the queue under its filename. Alternatively, upload a local file manually. Review the line-item grid, edit values, and click 📥 Approve & Commit.

**Voice Command to ERP:** Head to Agent 3. Click record and state a prompt (e.g., "Create a quote for boxes of Product A..."), or type into the textbox fallback. The assistant maps the intent, alerts you of missing details, and routes the transaction.
