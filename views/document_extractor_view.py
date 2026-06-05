import streamlit as st
import requests
from app.services.pdf_service import extract_text_from_pdf_bytes

def render_document_extractor():
    st.title("📑 Agent 2 — Document Data Extraction Engine")
    st.caption("Purpose: Tracks and reviews structured schemas generated automatically from incoming email PDF attachments.")
    st.markdown("---")
    
    # Fetch all active records from backend staging cache
    all_doc_drafts = []
    try:
        all_doc_drafts = requests.get("http://127.0.0.1:8000/document-drafts").json()
    except:
        st.error("Could not fetch current document ledger records from backend.")
        return

    pending_docs = [d for d in all_doc_drafts if d.get("status") == "Pending Review"]
    processed_docs = [d for d in all_doc_drafts if d.get("status") != "Pending Review"]
    
    col_queue, col_telemetry = st.columns([1, 1])
    selected_record = None
    
    with col_queue:
        st.subheader("📥 Live Ingested Attachment Queue")
        
        # 👑 MAIN BRANCH LOGIC ACCEPTED: Dynamic Name Resolution Handshake
        queue_options = []
        for d in pending_docs:
            data_core = d.get("extracted_data", {}) or {}
            vendor_name = data_core.get("vendor", {}).get("name")
            customer_name = data_core.get("customer", {}).get("name")
            
            # 1. First choice: Use the live mailbox sender name captured by our listener
            # 2. Second choice: Fallback to parsed structural identity strings
            # 3. Final choice: Standard baseline label string
            display_name = d.get("sender_name") or vendor_name or customer_name or "Unknown Sender"
            
            queue_options.append(f"📩 {display_name} (#{d['doc_id']})")
            
        if not queue_options:
            st.info("No new email attachments are currently awaiting extraction processing.")
            selected_option = None
        else:
            selected_option = st.selectbox(
                "Select a Document Source to Audit:",
                ["-- Choose an active document from queue --"] + queue_options,
                key="agent2_source_selector"
            )
        
        if selected_option and selected_option != "-- Choose an active document from queue --":
            # Safely parse the trailing voucher digit block out of the option layout string
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
            
        #LOCAL MANUAL UPLOAD FEATURE 
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📤 Local Manual System Upload Fallback", expanded=False):
            st.markdown("Manually upload a business document PDF here to parse it through Agent 2:")
            uploaded_file = st.file_uploader("Choose a PDF document", type=["pdf"], key="manual_agent2_file_uploader")
            
            if uploaded_file:
                if st.button("🚀 Process & Inject Uploaded Document", type="secondary", use_container_width=True):
                    with st.spinner("Extracting PDF bytes and executing AI extraction..."):
                        try:
                            file_bytes = uploaded_file.read()
                            extracted_text = extract_text_from_pdf_bytes(file_bytes)
                            
                            if not extracted_text.strip():
                                st.error("Could not extract any structural text parameters from this PDF file.")
                            else:
                                response = requests.post(
                                    f"http://127.0.0.1:8000/extract-document?filename={uploaded_file.name}",
                                    json={"raw_text": extracted_text}
                                )
                                if response.status_code == 200:
                                    st.success(f"Successfully staged '{uploaded_file.name}' into queue!")
                                    st.rerun()
                                else:
                                    st.error(f"Backend reported processing failure: {response.text}")
                        except Exception as upload_err:
                            st.error(f"Upload subsystem error occurred: {upload_err}")

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
            
            st.markdown("##### 📌 Missing Core Parameters")
            missing_list = data_core.get("missingFields", [])
            if missing_list:
                badge_markdown = " ".join([f"`⚠️ {field}`" for field in missing_list])
                st.markdown(badge_markdown)
            else:
                st.success("All standard transaction criteria fields found successfully.")
            
            if data_core.get("warnings"):
                st.error(f"🛑 **Model Warnings:** {', '.join(data_core['warnings'])}")

    # Human-in-the-loop verification form setup logic runs safely with dynamic tracking IDs
    if selected_record:
        st.markdown("---")
        st.subheader(f"🛠️ Human-in-the-Loop Validation Workspace — Audit Entry Voucher #{selected_record.get('doc_id')}")
        
        target_uid = str(selected_record.get('doc_id'))
        data_core = selected_record.get("extracted_data", {})
        doc_header = data_core.get("document", {})
        vendor_header = data_core.get("vendor", {})
        customer_header = data_core.get("customer", {}) 
        
        st.markdown("#### 🔑 Core Identity Headers")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            val_doc_no = st.text_input("Document Reference ID", value=str(doc_header.get("documentNo") or ""), key=f"doc_no_val_{target_uid}")
        with m_col2:
            val_doc_date = st.text_input("Issue Date (YYYY-MM-DD)", value=str(doc_header.get("documentDate") or ""), key=f"doc_date_val_{target_uid}")
        with m_col3:
            val_due_date = st.text_input("Payment Maturity Due Date", value=str(doc_header.get("dueDate") or ""), key=f"doc_due_val_{target_uid}")
        with m_col4:
            val_terms = st.text_input("Settlement Payment Terms", value=str(doc_header.get("paymentTerms") or ""), key=f"doc_trm_val_{target_uid}")
            
        c_col1, c_col2, c_col3, c_col4 = st.columns(4)
        with c_col1:
            val_vendor = st.text_input("Vendor Entity Name", value=str(vendor_header.get("name") or ""), key=f"doc_vend_val_{target_uid}")
        with c_col2:
            val_vendor_gst = st.text_input("Vendor Corporate GSTIN", value=str(vendor_header.get("gstin") or ""), key=f"doc_gst_val_{target_uid}")
        with c_col3:
            val_customer = st.text_input("Customer Entity Name", value=str(customer_header.get("name") or ""), key=f"doc_cust_val_{target_uid}")
        with c_col4:
            val_customer_gst = st.text_input("Customer Corporate GSTIN", value=str(customer_header.get("gstin") or ""), key=f"doc_cgst_val_{target_uid}")

        st.markdown("#### 💰 Financial Ledger Totals")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            try: subtotal_val = float(doc_header.get("subtotal") or 0.0)
            except: subtotal_val = 0.0
            val_subtotal = st.number_input("Net Financial Subtotal", value=subtotal_val, key=f"doc_sub_val_{target_uid}")
        with f_col2:
            try: tax_val = float(doc_header.get("taxAmount") or 0.0)
            except: tax_val = 0.0
            val_tax = st.number_input("Aggregated Value Tax Amount", value=tax_val, key=f"doc_tax_val_{target_uid}")
        with f_col3:
            try: disc_val = float(doc_header.get("discount") or 0.0)
            except: disc_val = 0.0
            val_discount = st.number_input("Absolute Discount Deductions", value=disc_val, key=f"doc_disc_val_{target_uid}")
        with f_col4:
            try: total_val = float(doc_header.get("totalAmount") or 0.0)
            except: total_val = 0.0
            val_total = st.number_input("Gross Total Balance Payable", value=total_val, key=f"doc_tot_val_{target_uid}")

        st.caption("Adjustable Mathematical Rounding Corrections:")
        try: round_val = float(doc_header.get("roundOff") or 0.0)
        except: round_val = 0.0
        val_round = st.number_input("Round Off Adjustment", value=round_val, key=f"doc_rnd_val_{target_uid}", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📦 Extracted Table Product Line Items Grid")
        
        edited_line_items = st.data_editor(
            data_core.get("lineItems", []), 
            width="stretch", 
            num_rows="dynamic",
            key=f"data_grid_editor_{target_uid}"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        act_col1, act_col2 = st.columns([1, 1])
        
        with act_col1:
            if st.button("📥 Approve & Commit Document Draft parameters to ERP Ledger", type="primary", width="stretch"):
                compiled_human_data = data_core.copy()
                compiled_human_data["document"] = {
                    "documentNo": val_doc_no, "documentDate": val_doc_date, "dueDate": val_due_date,
                    "paymentTerms": val_terms, "subtotal": val_subtotal, "taxAmount": val_tax,
                    "discount": val_discount, "totalAmount": val_total, "roundOff": val_round
                }
                compiled_human_data["vendor"] = {"name": val_vendor, "gstin": val_vendor_gst}
                compiled_human_data["customer"] = {"name": val_customer, "gstin": val_customer_gst}
                compiled_human_data["lineItems"] = edited_line_items
                compiled_human_data["requiresHumanReview"] = False
                
                requests.post("http://127.0.0.1:8000/document-drafts/action", json={
                    "doc_id": selected_record["doc_id"], "status": "Approved & Committed", "updated_data": compiled_human_data
                })
                st.session_state["agent2_commit_alert"] = f"🟢 Transaction Closed! Document #{selected_record['doc_id']} posted to main ERP accounts."
                st.rerun()
                
        with act_col2:
            if st.button("🗑️ Void/Reject Document Data", type="secondary", width="stretch"):
                requests.post("http://127.0.0.1:8000/document-drafts/action", json={
                    "doc_id": selected_record["doc_id"], "status": "Rejected & Voided", "updated_data": None
                })
                st.session_state["agent2_commit_alert"] = f"🗑️ Document Verification Voucher #{selected_record['doc_id']} declared void."
                st.rerun()

    @st.fragment(run_every="3s")
    def attachment_loop_watcher():
        try:
            live_check = requests.get("http://127.0.0.1:8000/document-drafts").json()
            active_p_count = len([d for d in live_check if d.get("status") == "Pending Review"])
            if active_p_count != len(pending_docs):
                st.rerun()
        except: pass

    attachment_loop_watcher()

    if processed_docs:
        st.markdown("---")
        st.subheader("📜 Historical Document Processing Log")
        
        formatted_history = []
        for item in processed_docs:
            data_core = item.get("extracted_data", {})
            doc_header = data_core.get("document", {})
            vendor_header = data_core.get("vendor", {})
            
            formatted_history.append({
                "Voucher ID": item["doc_id"],
                "Doc Type": data_core.get("documentType", "Unknown"),
                "Doc Number": doc_header.get("documentNo") or "N/A",
                "Vendor/Party Name": vendor_header.get("name") or "N/A",
                "Total Amount": doc_header.get("totalAmount") or 0.0,
                "Processed Time": item.get("timestamp", "N/A"),
                "Audit Outcome Status": "✅ Approved" if item["status"] == "Approved & Committed" else "❌ Voided/Rejected"
            })
        st.dataframe(formatted_history, hide_index=True)