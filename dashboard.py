import streamlit as st
from views.email_classifier_view import render_email_classifier
from views.document_extractor_view import render_document_extractor
from views.voice_assistant_view import render_voice_assistant

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
    ["Agent 1 — Email Classifier", "Agent 2 — Document Extractor", "Agent 3 — Voice Assistant"]
)

# --- ROUTER DISPATCHER HANDSHAKE ---
if agent_selection == "Agent 1 — Email Classifier":
    render_email_classifier()

elif agent_selection == "Agent 2 — Document Extractor":
    render_document_extractor()

elif agent_selection == "Agent 3 — Voice Assistant":
    render_voice_assistant()