from time import time
import streamlit as st
import requests

def render_email_classifier():
    st.title("📧 Agent 1 — Email Classification Agent")
    st.caption("Purpose: Automatically categorizes incoming emails and routes them to the correct workflow.")
    st.markdown("---")

    st.markdown("### **⚡ Control Center**")
    
    # 1. Fetch live system states and configuration payloads from backend
    current_status = "inactive"
    current_config = {"email": "", "app_password": "", "imap_server": "imap.gmail.com", "port": 993}
    
    try:
        current_status = requests.get("http://127.0.0.1:8000/agent-status").json().get("status", "inactive")
        res_data = requests.get("http://127.0.0.1:8000/get-email-settings").json()
        
        if isinstance(res_data, dict):
            current_config = res_data
        else:
            current_config = {"email": "", "app_password": "", "imap_server": "imap.gmail.com", "port": 993}
    except:
        current_status = "Disconnected"
        current_config = {"email": "", "app_password": "", "imap_server": "imap.gmail.com", "port": 993}

    # Display operational flags 
    if current_status == "active":
        st.success(f"🟢 **Agent Active** — Intercepting mail for **{current_config.get('email')}**")
    elif current_status == "inactive":
        st.warning("🔴 **Agent Stopped** — (Manual Review Console Active)")
    else:
        st.error("🚨 **System Offline:** Cannot connect to the backend server.")

    # 2. Unified Email Infrastructure Configuration Form
    with st.expander("⚙️ Email Account Settings", expanded=False):
        st.markdown("Manage connected email accounts. Select an existing profile or add a new one.")
        
        active_email = current_config.get("active_email", "")
        profiles = current_config.get("profiles", {})
        
        profile_options = ["➕ Add New Account..."] + list(profiles.keys())
        
        default_index = 0
        if active_email in profile_options:
            default_index = profile_options.index(active_email)
            
        selected_profile = st.selectbox("📂 Select Account to Edit/Activate", options=profile_options, index=default_index)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        form_email = ""
        form_pass = ""
        form_imap = "imap.gmail.com"
        form_port = 993
        
        if selected_profile != "➕ Add New Account...":
            form_email = selected_profile
            form_pass = profiles[selected_profile].get("app_password", "")
            form_imap = profiles[selected_profile].get("imap_server", "imap.gmail.com")
            form_port = profiles[selected_profile].get("port", 993)

        col_input_left, col_input_right = st.columns(2)
        with col_input_left:
            ui_email = st.text_input("Email Address", value=form_email, placeholder="company@gmail.com")
            ui_imap = st.text_input("IMAP Server", value=form_imap, placeholder="imap.gmail.com")
        with col_input_right:
            ui_password = st.text_input("App Password", value=form_pass, type="password", placeholder="xxxx xxxx xxxx xxxx")
            ui_port = st.number_input("IMAP Port", min_value=1, max_value=65535, value=int(form_port))

        if st.button("💾 Apply & Set as Active Account", type="secondary", use_container_width=True):
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
                        st.toast(f"Profile '{ui_email}' activated!", icon="💾")
                        st.rerun()
                    else:
                        st.error("Server rejected the configuration update.")
                except Exception as ex:
                    st.error(f"Connection failed: {ex}")
            else:
                st.error("Email, App Password, and IMAP host are required.")
                
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

    # 1. FETCH ALL DRAFT DATA
    all_drafts = []
    try:
        all_drafts = requests.get("http://127.0.0.1:8000/drafts").json()
    except:
        st.error("Could not fetch current records from backend.")
        return

    # 2. REAL-TIME METRICS CARDS
    st.markdown("### **📊 Inbox Metrics**")
    
    if not all_drafts:
        st.info("The dashboard is currently empty. Waiting for incoming mail...")
    else:
        total_emails = len(all_drafts)
        pending_count = len([d for d in all_drafts if d["status"] == "Pending Review"])
        processed_count = total_emails - pending_count

        def make_kpi_card(title, value, val_color="#333", bg_color="#ffffff"):
            return f"""
            <div style="background-color: {bg_color}; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                <div style="font-size: 12px; color: #666; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 4px;">{title}</div>
                <div style="font-size: 26px; font-weight: 700; color: {val_color}; margin: 0;">{value}</div>
            </div>
            """

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(make_kpi_card("Total Received", total_emails, "#1f77b4", "#f4f9fd"), unsafe_allow_html=True)
        with m2:
            st.markdown(make_kpi_card("Pending Review", pending_count, "#d62728", "#fdf4f4"), unsafe_allow_html=True)
        with m3:
            st.markdown(make_kpi_card("Processed", processed_count, "#2ca02c", "#f4fdf4"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Category Breakdown**")

        category_counts = {}
        for draft in all_drafts:
            cat = draft.get("predicted_category", "Uncategorized")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        num_cols = 4
        
        for i in range(0, len(categories), num_cols):
            cols = st.columns(num_cols)
            for j, col in enumerate(cols):
                if i + j < len(categories):
                    cat_name, count = categories[i + j]
                    with col:
                        st.markdown(make_kpi_card(cat_name, count), unsafe_allow_html=True)

    st.markdown("---")
    
    st.markdown("### **📥 Pending Email Reviews**")
    st.markdown("These emails were automatically classified and are waiting for your approval.")

    pending_items = [d for d in all_drafts if d["status"] == "Pending Review"]
    processed_items = [d for d in all_drafts if d["status"] != "Pending Review"]

    if not pending_items:
        st.info("No emails are currently awaiting verification.")
    else:
        draft_options = [f"Draft #{d['draft_id']}: {d['subject']} (From: {d['sender_name']})" for d in pending_items]
        selected_draft_str = st.selectbox("🔍 Choose an Email to Review:", draft_options)
        
        if selected_draft_str:
            target_id = int(selected_draft_str.split(":")[0].replace("Draft #", ""))
            target_record = next(d for d in pending_items if d["draft_id"] == target_id)

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("### **✉️ Original Email**")
                st.text_input("From (Name)", value=target_record["sender_name"], disabled=True, key=f"name_{target_id}")
                st.text_input("From (Email)", value=target_record["sender_email"], disabled=True, key=f"email_{target_id}")
                st.text_input("Subject", value=target_record["subject"], disabled=True, key=f"sub_{target_id}")
                st.text_area("Body", value=target_record["body"], height=180, disabled=True, key=f"body_{target_id}")
                
                attachments_list = target_record.get("attachments", [])
                has_pdf_attachment = any(str(name).lower().endswith(".pdf") for name in attachments_list)
                
                st.text_input("Attachments", value=", ".join(attachments_list) if attachments_list else "None", disabled=True, key=f"att_{target_id}")

                if has_pdf_attachment:
                    st.info("📎 **Notice:** PDF attachment sent to Document Extraction (Agent 2).")

            with col2:
                st.markdown("### **🤖 AI Suggestions**")
                edited_category = st.text_input("Category", value=target_record["predicted_category"], key=f"cat_edit_{target_id}")
                edited_action = st.text_input("Next Step", value=target_record["suggested_erp_action"], key=f"act_edit_{target_id}")
                
                st.metric(label="AI Confidence", value=f"{target_record['confidence']}%")
                
                if target_record["requires_human_review"]:
                    st.error("⚠️ **Notice:** This email needs careful review (low confidence or sensitive content).")
                else:
                    st.success("✅ **Notice:** Email categorization looks standard and clean.")
                    
                edited_summary = st.text_area("Summary", value=target_record["summary_draft"], height=120, key=f"sum_edit_{target_id}")

                st.markdown("<br>", unsafe_allow_html=True)
                act_col1, act_col2 = st.columns(2)
                
                with act_col1:
                    if st.button("📥 Approve & Proceed", type="primary", width="stretch", key=f"app_btn_{target_id}"):
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
                    if st.button("🗑️ Delete Request", type="secondary", width="stretch", key=f"rej_btn_{target_id}"):
                        requests.post("http://127.0.0.1:8000/drafts/action", json={
                            "draft_id": target_id, 
                            "status": "Rejected",
                            "updated_data": None
                        })
                        st.warning(f"Request #{target_id} deleted.")
                        st.rerun()

    if processed_items:
        st.markdown("---")
        st.markdown("### **📜 Processing History**")
        st.markdown("Review emails that have already been processed.")
        
        formatted_history = []
        for item in processed_items:
            formatted_history.append({
                "ID": item["draft_id"],
                "Sender": item["sender_name"],
                "Subject": item["subject"],
                "Category": item["predicted_category"],
                "Action Taken": item["suggested_erp_action"],
                "Status": "✅ Approved" if item["status"] == "Approved & Committed" else "❌ Rejected"
            })
        st.dataframe(formatted_history, hide_index=True)