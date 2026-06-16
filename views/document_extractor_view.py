import streamlit as st
import requests
from app.services.pdf_service import extract_text_from_pdf_bytes

def render_document_extractor():
    st.title("📑 Agent 2 — Document Data Extraction Engine")
    st.caption("Purpose: Extracts structured data like invoices and POs from email PDF attachments.")
    st.markdown("---")
    
    # Fetch all active records from backend staging cache
    all_doc_drafts = []
    try:
        all_doc_drafts = requests.get("http://127.0.0.1:8000/document-drafts").json()
    except:
        st.error("Could not fetch current document records from backend.")
        return

    pending_docs = [d for d in all_doc_drafts if d.get("status") == "Pending Review"]
    processed_docs = [d for d in all_doc_drafts if d.get("status") != "Pending Review"]
    
    col_queue, col_telemetry = st.columns([1, 1])
    selected_record = None
    
    with col_queue:
        st.markdown("### **📥 Attachment Queue**")
        
        queue_options = []
        for d in pending_docs:
            data_core = d.get("extracted_data", {}) or {}
            vendor_name = data_core.get("vendor", {}).get("name")
            customer_name = data_core.get("customer", {}).get("name")
            
            display_name = d.get("sender_name") or vendor_name or customer_name or "Unknown Sender"
            queue_options.append(f"📩 {display_name} (#{d['doc_id']})")
            
        if not queue_options:
            st.info("No new documents are waiting for review.")
            selected_option = None
        else:
            selected_option = st.selectbox(
                "Select a Document to Review:",
                ["-- Choose a document --"] + queue_options,
                key="agent2_source_selector"
            )
        
        if selected_option and selected_option != "-- Choose a document --":
            target_id = int(selected_option.split("#")[-1].replace(")", ""))
            selected_record = next(d for d in pending_docs if d["doc_id"] == target_id)
            
            st.info(f"⏳ **Origin:** Email Attachment.")
            st.text_area(
                "Raw Text Extracted from PDF:", 
                value=selected_record.get("raw_input_text", ""), 
                height=220, 
                disabled=True,
                key=f"raw_view_{target_id}"
            )
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📤 Upload Document Manually", expanded=False):
            st.markdown("Upload a PDF document directly:")
            uploaded_file = st.file_uploader("Choose a PDF document", type=["pdf"], key="manual_agent2_file_uploader")
            
            if uploaded_file:
                if st.button("🚀 Process Uploaded Document", type="secondary", use_container_width=True):
                    with st.spinner("Extracting text and analyzing..."):
                        try:
                            file_bytes = uploaded_file.read()
                            extracted_text = extract_text_from_pdf_bytes(file_bytes)
                            
                            if not extracted_text.strip():
                                st.error("Could not extract any text from this PDF.")
                            else:
                                response = requests.post(
                                    f"http://127.0.0.1:8000/extract-document?filename={uploaded_file.name}",
                                    json={"raw_text": extracted_text}
                                )
                                if response.status_code == 200:
                                    st.success(f"Successfully added '{uploaded_file.name}' to the queue!")
                                    st.rerun()
                                else:
                                    st.error(f"Server reported an error: {response.text}")
                        except Exception as upload_err:
                            st.error(f"Upload error: {upload_err}")

    with col_telemetry:
        st.markdown("### **🖥️ AI Interpretation**")
        if not selected_record:
            if "agent2_commit_alert" in st.session_state and st.session_state["agent2_commit_alert"]:
                st.success(st.session_state["agent2_commit_alert"])
                st.session_state["agent2_commit_alert"] = None
            else:
                st.info("System standing by. Select a document from the queue to view details.")
        else:
            st.session_state["agent2_commit_alert"] = None
            data_core = selected_record.get("extracted_data", {})
            
            st.metric(
                label=f"Document Type: {data_core.get('documentType', 'Unknown')}", 
                value=f"{data_core.get('confidence', 0)}% Confidence"
            )
            
            st.markdown("<br><b>📌 Missing Data</b>", unsafe_allow_html=True)
            missing_list = data_core.get("missingFields", [])
            if missing_list:
                badge_markdown = " ".join([f"`⚠️ {field}`" for field in missing_list])
                st.markdown(badge_markdown)
            else:
                st.success("All expected fields found successfully.")
            
            if data_core.get("warnings"):
                st.warning(f"⚠️ **Warnings:** {', '.join(data_core['warnings'])}")

    if selected_record:
        st.markdown("---")
        st.markdown(f"### **🛠️ Review & Approve Details — ID #{selected_record.get('doc_id')}**")
        
        target_uid = str(selected_record.get('doc_id'))
        data_core = selected_record.get("extracted_data", {})
        doc_header = data_core.get("document", {})
        vendor_header = data_core.get("vendor", {})
        customer_header = data_core.get("customer", {}) 

        st.markdown("<br><b>📧 Email Origin</b>", unsafe_allow_html=True)
        e_col1, e_col2, e_col3 = st.columns(3)
        with e_col1:
            st.text_input("From", value=selected_record.get("from_email") or "Manual Upload", disabled=True, key=f"email_from_{target_uid}")
        with e_col2:
            st.text_input("To", value=selected_record.get("to_email") or "Manual Upload", disabled=True, key=f"email_to_{target_uid}")
        with e_col3:
            st.text_input("Subject", value=selected_record.get("subject") or "No Subject", disabled=True, key=f"email_sub_{target_uid}")
        
        st.markdown("<br><b>🔑 Basic Details</b>", unsafe_allow_html=True)
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            val_doc_no = st.text_input("Document Number", value=str(doc_header.get("documentNo") or ""), key=f"doc_no_val_{target_uid}")
        with m_col2:
            val_doc_date = st.text_input("Date", value=str(doc_header.get("documentDate") or ""), key=f"doc_date_val_{target_uid}")
        with m_col3:
            val_due_date = st.text_input("Due Date", value=str(doc_header.get("dueDate") or ""), key=f"doc_due_val_{target_uid}")
        with m_col4:
            val_terms = st.text_input("Payment Terms", value=str(doc_header.get("paymentTerms") or ""), key=f"doc_trm_val_{target_uid}")
            
        c_col1, c_col2, c_col3, c_col4 = st.columns(4)
        with c_col1:
            val_vendor = st.text_input("Vendor Name", value=str(vendor_header.get("name") or ""), key=f"doc_vend_val_{target_uid}")
        with c_col2:
            val_vendor_gst = st.text_input("Vendor GSTIN", value=str(vendor_header.get("gstin") or ""), key=f"doc_gst_val_{target_uid}")
        with c_col3:
            val_customer = st.text_input("Customer Name", value=str(customer_header.get("name") or ""), key=f"doc_cust_val_{target_uid}")
        with c_col4:
            val_customer_gst = st.text_input("Customer GSTIN", value=str(customer_header.get("gstin") or ""), key=f"doc_cgst_val_{target_uid}")

        st.markdown("<br><b>💰 Financial Totals</b>", unsafe_allow_html=True)
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            try: subtotal_val = float(doc_header.get("subtotal") or 0.0)
            except: subtotal_val = 0.0
            val_subtotal = st.number_input("Subtotal", value=subtotal_val, key=f"doc_sub_val_{target_uid}")
        with f_col2:
            try: tax_val = float(doc_header.get("taxAmount") or 0.0)
            except: tax_val = 0.0
            val_tax = st.number_input("Tax", value=tax_val, key=f"doc_tax_val_{target_uid}")
        with f_col3:
            try: disc_val = float(doc_header.get("discount") or 0.0)
            except: disc_val = 0.0
            val_discount = st.number_input("Discount", value=disc_val, key=f"doc_disc_val_{target_uid}")
        with f_col4:
            try: total_val = float(doc_header.get("totalAmount") or 0.0)
            except: total_val = 0.0
            val_total = st.number_input("Total", value=total_val, key=f"doc_tot_val_{target_uid}")

        st.caption("Rounding Adjustments:")
        try: round_val = float(doc_header.get("roundOff") or 0.0)
        except: round_val = 0.0
        val_round = st.number_input("Round Off", value=round_val, key=f"doc_rnd_val_{target_uid}", label_visibility="collapsed")

        st.markdown("<br><b>📦 Line Items</b>", unsafe_allow_html=True)
        
        edited_line_items = st.data_editor(
            data_core.get("lineItems", []), 
            width="stretch", 
            num_rows="dynamic",
            key=f"data_grid_editor_{target_uid}"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        act_col1, act_col2 = st.columns([1, 1])
        
        with act_col1:
            if st.button("📥 Approve & Save", type="primary", width="stretch"):
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
                st.session_state["agent2_commit_alert"] = f"🟢 Document #{selected_record['doc_id']} approved and saved."
                st.rerun()
                
        with act_col2:
            if st.button("🗑️ Delete", type="secondary", width="stretch"):
                requests.post("http://127.0.0.1:8000/document-drafts/action", json={
                    "doc_id": selected_record["doc_id"], "status": "Rejected & Voided", "updated_data": None
                })
                st.session_state["agent2_commit_alert"] = f"🗑️ Document #{selected_record['doc_id']} deleted."
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
        st.markdown("### **📜 Processing History**")
        
        formatted_history = []
        for item in processed_docs:
            data_core = item.get("extracted_data", {})
            doc_header = data_core.get("document", {})
            vendor_header = data_core.get("vendor", {})
            
            formatted_history.append({
                "ID": item["doc_id"],
                "Doc Type": data_core.get("documentType", "Unknown"),
                "Doc Number": doc_header.get("documentNo") or "N/A",
                "Vendor/Customer": vendor_header.get("name") or "N/A",
                "Total": doc_header.get("totalAmount") or 0.0,
                "Status": "✅ Approved" if item["status"] == "Approved & Committed" else "❌ Rejected"
            })
        st.dataframe(formatted_history, hide_index=True)