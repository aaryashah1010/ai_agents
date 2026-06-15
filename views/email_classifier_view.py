from time import time

import streamlit as st
import requests

def render_email_classifier():
    st.title("📧 Agent 1 — Email Classification Agent")
    st.caption("Purpose: Analyzes incoming communications, builds draft proposals, and routes data to human validation queues.")
    st.markdown("---")

    st.subheader("⚡ Core Agent Control Center")
    
    # 1. Fetch live system states and configuration payloads from backend
    current_status = "inactive"
    current_config = {"email": "", "app_password": "", "imap_server": "imap.gmail.com", "port": 993}
    
    try:
        current_status = requests.get("http://127.0.0.1:8000/agent-status").json().get("status", "inactive")
        res_data = requests.get("http://127.0.0.1:8000/get-email-settings").json()
        
        # Defensive check: if the API returned a list or None, override it with a valid dict
        if isinstance(res_data, dict):
            current_config = res_data
        else:
            current_config = {"email": "", "app_password": "", "imap_server": "imap.gmail.com", "port": 993}
    except:
        current_status = "Disconnected"
        current_config = {"email": "", "app_password": "", "imap_server": "imap.gmail.com", "port": 993}

    # Display operational flags 
    if current_status == "active":
        st.success(f"🟢 **Agent Status:** Active — intercepting incoming mail stream via **{current_config.get('email')}**")
    elif current_status == "inactive":
        st.warning("🔴 **Agent Status:** Stopped & Idle (Draft Review Console Active)")
    else:
        st.error("🚨 **System Status:** Disconnected from downstream FastAPI runtime environment.")

    # 2. NEW STRIPED COMPONENT: Unified Email Infrastructure Configuration Form
    with st.expander("⚙️ Advanced Mail Routing & Credentials Configuration", expanded=False):
        st.markdown("Manage target ingestion criteria. Select an existing profile or add a new one.")
        
        # Determine dropdown options based on fetched backend data
        active_email = current_config.get("active_email", "")
        profiles = current_config.get("profiles", {})
        
        profile_options = ["➕ Add New Configuration Profile..."] + list(profiles.keys())
        
        # Try to default the dropdown to the active email if it exists
        default_index = 0
        if active_email in profile_options:
            default_index = profile_options.index(active_email)
            
        selected_profile = st.selectbox("📂 Select Configuration Profile to Edit/Activate", options=profile_options, index=default_index)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Populate default form values based on the dropdown selection
        form_email = ""
        form_pass = ""
        form_imap = "imap.gmail.com"
        form_port = 993
        
        if selected_profile != "➕ Add New Configuration Profile...":
            form_email = selected_profile
            form_pass = profiles[selected_profile].get("app_password", "")
            form_imap = profiles[selected_profile].get("imap_server", "imap.gmail.com")
            form_port = profiles[selected_profile].get("port", 993)

        # Grid input arrays
        col_input_left, col_input_right = st.columns(2)
        with col_input_left:
            ui_email = st.text_input("Email Address", value=form_email, placeholder="company@gmail.com")
            ui_imap = st.text_input("IMAP Server Address", value=form_imap, placeholder="imap.gmail.com")
        with col_input_right:
            ui_password = st.text_input("App Password", value=form_pass, type="password", placeholder="xxxx xxxx xxxx xxxx")
            ui_port = st.number_input("IMAP Port Metric", min_value=1, max_value=65535, value=int(form_port))

        if st.button("💾 Apply & Set as Active Target Profile", type="secondary", use_container_width=True):
            if ui_email and ui_password and ui_imap:
                payload = {
                    "email": ui_email,
                    "app_password": ui_password,
                    "imap_server": ui_imap,
                    "port": int(ui_port)
                }
                try:
                    res = requests.post("http://127.0.0.1:8000/save-email-settings", json=payload)
                    if res.status_code == 200:
                        st.toast(f"Profile '{ui_email}' committed and activated!", icon="💾")
                        time.sleep(0.5) # Give the toast a moment to show before rerunning
                        st.rerun()
                    else:
                        st.error("Internal processing server rejected deployment metadata.")
                except Exception as ex:
                    st.error(f"Failed to establish API sync: {ex}")
            else:
                st.error("Email, App Password, and IMAP host addresses are mandatory processing parameters.")
                
    # Main Agent operational trigger toggles
    btn_col1, btn_col2, _ = st.columns([1, 1, 4])
    with btn_col1:
        if st.button("▶️ Start Agent", type="primary", width="stretch", disabled=(current_status == "active" or current_status == "Disconnected")):
            requests.post("http://127.0.0.1:8000/agent-toggle", json={"command": "start"})
            st.rerun()
    with btn_col2:
        if st.button("⏹️ Stop Agent", type="secondary", width="stretch", disabled=(current_status == "inactive" or current_status == "Disconnected")):
            requests.post("http://127.0.0.1:8000/agent-toggle", json={"command": "stop"})
            st.rerun()

    st.markdown("---")

    # 1. FETCH ALL DRAFT DATA ONCE FOR THE ENTIRE PAGE
    all_drafts = []
    try:
        all_drafts = requests.get("http://127.0.0.1:8000/drafts").json()
    except:
        st.error("Could not fetch current draft ledger records from backend.")
        return

    # 2. NEW FEATURE: 📊 REAL-TIME INBOX METRICS CARDS
    st.subheader("📊 Real-Time Inbox Metrics")
    
    if not all_drafts:
        st.info("The ledger is currently empty. Waiting for incoming mail to generate metrics...")
    else:
        # Calculate high-level ledger stats
        total_emails = len(all_drafts)
        pending_count = len([d for d in all_drafts if d["status"] == "Pending Review"])
        processed_count = total_emails - pending_count

        # Render Top-Level Stats
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Emails Intercepted", total_emails)
        m2.metric("Pending Human Review", pending_count)
        m3.metric("Processed & Committed", processed_count)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Category Breakdown**")

        # Dynamically count how many emails belong to each predicted category
        category_counts = {}
        for draft in all_drafts:
            cat = draft.get("predicted_category", "Uncategorized")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Render Category Metrics in a dynamic 4-column grid
        categories = list(category_counts.items())
        num_cols = 4
        
        for i in range(0, len(categories), num_cols):
            cols = st.columns(num_cols)
            for j, col in enumerate(cols):
                if i + j < len(categories):
                    cat_name, count = categories[i + j]
                    # We use a smaller delta text just for visual flair if you like, or just the value
                    col.metric(label=cat_name, value=count)

    st.markdown("---")
    st.subheader("📥 Human-in-the-Loop Draft Staging Ledger")
    st.markdown("The following records were extracted by the background AI agent and are awaiting manual validation.")

    all_drafts = []
    try:
        all_drafts = requests.get("http://127.0.0.1:8000/drafts").json()
    except:
        st.error("Could not fetch current draft ledger records from backend.")
        return

    pending_items = [d for d in all_drafts if d["status"] == "Pending Review"]
    processed_items = [d for d in all_drafts if d["status"] != "Pending Review"]

    if not pending_items:
        st.info("No documents are currently awaiting manual verification. Waiting for new emails...")
    else:
        draft_options = [f"Draft #{d['draft_id']}: {d['subject']} (From: {d['sender_name']})" for d in pending_items]
        selected_draft_str = st.selectbox("🔍 Choose a Draft Document to Audit:", draft_options)
        
        if selected_draft_str:
            target_id = int(selected_draft_str.split(":")[0].replace("Draft #", ""))
            target_record = next(d for d in pending_items if d["draft_id"] == target_id)

            # 🟢 FIX Part 2: Dynamically include the Target ID in widget keys to force safe record switches
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("### ✉️ Original Mail Details")
                st.text_input("Sender Name", value=target_record["sender_name"], disabled=True, key=f"name_{target_id}")
                st.text_input("Sender Email", value=target_record["sender_email"], disabled=True, key=f"email_{target_id}")
                st.text_input("Subject Line", value=target_record["subject"], disabled=True, key=f"sub_{target_id}")
                st.text_area("Original Text Content", value=target_record["body"], height=180, disabled=True, key=f"body_{target_id}")
                
                attachments_list = target_record.get("attachments", [])
                has_pdf_attachment = any(str(name).lower().endswith(".pdf") for name in attachments_list)
                
                st.text_input("Physical Attachments Detected", value=", ".join(attachments_list) if attachments_list else "None", disabled=True, key=f"att_{target_id}")

                attachment_flag_value = target_record.get("attachment_processing_required", "No")
                st.text_input(
                    "Attachment Processing Required?", 
                    value=attachment_flag_value, 
                    disabled=True, 
                    key=f"att_req_flag_{target_id}"
                )

                if has_pdf_attachment:
                    st.info("📎 **Pipeline Notice:** Attachment sent to Agent 2.")

            with col2:
                st.markdown("### 🤖 Proposed AI Data Parameters")
                edited_category = st.text_input("Assigned Category Classification", value=target_record["predicted_category"], key=f"cat_edit_{target_id}")
                edited_action = st.text_input("Recommended ERP Action", value=target_record["suggested_erp_action"], key=f"act_edit_{target_id}")
                
                st.metric(label="Model Certainty Factor", value=f"{target_record['confidence']}%")
                
                if target_record["requires_human_review"]:
                    st.error("⚠️ **System Flag:** This file contains structural anomalies or negative sentiment parameters.")
                else:
                    st.success("✅ **System Flag:** Data parameters appear clear and match baseline standards.")
                    
                edited_summary = st.text_area("Generated Summary Draft", value=target_record["summary_draft"], height=120, key=f"sum_edit_{target_id}")

                st.markdown("<br>", unsafe_allow_html=True)
                act_col1, act_col2 = st.columns(2)
                
                with act_col1:
                    if st.button("✅ Approve & Commit to ERP", type="primary", width="stretch", key=f"app_btn_{target_id}"):
                        updated_payload = {
                            "category": edited_category,
                            "suggested_erp_action": edited_action,
                            "summary_draft": edited_summary
                        }
                        requests.post("http://127.0.0.1:8000/drafts/action", json={
                            "draft_id": target_id, 
                            "status": "Approved & Committed",
                            "updated_data": updated_payload
                        })
                        st.success(f"Success! Record #{target_id} committed.")
                        st.rerun()
                        
                with act_col2:
                    if st.button("❌ Reject Draft", type="secondary", width="stretch", key=f"rej_btn_{target_id}"):
                        requests.post("http://127.0.0.1:8000/drafts/action", json={
                            "draft_id": target_id, 
                            "status": "Rejected",
                            "updated_data": None
                        })
                        st.warning(f"Draft document #{target_id} cancelled.")
                        st.rerun()

    if processed_items:
        st.markdown("---")
        st.subheader("📜 Historical Processing Log")
        st.markdown("Review records that have already gone through human review triage.")
        
        formatted_history = []
        for item in processed_items:
            formatted_history.append({
                "ID": item["draft_id"],
                "Sender": item["sender_name"],
                "Subject": item["subject"],
                "Category Decision": item["predicted_category"],
                "ERP Action Mapping": item["suggested_erp_action"],
                "Summary": item["summary_draft"],
                "Audit Outcome Status": "✅ Approved" if item["status"] == "Approved & Committed" else "❌ Rejected"
            })
        st.dataframe(formatted_history, hide_index=True)