import streamlit as st
import requests

def render_email_classifier():
    st.title("📧 Agent 1 — Email Classification Agent")
    st.caption("Purpose: Analyzes incoming communications, builds draft proposals, and routes data to human validation queues.")
    st.markdown("---")

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
        if st.button("▶️ Start Agent", type="primary", width="stretch", disabled=(current_status == "active")):
            requests.post("http://127.0.0.1:8000/agent-toggle", json={"command": "start"})
            st.rerun()
    with btn_col2:
        if st.button("⏹️ Stop Agent", type="secondary", width="stretch", disabled=(current_status == "inactive")):
            requests.post("http://127.0.0.1:8000/agent-toggle", json={"command": "stop"})
            st.rerun()

    st.markdown("---")
    st.subheader("📥 Human-in-the-Loop Draft Staging Ledger")
    st.markdown("The following records were extracted by the background AI agent and are awaiting manual validation.")

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
                    
                    attachments_list = target_record.get("attachments", [])
                    has_pdf_attachment = any(str(name).lower().endswith(".pdf") for name in attachments_list)
                    
                    st.text_input("Physical Attachments Detected", value=", ".join(attachments_list) if attachments_list else "None", disabled=True, key=f"att_{target_id}")
                    
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
                        if st.button("✅ Approve & Commit to ERP", type="primary", width="stretch", key=f"app_btn_{target_id}"):
                            requests.post("http://127.0.0.1:8000/drafts/action", json={"draft_id": target_id, "status": "Approved & Committed"})
                            st.success(f"Success! Record #{target_id} committed.")
                            st.rerun()
                            
                    with act_col2:
                        if st.button("❌ Reject Draft", type="secondary", width="stretch", key=f"rej_btn_{target_id}"):
                            requests.post("http://127.0.0.1:8000/drafts/action", json={"draft_id": target_id, "status": "Rejected"})
                            st.warning(f"Draft document #{target_id} cancelled.")
                            st.rerun()
        return processed_items

    processed_items = render_live_draft_workspace()

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