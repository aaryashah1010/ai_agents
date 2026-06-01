import streamlit as st
import requests
from streamlit_mic_recorder import speech_to_text

def render_voice_assistant():
    st.title("🗣️ Agent 3 — Voice-to-ERP Action Agent")
    st.caption("Purpose: Decodes conversational user transcripts, extracts transactional parameters, and maps downstream ERP routing intents.")
    st.markdown("---")

    # High-speed fragment container window to monitor incoming server updates on a loop
    @st.fragment(run_every="3s")
    def render_live_voice_workspace():
        # Fetch existing live records from backend database ledger cache file safely
        all_voice_drafts = []
        try:
            all_voice_drafts = requests.get("http://127.0.0.1:8000/voice-drafts").json()
        except:
            st.error("Could not fetch current voice action ledger from backend server gateway.")
            return

        pending_voices = [v for v in all_voice_drafts if v.get("status") == "Pending Review"]
        
        if st.session_state.get("active_live_voice_payload"):
            selected_voice_record = st.session_state["active_live_voice_payload"]
        elif pending_voices:
            selected_voice_record = pending_voices[0]
        else:
            selected_voice_record = None

        col_input, col_telemetry = st.columns([1, 1])
        
        with col_input:
            st.subheader("🎙️ Live Voice Input Capture")
            st.markdown("Click the record button below, speak your command clearly, and then click it again to parse:")

            # DYNAMIC AUDIO PIPELINE TELEMETRY STATUS PANEL
            if "last_processed_live_speech" not in st.session_state:
                st.info("🎯 **Pipeline Status:** System Standby — Waiting for Audio Input...")
            
            # Captures browser-native speech recognition events
            text_transcription_result = speech_to_text(
                language='en',
                start_prompt="🔴 Click to Record Speech",
                stop_prompt="🟩 Stop & Parse Command",
                just_once=True,
                key="live_audio_stt_hardware_stream"
            )
            
            # Initialize clean text string carrier
            clean_speech_text = ""
            
            # Branch A: Handle input if browser microphone successfully captures speech
            if text_transcription_result:
                clean_speech_text = str(text_transcription_result).strip()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 👑 BRANCH B: HARDWARE FALLBACK TEXT FIELD
            # This allows typing in commands if your local browser permissions block microphone streaming!
            fallback_text_input = st.text_input(
                "⌨️ Hardware Fallback — Type spoken instruction here if mic is blocked:",
                placeholder="Example: Create a quote for ABC Traders for 10 boxes of Product A.",
                key="voice_fallback_text_field"
            )
            
            if fallback_text_input and not clean_speech_text:
                clean_speech_text = fallback_text_input.strip()

            # Execute pipeline extraction if text is caught from either the Mic or the Textbox
            if clean_speech_text:
                # Check signature lock to avoid sending duplicate API hits inside the fast looping fragment
                if st.session_state.get("last_processed_live_speech") != clean_speech_text:
                    st.warning("🗣️ **Pipeline Status:** Payload Captured! Converting Speech to Text...")
                    
                    with st.spinner("Invoking Gemini Voice Intent Engine Layer... Staging Voucher..."):
                        try:
                            # Package and dispatch the transcript over to your FastAPI endpoint rule controller
                            res = requests.post(
                                "http://127.0.0.1:8000/process-voice-action", 
                                json={"transcript": clean_speech_text}
                            )
                            if res.status_code == 200:
                                # Save returned successful staging data straight to persistent view state
                                st.session_state["active_live_voice_payload"] = res.json()["voice_data"]
                                st.session_state["last_processed_live_speech"] = clean_speech_text
                                st.rerun()
                            else:
                                st.error(f"Backend reported engine fault processing text: {res.text}")
                        except Exception as ex:
                            st.error(f"Failed to process real-time voice pipeline query: {ex}")
                    

        with col_telemetry:
            st.subheader("🖥️ Live Model Output Telemetry")
            if not selected_voice_record:
                st.info("System standing by. Awaiting valid input mapping controls.")
            else:
                action_data = selected_voice_record.get("extracted_action_data", {})
                
                # Check if the voucher was flagged as a processing error
                if selected_voice_record.get("status") == "Failed Pre-Processing" or action_data.get("intent") == "Extraction Error":
                    st.error("🛑 **Enterprise System Alert: Automated Transaction Processing Failed**")
                    st.markdown("""
                    This record has been intercepted by safety guardrails due to an internal system exception or unparseable input.
                    - **Action Taken:** Saved safely to diagnostics ledger cache database.
                    - **Notification:** Downstream technical alert dispatched automatically to IT administration infrastructure.
                    """)
                    st.info(f"📁 **Diagnostic Log Summary:** {', '.join(action_data.get('warnings', []))}")
                else:
                    # Render your normal metric widgets smoothly
                    st.metric(
                        label=f"Identified Action Intent Target: {action_data.get('intent', 'Unknown')}",
                        value=f"{action_data.get('confidence', 0)}% Model Confidence"
                    )
                    st.text_input("Suggested Target UI ERP Command Routing Link:", value=action_data.get("suggestedERPAction", ""), disabled=True)


        # --- HUMAN CONFIRMATION FORM VIEW ---
        if selected_voice_record:
            st.markdown("---")
            st.subheader(f"🛠️ Human Review & Confirmation Workspace — Entry Ref #{selected_voice_record.get('voice_id', 'SIM')}")
            
            action_data = selected_voice_record.get("extracted_action_data", {})
            discount_node = action_data.get("discount", {}) or {}
            
            st.markdown("#### 🔑 Identity & Parameter Headers")
            h_col1, h_col2, h_col3, h_col4 = st.columns(4)
            with h_col1:
                val_customer = st.text_input("Customer Name Reference", value=str(action_data.get("customerName") or ""), key="v3_cust_name")
            with h_col2:
                val_vendor = st.text_input("Vendor Name Reference", value=str(action_data.get("vendorName") or ""), key="v3_vend_name")
            with h_col3:
                val_party_type = st.text_input("Evaluated Entity Party Type", value=str(action_data.get("partyType") or ""), key="v3_party_type")
            with h_col4:
                val_delivery_date = st.text_input("Preserved Delivery Deadline Text", value=str(action_data.get("deliveryDateText") or ""), key="v3_del_text")
                
            p_col1, p_col2, p_col3 = st.columns([1, 1, 2])
            with p_col1:
                val_disc_type = st.text_input("Pricing Deduction Type", value=str(discount_node.get("type") or "None"), key="v3_disc_type")
            with p_col2:
                try: disc_amt = float(discount_node.get("value") or 0.0)
                except: disc_amt = 0.0
                val_disc_val = st.number_input("Applied Deduction Value Metric", value=disc_amt, key="v3_disc_val")
            with p_col3:
                val_p_terms = st.text_input("Extracted Standard Settlement Payment Terms", value=str(action_data.get("paymentTerms") or "None"), key="v3_p_terms")

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

    render_live_voice_workspace()