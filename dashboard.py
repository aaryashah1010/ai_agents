import streamlit as st
import requests
import json
import os
from data.sample_documents import SAMPLE_DOCUMENTS

# --- GLOBAL CORE INITIALIZATION PANELS ---
st.set_page_config(page_title="Enterprise AI ERP Assistant Suite", layout="wide")

st.markdown("""
    <style>
    div[data-baseweb="select"] { cursor: pointer !important; }
    .stDeployButton { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- NAVIGATION HUB SIDEBAR TRACKER ---
st.sidebar.title("🤖 Navigation Hub")
agent_selection = st.sidebar.radio(
    "Active AI Agents:",
    ["Agent 1 — Email Classifier", "Agent 2 — Document Extractor", "Agent 3 — (Coming Soon)"]
)

# =========================================================================
# WORKSPACE PIPELINE FOR AGENT 1 — EMAIL INTENT CLASSIFICATION
# =========================================================================
if agent_selection == "Agent 1 — Email Classifier":
    st.title("📧 Agent 1 — Email Classification Agent")
    st.caption("Purpose: Analyzes incoming communications, builds draft proposals, and routes data to human validation queues.")
    st.markdown("---")

    # 1. LIVE REPOSITORY TOGGLE RUNTIME CONTROLS
    st.subheader("⚡ Core Agent Control Center")
    current_status = "inactive"
    try:
        current_status = requests.get("http://127.0.0.1:8000/agent-status").json().get("status", "inactive")
    except:
        current_status = "Disconnected"

    if current_status == "active":
        st.success("🟢 **Agent Status:** Active & Automatically Intercepting Mailboxes")
    else:
        st.warning("🔴 **Agent Status:** Stopped & Idle (Draft Review Console Active)")

    btn_col1, btn_col2, _ = st.columns([1, 1, 4])
    with btn_col1:
        if st.button("▶️ Start Agent", type="primary", use_container_width=True, disabled=(current_status == "active")):
            requests.post("http://127.0.0.1:8000/agent-toggle", json={"command": "start"})
            st.rerun()
    with btn_col2:
        if st.button("⏹️ Stop Agent", type="secondary", use_container_width=True, disabled=(current_status == "inactive")):
            requests.post("http://127.0.0.1:8000/agent-toggle", json={"command": "stop"})
            st.rerun()

    st.markdown("---")
    st.subheader("📥 Human-in-the-Loop Draft Staging Ledger")
    st.markdown("The following records were extracted by the background AI agent and are awaiting manual validation.")

    # Isolated high-speed tracking loop fragment for Agent 1 mail parsing
    @st.fragment(run_every="3s")
    def render_live_draft_workspace():
        all_drafts = []
        try:
            all_drafts = requests.get("http://127.0.0.1:8000/drafts").json()
        except:
            st.error("Could not fetch current draft ledger records from backend.")
            return []

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

                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("### ✉️ Original Mail Details")
                    st.text_input("Sender Name", value=target_record["sender_name"], disabled=True, key=f"name_{target_id}")
                    st.text_input("Sender Email", value=target_record["sender_email"], disabled=True, key=f"email_{target_id}")
                    st.text_input("Subject Line", value=target_record["subject"], disabled=True, key=f"sub_{target_id}")
                    st.text_area("Original Text Content", value=target_record["body"], height=180, disabled=True, key=f"body_{target_id}")
                    
                    # Intercept files inside the payload array to flag any matching PDF attachments
                    attachments_list = target_record.get("attachments", [])
                    has_pdf_attachment = any(str(name).lower().endswith(".pdf") for name in attachments_list)
                    
                    st.text_input("Physical Attachments Detected", value=", ".join(attachments_list) if attachments_list else "None", disabled=True, key=f"att_{target_id}")
                    
                    # 👑 PIPELINE HANDOFF INDICATOR FOR AGENT 1
                    if has_pdf_attachment:
                        st.info("📎 **Pipeline Notice:** Attachment sent to Agent 2.")

                with col2:
                    st.markdown("### 🤖 Proposed AI Data Parameters")
                    edited_category = st.text_input("Assigned Category Classification", value=target_record["predicted_category"], key=f"cat_edit_{target_id}")
                    edited_action = st.text_input("Recommended ERP Transaction Target", value=target_record["suggested_erp_action"], key=f"act_edit_{target_id}")
                    
                    st.metric(label="Model Certainty Factor", value=f"{target_record['confidence']}%")
                    
                    if target_record["requires_human_review"]:
                        st.error("⚠️ **System Flag:** This file contains structural anomalies or negative sentiment parameters.")
                    else:
                        st.success("✅ **System Flag:** Data parameters appear clear and match baseline standards.")
                        
                    edited_summary = st.text_area("Generated Summary Draft", value=target_record["summary_draft"], height=120, key=f"sum_edit_{target_id}")

                    st.markdown("<br>", unsafe_allow_html=True)
                    act_col1, act_col2 = st.columns(2)
                    
                    with act_col1:
                        if st.button("✅ Approve & Commit to ERP", type="primary", use_container_width=True, key=f"app_btn_{target_id}"):
                            requests.post("http://127.0.0.1:8000/drafts/action", json={"draft_id": target_id, "status": "Approved & Committed"})
                            st.success(f"Success! Record #{target_id} committed.")
                            st.rerun()
                            
                    with act_col2:
                        if st.button("❌ Reject Draft", type="secondary", use_container_width=True, key=f"rej_btn_{target_id}"):
                            requests.post("http://127.0.0.1:8000/drafts/action", json={"draft_id": target_id, "status": "Rejected"})
                            st.warning(f"Draft document #{target_id} cancelled.")
                            st.rerun()
        return processed_items

    processed_items = render_live_draft_workspace()

    # 3. HISTORICAL DRILLDOWN PERFORMANCE LOG AT THE BOTTOM
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
        st.dataframe(formatted_history, use_container_width=True, hide_index=True)


# =========================================================================
# WORKSPACE PIPELINE FOR AGENT 2 — LIVE ATTACHMENT EXTRACTION CONSOLE
# =========================================================================
elif agent_selection == "Agent 2 — Document Extractor":
    st.title("📑 Agent 2 — Automated Document Data Extraction Engine")
    st.caption("Purpose: Tracks and reviews structured schemas generated automatically from incoming email PDF attachments.")
    st.markdown("---")
    
    # We wrap Agent 2 workspace inside a live high-speed fragment tracking loop
    @st.fragment(run_every="3s")
    def render_agent2_workspace():
        # Fetch live automated attachment structures from the backend database records safely
        all_doc_drafts = []
        try:
            all_doc_drafts = requests.get("http://127.0.0.1:8000/document-drafts").json()
        except:
            st.error("Could not fetch current document ledger records from backend.")
            return

        pending_docs = [d for d in all_doc_drafts if d.get("status") == "Pending Review"]
        
        col_queue, col_telemetry = st.columns([1, 1])
        selected_record = None
        
        with col_queue:
            st.subheader("📥 Live Ingested Attachment Queue")
            
            # Combine real real-time email entries with our 10 simulation vectors dynamically
            queue_options = []
            for d in pending_docs:
                queue_options.append(f"📩 Live Email Attachment (Voucher #{d['doc_id']})")
            for k in SAMPLE_DOCUMENTS.keys():
                queue_options.append(f"📋 Simulation Test Case: {k}")
                
            selected_option = st.selectbox(
                "Select a Document Source to Audit:",
                ["-- Choose an active document from queue --"] + queue_options,
                key="agent2_source_selector"
            )
            
            # Intercept selections to handle processing branches
            if selected_option and selected_option != "-- Choose an active document from queue --":
                if "Live Email Attachment" in selected_option:
                    # Extract index tracking ID string elements directly
                    target_id = int(selected_option.split("#")[-1].replace(")", ""))
                    selected_record = next(d for d in pending_docs if d["doc_id"] == target_id)
                    
                    st.info(f"⏳ **Origin:** Intercepted background email PDF attachment. Loaded into memory.")
                    st.text_area(
                        "Extracted Raw Document Text Block:", 
                        value=selected_record.get("raw_input_text", ""), 
                        height=220, 
                        disabled=True,
                        key=f"raw_view_{target_id}"
                    )
                else:
                    # Handle classic demo testing cases safely
                    sample_key = selected_option.replace("📋 Simulation Test Case: ", "")
                    raw_sample_text = SAMPLE_DOCUMENTS[sample_key].strip()
                    
                    st.info(f"🔬 **Origin:** Static prototyping verification test blueprint environment.")
                    st.text_area(
                        "Extracted Raw Document Text Block:", 
                        value=raw_sample_text, 
                        height=180, 
                        disabled=True,
                        key=f"sim_view_{sample_key.replace(' ', '_')}"
                    )
                    
                    if st.button("⚡ Run Gemini Analysis on Test Template", type="primary", use_container_width=True):
                        with st.spinner("Invoking Gemini extraction matrix lines..."):
                            try:
                                res = requests.post("http://127.0.0.1:8000/extract-document", json={"raw_text": raw_sample_text})
                                if res.status_code == 200:
                                    st.success("Mock Template Processed!")
                                    st.session_state["active_sim_payload"] = res.json()["draft_data"]
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Extraction execution failed: {e}")
                                
                    if "active_sim_payload" in st.session_state and st.session_state["active_sim_payload"]:
                        selected_record = st.session_state["active_sim_payload"]

        # 2. Render Live Model Output Telemetry Box
        with col_telemetry:
            st.subheader("🖥️ Live Model Output Telemetry")
            if not selected_record:
                if "agent2_commit_alert" in st.session_state and st.session_state["agent2_commit_alert"]:
                    st.success(st.session_state["agent2_commit_alert"])
                    st.session_state["agent2_commit_alert"] = None
                else:
                    st.info("System standing by. Choose an active item from the mailbox attachment queue to display telemetry details.")
            else:
                st.session_state["agent2_commit_alert"] = None
                data_core = selected_record.get("extracted_data", {})
                
                st.metric(
                    label=f"Identified Class Target: {data_core.get('documentType', 'Unknown')}", 
                    value=f"{data_core.get('confidence', 0)}% Model Certainty"
                )
                
                if data_core.get("missingFields"):
                    st.warning(f"⚠️ **Missing Parameters Identified:** {', '.join(data_core['missingFields'])}")
                if data_core.get("warnings"):
                    st.error(f"🛑 **Model Warnings:** {', '.join(data_core['warnings'])}")

        # 3. Render Human Validation Audit Workspace Form Fields if a record is active
        if selected_record:
            st.markdown("---")
            st.subheader(f"🛠️ Human-in-the-Loop Validation Workspace — Audit Entry Voucher #{selected_record.get('doc_id', 'SIM')}")
            
            data_core = selected_record.get("extracted_data", {})
            doc_header = data_core.get("document", {})
            vendor_header = data_core.get("vendor", {})
            
            st.markdown("#### 🔑 Core Identity Headers")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                val_doc_no = st.text_input("Document Reference ID", value=str(doc_header.get("documentNo") or ""), key="doc_no_val")
            with m_col2:
                val_doc_date = st.text_input("Issue Date (YYYY-MM-DD)", value=str(doc_header.get("documentDate") or ""), key="doc_date_val")
            with m_col3:
                val_vendor = st.text_input("Vendor Entity Name", value=str(vendor_header.get("name") or ""), key="doc_vend_val")
            with m_col4:
                val_vendor_gst = st.text_input("Vendor corporate GSTIN", value=str(vendor_header.get("gstin") or ""), key="doc_gst_val")
                
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                try: subtotal_val = float(doc_header.get("subtotal") or 0.0)
                except: subtotal_val = 0.0
                val_subtotal = st.number_input("Net Financial Subtotal", value=subtotal_val, key="doc_sub_val")
                
            with f_col2:
                try: tax_val = float(doc_header.get("taxAmount") or 0.0)
                except: tax_val = 0.0
                val_tax = st.number_input("Aggregated Value Tax Amount", value=tax_val, key="doc_tax_val")
                
            with f_col3:
                try: total_val = float(doc_header.get("totalAmount") or 0.0)
                except: total_val = 0.0
                val_total = st.number_input("Gross Total Balance Payable", value=total_val, key="doc_tot_val")
                
            with f_col4:
                val_terms = st.text_input("Settlement Payment Terms", value=str(doc_header.get("paymentTerms") or "None"), key="doc_trm_val")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📦 Extracted Table Product Line Items Grid")
            st.caption("Double click inside cells to directly override or fix specific tabular parameters programmatically:")
            
            # Interactive data grid framework sheet
            edited_line_items = st.data_editor(
                data_core.get("lineItems", []), 
                use_container_width=True, 
                num_rows="dynamic",
                key=f"data_grid_editor_{selected_record.get('doc_id', 'SIM')}"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            act_col1, act_col2 = st.columns([1, 1])
            
            with act_col1:
                if st.button("📥 Approve & Commit Document Draft parameters to ERP Ledger", type="primary", use_container_width=True):
                    compiled_human_data = data_core.copy()
                    if "document" not in compiled_human_data: compiled_human_data["document"] = {}
                    if "vendor" not in compiled_human_data: compiled_human_data["vendor"] = {}
                    
                    compiled_human_data["document"]["documentNo"] = val_doc_no
                    compiled_human_data["document"]["documentDate"] = val_doc_date
                    compiled_human_data["vendor"]["name"] = val_vendor
                    compiled_human_data["vendor"]["gstin"] = val_vendor_gst
                    compiled_human_data["document"]["subtotal"] = val_subtotal
                    compiled_human_data["document"]["taxAmount"] = val_tax
                    compiled_human_data["document"]["totalAmount"] = val_total
                    compiled_human_data["document"]["paymentTerms"] = val_terms
                    compiled_human_data["lineItems"] = edited_line_items
                    compiled_human_data["requiresHumanReview"] = False
                    
                    if "Live Email Attachment" in selected_option:
                        requests.post("http://127.0.0.1:8000/document-drafts/action", json={
                            "doc_id": selected_record["doc_id"],
                            "status": "Approved & Committed",
                            "updated_data": compiled_human_data
                        })
                        st.session_state["agent2_commit_alert"] = f"🟢 Transaction Closed! Document #{selected_record['doc_id']} posted to main ERP accounts."
                    else:
                        st.session_state["agent2_commit_alert"] = "🟢 Prototyping simulation voucher approved successfully."
                        st.session_state["active_sim_payload"] = None
                        
                    st.rerun()
                    
            with act_col2:
                if st.button("🗑️ Void/Reject Document Data", type="secondary", use_container_width=True):
                    if "Live Email Attachment" in selected_option:
                        requests.post("http://127.0.0.1:8000/document-drafts/action", json={
                            "doc_id": selected_record["doc_id"],
                            "status": "Rejected & Voided",
                            "updated_data": None
                        })
                        st.session_state["agent2_commit_alert"] = f"🗑️ Document Verification Voucher #{selected_record['doc_id']} declared void."
                    else:
                        st.session_state["agent2_commit_alert"] = "🗑️ Prototyping template placeholder rejected."
                        st.session_state["active_sim_payload"] = None
                        
                    st.rerun()

    render_agent2_workspace()

# =========================================================================
# RESERVED WORKSPACE FOR FUTURE AGENTS
# =========================================================================
else:
    st.title("🤖 Coming Soon Panel")
    st.info("This agent slot is reserved for downstream automation modules currently under development pipeline layout workflows.")