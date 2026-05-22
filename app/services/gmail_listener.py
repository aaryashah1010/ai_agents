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

load_dotenv()

is_agent_active = False
LEDGER_PATH = "data/draft_ledger.json"

def save_to_draft_ledger(email_data: EmailInput, agent_output):
    """Appends the classified record into a draft staging document cache."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    
    # Load existing drafts
    drafts = []
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r") as f:
                drafts = json.load(f)
        except:
            drafts = []

    # Check if this email unique tracking signature is already recorded
    if any(d.get("subject") == email_data.subject and d.get("sender_email") == email_data.fromEmail for d in drafts):
        print(f"[SYSTEM] Email '{email_data.subject}' already staged. Skipping duplicate.")
        return

    # Generate an incremental draft tracking index
    next_id = max([d.get("draft_id", 0) for d in drafts]) + 1 if drafts else 1

    # Create the Human-in-the-loop Draft object structure
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

def parse_and_process_email(mail, message_id):
    try:
        status, data = mail.fetch(message_id, "(RFC822)")
        if status != "OK" or not data[0]:
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
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                elif "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachment_names.append(filename)
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
        output = classify_email(live_payload)
        
        # Write to our staging area instead of directly to production ERP
        save_to_draft_ledger(live_payload, output)
        
        mail.store(message_id, "+FLAGS", "\\Seen")

    except Exception as e:
        print(f"[ERROR IN LIVE AGENT PARSER]: {e}")

def start_live_gmail_listener():
    # Force the thread to look at the global switch variable
    global is_agent_active
    username = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    print("[SYSTEM] Background thread initialized. Standing by for activation signal...")
    
    while True:
        # Check if the dashboard flipped the switch on
        if not is_agent_active:
            time.sleep(1)
            continue
            
        try:
            print("[SYSTEM] Activation signal received! Connecting to Gmail server...")
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(username, password)
            print("[SYSTEM] Authentication successful. Monitoring inbox for UNSEEN mail...")
            
            # Keep looping as long as the agent is active
            while is_agent_active:
                mail.select("inbox")
                status, messages = mail.search(None, "UNSEEN")
                
                # Add this explicit debug print to force terminal feedback
                print(f"[LIVE CHECK] Inbox scan status: {status} | Unread data packet: {messages[0]}")
                
                if status == "OK" and messages[0]:
                    email_ids = messages[0].split()
                    for msg_id in email_ids:
                        # Double check switch before running the parsing agent
                        if not is_agent_active:
                            break
                        parse_and_process_email(mail, msg_id)
                
                # Sleep for 5 seconds before checking the inbox again
                time.sleep(5)
                
            print("[SYSTEM] Agent deactivated by user switch. Closing mailbox link...")
            mail.logout()
            
        except Exception as e:
            print(f"[SYSTEM EXCEPTION] Error in mail stream loop: {e}")
            time.sleep(5)
            
def launch_listener_thread():
    listener_thread = threading.Thread(target=start_live_gmail_listener, daemon=True)
    listener_thread.start()