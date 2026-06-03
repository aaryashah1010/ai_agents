import streamlit as st
import requests
import time
from streamlit_mic_recorder import speech_to_text

def render_voice_assistant():
    st.title("🗣️ Agent 3 — Voice-to-ERP Action Agent")
    st.caption("Purpose: Decodes conversational user transcripts, extracts transactional parameters, and maps downstream ERP routing intents.")
    st.markdown("---")

    @st.fragment(run_every="3s")
    def render_live_voice_workspace():
        
        selected_voice_record = None
        clean_speech_text = ""

        all_voice_drafts = []
        try:
            all_voice_drafts = requests.get("http://127.0.0.1:8000/voice-drafts").json()
        except:
            st.error("Could not fetch current voice action ledger from backend server gateway.")
            return

        pending_voices = [v for v in all_voice_drafts if v.get("status") == "Pending Review"]
        processed_voices = [v for v in all_voice_drafts if v.get("status") != "Pending Review"]
        
        # live autio ingestion and immediate telemetry screen panels
        col_input, col_telemetry = st.columns([1, 1])
        
        with col_input:
            st.subheader("🎙️ Live Voice Input Capture")
            st.markdown("Click the record button below, speak your command clearly, and then click it again to parse:")

            if "last_processed_live_speech" not in st.session_state:
                st.info("🎯 **Pipeline Status:** System Standby — Waiting for Audio Input...")
            
            text_transcription_result = speech_to_text(
                language='en',
                start_prompt="🔴 Click to Record Speech",
                stop_prompt="🟩 Stop & Parse Command",
                just_once=True,
                key="live_audio_stt_hardware_stream"
            )
            
            if text_transcription_result:
                clean_speech_text = str(text_transcription_result).strip()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            fallback_text_input = st.text_input(
                "⌨️ Hardware Fallback — Type spoken instruction here if mic is blocked:",
                placeholder="Example: Create a quote for ABC Traders for 10 boxes of Product A.",
                key="voice_fallback_text_field"
            )
            
            if fallback_text_input and not clean_speech_text:
                clean_speech_text = fallback_text_input.strip()

            if clean_speech_text:
                if st.session_state.get("last_processed_live_speech") != clean_speech_text:
                    st.warning("🗣️ **Pipeline Status:** Payload Captured! Converting Speech to Text...")
                    
                    with st.spinner("Invoking Gemini Voice Intent Engine Layer... Staging Voucher..."):
                        try:
                            res = requests.post(
                                "http://127.0.0.1:8000/process-voice-action", 
                                json={"transcript": clean_speech_text}
                            )
                            if res.status_code == 200:
                                # Instantly force selection view focus onto this freshly recorded item
                                new_record = res.json()["voice_data"]
                                st.session_state["active_live_voice_payload"] = new_record
                                st.session_state["last_processed_live_speech"] = clean_speech_text
                                st.rerun()
                            else:
                                st.error(f"Backend reported engine fault processing text: {res.text}")
                        except Exception as ex:
                            st.error(f"Failed to process real-time voice pipeline query: {ex}")

            if st.session_state.get("last_processed_live_speech"):
                st.success("✨ **Pipeline Status:** Audio Conversion Success!")
                st.markdown(f"""
                <div style="background-color: #1e293b; padding: 15px; border-left: 5px solid #10b981; border-radius: 4px; margin-bottom: 20px;">
                    <span style="color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; font-weight: bold;">Captured Audio Transcript:</span>
                    <p style="color: #f8fafc; font-size: 1.1rem; margin-top: 5px; font-style: italic; margin-bottom: 0px;">
                        "{st.session_state['last_processed_live_speech']}"
                    </p>
                </div>
                """, unsafe_allow_html=True)

        queue_options = ["-- Choose an active voucher draft to process --"]
        
        if st.session_state.get("active_live_voice_payload"):
            queue_options.append("✨ LIVE-VR-DRAFT | Newly Captured Action")
            
        for v in pending_voices:
            ts_part = v.get("timestamp", "0000-00-00 00:00:00").split()[0].replace("-", "")
            queue_options.append(f"📄 AUDIT-VR-{ts_part}-{v['voice_id']:02d} | Pending Review")

        #queue of ingested commands
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.subheader("📥 Queue of Ingested Spoken Commands")
        st.markdown("Select an ingested voice voucher record from ledger cache to display audit form:")
        
        default_index = 0
        if st.session_state.get("active_live_voice_payload"):
            default_index = 1
        elif len(queue_options) > 1 and not st.session_state.get("active_live_voice_payload"):
            default_index = 1

        selected_option = st.selectbox(
            "Select an ingested voice voucher record from ledger cache to display audit form:",
            options=queue_options,
            index=default_index,
            key="voice_queue_selectbox_widget",
            label_visibility="collapsed" 
        )
        
        if selected_option and not selected_option.startswith("--"):
            if "LIVE-VR-DRAFT" in selected_option:
                selected_voice_record = st.session_state.get("active_live_voice_payload")
            else:
                try:
                    parsed_id = int(selected_option.split("-")[-1].split()[0])
                    selected_voice_record = next(v for v in pending_voices if v["voice_id"] == parsed_id)
                except:
                    selected_voice_record = None

        with col_telemetry:
            st.subheader("🖥️ Live Model Output Telemetry")
            if not selected_voice_record:
                if "agent3_success_banner" in st.session_state and st.session_state["agent3_success_banner"]:
                    st.success(st.session_state["agent3_success_banner"])
                    st.session_state["agent3_success_banner"] = None
                else:
                    st.info("System standing by. Click 'Record' on the left, type an instruction, or choose an item from the draft queue box below.")
            else:
                st.session_state["agent3_success_banner"] = None
                action_data = selected_voice_record.get("extracted_action_data", {})
                
                st.metric(
                    label=f"Identified Action Intent Target: {action_data.get('intent', 'Unknown')}",
                    value=f"{action_data.get('confidence', 0)}% Model Confidence"
                )
                st.text_input("Suggested Target ERP Action:", value=action_data.get("suggestedERPAction", ""), disabled=True)
                
                if action_data.get("missingFields"):
                    st.error(f"⚠️ **Mandatory Missing Fields:** {', '.join(action_data['missingFields'])}")
                if action_data.get("warnings"):
                    st.warning(f"🛑 **Operational Warnings Logged:** {', '.join(action_data['warnings'])}")

        if selected_voice_record:
            st.info("Loaded transcript profile summary block:")
            st.text_area(
                "Decoded Audio Text Payload:", 
                value=selected_voice_record.get("raw_transcript_text", ""), 
                height=65, 
                disabled=True, 
                key=f"text_area_preview_{selected_voice_record.get('voice_id')}"
            )

        # human review and confirmation workspace for the selected record
        if selected_voice_record:
            st.markdown("---")
            st.subheader(f"🛠️ Human Review & Confirmation Workspace — Entry Ref #{selected_voice_record.get('voice_id', 'SIM')}")
            
            action_data = selected_voice_record.get("extracted_action_data", {})
            discount_node = action_data.get("discount", {}) or {}
            
            record_uid = str(selected_voice_record.get('voice_id', 'SIM'))

            st.markdown("#### 🔑 Identity & Parameter Headers")
            h_col1, h_col2, h_col3, h_col4 = st.columns(4)
            with h_col1:
                val_customer = st.text_input(
                    "Customer Name Reference", 
                    value=str(action_data.get("customerName") or ""), 
                    key=f"v3_cust_name_{record_uid}"
                )
            with h_col2:
                val_vendor = st.text_input(
                    "Vendor Name Reference", 
                    value=str(action_data.get("vendorName") or ""), 
                    key=f"v3_vend_name_{record_uid}"
                )
            with h_col3:
                val_party_type = st.text_input(
                    "Evaluated Entity Party Type", 
                    value=str(action_data.get("partyType") or ""), 
                    key=f"v3_party_type_{record_uid}"
                )
            with h_col4:
                val_delivery_date = st.text_input(
                    "Preserved Delivery Deadline Text", 
                    value=str(action_data.get("deliveryDateText") or ""), 
                    key=f"v3_del_text_{record_uid}"
                )
                
            p_col1, p_col2, p_col3 = st.columns([1, 1, 2])
            with p_col1:
                val_disc_type = st.text_input(
                    "Pricing Deduction Type", 
                    value=str(discount_node.get("type") or "None"), 
                    key=f"v3_disc_type_{record_uid}" 
                )
            with p_col2:
                try: 
                    disc_amt = float(discount_node.get("value") or 0.0)
                except: 
                    disc_amt = 0.0
                val_disc_val = st.number_input(
                    "Applied Deduction Value Metric", 
                    value=disc_amt, 
                    key=f"v3_disc_val_{record_uid}" 
                )
            with p_col3:
                val_p_terms = st.text_input(
                    "Extracted Standard Settlement Payment Terms", 
                    value=str(action_data.get("paymentTerms") or "None"), 
                    key=f"v3_p_terms_{record_uid}" 
                )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📦 Item Line Parameter Matrix Grid")
            
            edited_items_list = st.data_editor(
                action_data.get("items", []),
                width='stretch',
                num_rows="dynamic",
                key=f"data_grid_editor_v3_{selected_voice_record.get('voice_id', 'SIM')}"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            act_col1, act_col2 = st.columns(2)
            
            with act_col1:
                if st.button("📥 Approve Prefilled Data & Launch Active ERP Transaction Window", type="primary", width='stretch'):
                    updated_compiled_dict = action_data.copy()
                    updated_compiled_dict["customerName"] = val_customer
                    updated_compiled_dict["vendorName"] = val_vendor
                    updated_compiled_dict["partyType"] = val_party_type
                    updated_compiled_dict["deliveryDateText"] = val_delivery_date
                    updated_compiled_dict["paymentTerms"] = val_p_terms
                    updated_compiled_dict["discount"] = {"type": val_disc_type, "value": val_disc_val}
                    updated_compiled_dict["items"] = edited_items_list
                    updated_compiled_dict["confirmationRequired"] = False
                    
                    requests.post("http://127.0.0.1:8000/voice-drafts/action", json={
                        "voice_id": selected_voice_record["voice_id"],
                        "status": "Approved & Committed",
                        "updated_data": updated_compiled_dict
                    })
                    
                    st.session_state["agent3_success_banner"] = f"🟢 Voice Voucher #{selected_voice_record['voice_id']} successfully routed and prefilled into accounting form layout!"
                    st.session_state["active_live_voice_payload"] = None
                    st.session_state["last_processed_live_speech"] = None
                    st.rerun()
                    
            with act_col2:
                if st.button("🗑️ Reject & Clear Intent Request", type="secondary", width='stretch'):
                    requests.post("http://127.0.0.1:8000/voice-drafts/action", json={
                        "voice_id": selected_voice_record["voice_id"],
                        "status": "Rejected & Voided",
                        "updated_data": None
                    })
                    
                    st.session_state["agent3_success_banner"] = f"🗑️ Voice Command Entry Ref #{selected_voice_record['voice_id']} canceled."
                    st.session_state["active_live_voice_payload"] = None
                    st.session_state["last_processed_live_speech"] = None
                    st.rerun()

        # historical logs
        if processed_voices:
            st.markdown("---")
            st.subheader("📜 Historical Processing Log")
            st.markdown("Review records that have already gone through human validation triage.")
            
            formatted_history = []
            for item in processed_voices:
                core_data = item.get("extracted_action_data", {}) or {}
                resolved_party = core_data.get("customerName") or core_data.get("vendorName") or "N/A"
                
                formatted_history.append({
                    "Voucher ID": f"VR-{item['voice_id']:03d}",
                    "Timestamp": item.get("timestamp", "Unknown"),
                    "Original Transcript Text": item.get("raw_transcript_text", ""),
                    "Detected Intent": core_data.get("intent", "Unknown"),
                    "Associated Party": resolved_party,
                    "ERP Navigation Action Link": core_data.get("suggestedERPAction", "None"),
                    "Audit Outcome Status": "✅ Approved" if item["status"] == "Approved & Committed" else "❌ Voided/Rejected"
                })
                
            st.dataframe(formatted_history, width='stretch', hide_index=True)

    render_live_voice_workspace()