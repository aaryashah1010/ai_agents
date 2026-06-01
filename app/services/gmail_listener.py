import imaplib
import email
import os
import time
import json
import threading
from email.header import decode_header
from dotenv import load_dotenv
from app.models.email_models import EmailInput
from app.agents.email_agent import classify_email
from app.services.pdf_service import extract_text_from_pdf_bytes
from app.services.document_service import process_and_stage_document
import logging

load_dotenv()

is_agent_active = False
LEDGER_PATH = "data/draft_ledger.json"
DOC_LEDGER_PATH = "data/document_ledger.json"

# Capture unified application logging configuration
logger = logging.getLogger("app.log")

def save_to_draft_ledger(email_data: EmailInput, agent_output):
    """Appends the classified record into a draft staging document cache."""
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    
    drafts = []
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r") as f:
                drafts = json.load(f)
        except Exception as err:
            logger.warning(f"Failed to parse draft ledger data file: {err}. Starting with fresh structure.")
            drafts = []

    if any(d.get("subject") == email_data.subject and d.get("sender_email") == email_data.fromEmail for d in drafts):
        print(f"[SYSTEM] Email '{email_data.subject}' already staged. Skipping duplicate.")
        logger.info(f"Duplicate email found for tracking signature: '{email_data.subject}'. Processing skipped.")
        return

    next_id = max([d.get("draft_id", 0) for d in drafts]) + 1 if drafts else 1

    draft_record = {
        "draft_id": next_id,
        "status": "Pending Review",
        "sender_name": email_data.fromName,
        "sender_email": email_data.fromEmail,
        "subject": email_data.subject,
        "body": email_data.body,
        "attachments": email_data.attachmentNames,
        "predicted_category": agent_output.category,
        "confidence": agent_output.confidence,
        "suggested_erp_action": agent_output.suggestedERPAction,
        "summary_draft": agent_output.summary,
        "requires_human_review": agent_output.requiresHumanReview,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    drafts.append(draft_record)
    with open(LEDGER_PATH, "w") as f:
        json.dump(drafts, f, indent=2)
    print(f"[LEDGER] Saved live email as Draft ID #{next_id} (Status: Pending Review).")
    logger.info(f"Successfully committed Agent 1 pipeline results. Encapsulated Draft ID #{next_id}.")

def parse_and_process_email(mail, message_id):
    try:
        status, data = mail.fetch(message_id, "(RFC822)")
        if status != "OK" or not data[0]:
            logger.warning(f"Failed to fetch raw message body text for Message ID: {message_id}")
            return

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
            
        from_sender, encoding = decode_header(msg["From"])[0]
        if isinstance(from_sender, bytes):
            from_sender = from_sender.decode(encoding if encoding else "utf-8", errors="ignore")
            
        body = ""
        attachment_names = []
        
        # Track pending extraction payloads to process safely post-classification handshake
        pdf_attachments_payloads = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                elif "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        # Decode potential non-ASCII encoded attachment header strings safely
                        decoded_filename, file_enc = decode_header(filename)[0]
                        if isinstance(decoded_filename, bytes):
                            filename = decoded_filename.decode(file_enc if file_enc else "utf-8", errors="ignore")
                        
                        attachment_names.append(filename)
                        
                        # --- NEW FEATURE: LIVE PDF INTERCEPTION TRIGGER ---
                        if filename.lower().endswith(".pdf"):
                            raw_file_bytes = part.get_payload(decode=True)
                            if raw_file_bytes:
                                pdf_attachments_payloads.append((filename, raw_file_bytes))
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            
        live_payload = EmailInput(
            id=202,
            fromName=from_sender.split("<")[0].strip() if "<" in from_sender else from_sender,
            fromEmail=from_sender.split("<")[1].replace(">", "").strip() if "<" in from_sender else from_sender,
            subject=subject,
            body=body.strip(),
            attachmentNames=attachment_names
        )
        
        print(f"\n[LIVE EVENT] Processing incoming mail: {live_payload.subject}")
        logger.info(f"Initializing email processing workflow parameters for incoming message: '{live_payload.subject}'")
        
        output = classify_email(live_payload)
        save_to_draft_ledger(live_payload, output)
        
        # --- NEW FEATURE: EXECUTE AUTOMATED PIPELINE HANDOFF TO AGENT 2 ---
        for filename, file_bytes in pdf_attachments_payloads:
            logger.info(f"Discovered matching PDF business file attachment: '{filename}'. Initiating parsing sequence.")
            
            # 1. Convert PDF input streams to unstructured text arrays
            extracted_pdf_text = extract_text_from_pdf_bytes(file_bytes)
            
            if not extracted_pdf_text.strip():
                logger.warning(f"Aborting auto-handoff loop profile for '{filename}': Text conversion result empty.")
                continue
                
            # 2. Forward converted text structure directly to Agent 2 service core wrapper
            service_result = process_and_stage_document(extracted_pdf_text)
            
            if service_result.get("status") == "success":
                extracted_dict_data = service_result["data"]
                
                # 3. Stage parsed records straight into the data/document_ledger.json database
                os.makedirs(os.path.dirname(DOC_LEDGER_PATH), exist_ok=True)
                doc_drafts = []
                if os.path.exists(DOC_LEDGER_PATH) and os.path.getsize(DOC_LEDGER_PATH) > 0:
                    with open(DOC_LEDGER_PATH, "r", encoding="utf-8") as f:
                        try:
                            doc_drafts = json.load(f)
                        except Exception:
                            doc_drafts = []
                            
                next_doc_id = max([d.get("doc_id", 0) for d in doc_drafts]) + 1 if doc_drafts else 1
                
                doc_record = {
                    "doc_id": next_doc_id,
                    "status": "Pending Review",
                    "sender_name": live_payload.fromName,
                    "raw_input_text": extracted_pdf_text,
                    "extracted_data": extracted_dict_data,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                doc_drafts.append(doc_record)
                with open(DOC_LEDGER_PATH, "w", encoding="utf-8") as f:
                    json.dump(doc_drafts, f, indent=2)
                    
                logger.info(f"🎯 Auto-Handoff Success! Attached file '{filename}' converted and posted to Agent 2 Ledger under Voucher ID #{next_doc_id}")
            else:
                logger.error(f"Agent 2 extraction pipeline failed during automatic attachment ingestion: {service_result.get('message')}")

        mail.store(message_id, "+FLAGS", "\\Seen")

    except Exception as e:
        print(f"[ERROR IN LIVE AGENT PARSER]: {e}")
        logger.error(f"Fatal processing exception raised within message processing framework loops: {str(e)}")

def start_live_gmail_listener():
    global is_agent_active
    username = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    print("[SYSTEM] Background thread initialized. Standing by for activation signal...")
    logger.info("Background listener system process spun up successfully. Awaiting dashboard connection activation hook.")
    
    while True:
        if not is_agent_active:
            time.sleep(1)
            continue
            
        try:
            print("[SYSTEM] Activation signal received! Connecting to Gmail server...")
            logger.info("Activation switch flip detected. Constructing production secure IMAP link with imap.gmail.com...")
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(username, password)
            print("[SYSTEM] Authentication successful. Monitoring inbox for UNSEEN mail...")
            logger.info("IMAP Mailbox layer credential authentication verified. Inception loop active.")
            
            while is_agent_active:
                mail.select("inbox")
                status, messages = mail.search(None, "UNSEEN")
                
                print(f"[LIVE CHECK] Inbox scan status: {status} | Unread data packet: {messages[0]}")
                
                if status == "OK" and messages[0]:
                    email_ids = messages[0].split()
                    logger.info(f"Discovered {len(email_ids)} unread transaction emails inside target mailbox. Processing started.")
                    for msg_id in email_ids:
                        if not is_agent_active:
                            break
                        parse_and_process_email(mail, msg_id)
                
                time.sleep(5)
                
            print("[SYSTEM] Agent deactivated by user switch. Closing mailbox link...")
            logger.info("Deactivation command intercepted. Terminating downstream mailbox loop networks safely.")
            mail.logout()
            
        except Exception as e:
            print(f"[SYSTEM EXCEPTION] Error in mail stream loop: {e}")
            logger.error(f"Uncaught background runtime error raised in core polling worker sequence: {str(e)}")
            time.sleep(5)
            
def launch_listener_thread():
    listener_thread = threading.Thread(target=start_live_gmail_listener, daemon=True)
    listener_thread.start()