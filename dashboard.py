import streamlit as st
import requests
import json
import os

# 1. Global Page Layout Configurations
st.set_page_config(page_title="Enterprise AI ERP Assistant Suite", layout="wide")

# Force-enable standard CSS layout parameters to preserve native HTML selection arrows
st.markdown("""
    <style>
    /* Ensure system browser select elements retain clear visual drop indications */
    div[data-baseweb="select"] {
        cursor: pointer !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Sidebar Navigation Control
st.sidebar.title("🤖 Navigation Hub")
st.sidebar.markdown("Select an active operational AI agent from the suite below:")

# Radio selection for managing our different agent instances
agent_selection = st.sidebar.radio(
    "Active AI Agents:",
    [
        "📊 Agent 1 — Email Classification",
        "📦 Agent 2 — (Placeholder)",
        "💰 Agent 3 — (Placeholder)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**System Status:**\n"
    "• FastAPI Backend: Connected\n"
    "• Current Workspace: Development"
)

# =========================================================================
# WORKSPACE: AGENT 1 — EMAIL CLASSIFICATION AGENT
# =========================================================================
if agent_selection == "📊 Agent 1 — Email Classification":
    st.title("📧 Agent 1 — Email Classification Agent")
    st.caption("Purpose: Analyzes incoming business communications, extracts transactional categories, and maps ERP workflow updates.")
    st.markdown("---")

    # --- LOAD TEST DATA ---
    SAMPLES_PATH = "data/samples.json"
    test_cases = []
    if os.path.exists(SAMPLES_PATH):
        with open(SAMPLES_PATH, "r") as f:
            test_cases = json.load(f)

    dropdown_options = [f"Case {tc['id']}: {tc['subject']} ({tc['fromName']})" for tc in test_cases]

    # Dashboard Grid Setup
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📥 Incoming Email Simulation")
        selected_option = st.selectbox("📂 Quick-Load a Test Sample Case:", ["-- Manual Input --"] + dropdown_options)
        
        # Form field fallback defaults
        def_id, def_name, def_email, def_sub, def_body, def_att = None, "ABC Traders", "customer@example.com", "Purchase Order", "Body...", "PO.pdf"
        
        # Override fields dynamically if a sample index is selected
        if selected_option != "-- Manual Input --":
            case_id = int(selected_option.split(":")[0].replace("Case ", ""))
            match = next(tc for tc in test_cases if tc["id"] == case_id)
            def_id = match["id"]
            def_name = match["fromName"]
            def_email = match["fromEmail"]
            def_sub = match["subject"]
            def_body = match["body"]
            def_att = ", ".join(match["attachmentNames"])

        # Construct UI Fields
        from_name = st.text_input("Sender Name", value=def_name)
        from_email = st.text_input("Sender Email", value=def_email)
        subject = st.text_input("Subject Line", value=def_sub)
        body = st.text_area("Email Body Content", height=200, value=def_body)
        attachments = st.text_input("Simulated Attachments (Comma Separated)", value=def_att)

        attachment_list = [att.strip() for att in attachments.split(",") if att.strip()]
        submit_btn = st.button("🚀 Run Email Classification Pipeline", type="primary")

    with col2:
        st.subheader("🤖 Agent Processing Results")
        
        if submit_btn:
            # Construct execution payload preserving the origin unique identifier index
            payload = {
                "id": def_id,  # Passes real case ID or None if purely manual
                "fromEmail": from_email,
                "fromName": from_name,
                "subject": subject,
                "body": body,
                "attachmentNames": attachment_list
            }
            
            with st.spinner("Executing Agent 1 analysis..."):
                try:
                    response = requests.post("http://127.0.0.1:8000/classify-email", json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        
                        m1, m2 = st.columns(2)
                        m1.metric(label="Assigned Category", value=result["category"])
                        m2.metric(label="Model Confidence Score", value=f"{result['confidence']}%")
                        
                        # Add high-end continuous evaluation certainty slider
                        st.progress(min(max(int(result["confidence"]) / 100, 0.0), 1.0))
                        
                        st.info(f"⚙️ **Suggested ERP Action:** `{result['suggestedERPAction']}`")
                        
                        if result["requiresHumanReview"]:
                            st.error("⚠️ **Attention Required:** This email was flagged for immediate Human Review.")
                        else:
                            st.success("✅ **Automated Pathing:** Safe for direct background ERP integration processing.")
                            
                        st.markdown("### 📝 Text Summary Generated")
                        st.write(result["summary"])
                        
                        st.markdown("### 🛠️ Raw Output Object JSON Received")
                        st.json(result)
                    else:
                        st.error(f"Backend API failure. Error code: {response.status_code}")
                except Exception as e:
                    st.error(f"Could not establish a connection to the FastAPI backend service: {e}")
        else:
            st.write("Select an evaluation sample or draft an email manually, then trigger the processing pipeline.")


# =========================================================================
# WORKSPACE: AGENT 2 PLACEHOLDER
# =========================================================================
elif agent_selection == "📦 Agent 2 — (Placeholder)":
    st.title("📦 Agent 2 — Core Engine Workspace")
    st.caption("This interface is prepared and wired to capture Agent 2 processing workflows.")
    st.markdown("---")
    
    st.warning("⚠️ **Under Development:** This agent workspace is structured but not yet active.")
    st.write("When you begin implementing Agent 2, we will map your new FastAPI routes and forms right here.")

# =========================================================================
# WORKSPACE: AGENT 3 PLACEHOLDER
# =========================================================================
elif agent_selection == "💰 Agent 3 — (Placeholder)":
    st.title("💰 Agent 3 — Core Engine Workspace")
    st.caption("This interface is prepared and wired to capture Agent 3 processing workflows.")
    st.markdown("---")
    
    st.warning("⚠️ **Under Development:** This agent workspace is structured but not yet active.")
    st.write("When you begin implementing Agent 3, we will map your new FastAPI routes and forms right here.")