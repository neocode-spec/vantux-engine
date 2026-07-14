import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json

# --- 1. SET PAGE CONFIG (Updated with Galaxy Icon) ---
st.set_page_config(page_title="Oremi Prime", page_icon="🌌", layout="wide")

# --- 2. PREMIUM PRIME STAR DESIGN SYSTEM (CUSTOM CSS) ---
st.markdown("""
    <style>
    /* Overall Background and Text */
    .stApp {
        background: linear-gradient(135deg, #090a0f 0%, #12141f 100%);
        color: #e2e8f0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0c0d14 !important;
        border-right: 1px solid #00c6ff33;
    }
    
    /* Input Box focus and styling */
    textarea, input {
        background-color: #151724 !important;
        color: #ffffff !important;
        border: 1px solid #0072ff !important;
        border-radius: 10px !important;
    }
    textarea:focus, input:focus {
        border-color: #00c6ff !important;
        box-shadow: 0 0 10px #00c6ff55 !important;
    }

    /* Premium Prime Star Gradient Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 198, 255, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 198, 255, 0.6) !important;
    }

    /* Secondary/Delete Buttons styling override */
    div.stButton > button[key*="delete"] {
        background: #ef4444 !important;
        box-shadow: 0 4px 10px rgba(239, 68, 68, 0.4) !important;
    }

    /* Message card layout */
    .chat-bubble-user {
        background: rgba(0, 114, 255, 0.15);
        border-left: 4px solid #0072ff;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .chat-bubble-model {
        background: rgba(0, 198, 255, 0.1);
        border-left: 4px solid #00c6ff;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }

    /* PREMIUM GRADIENT LOGO STYLE */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 25px;
    }
    .prime-logo {
        font-size: 42px;
        font-weight: 800;
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        font-family: 'Inter', sans-serif;
        line-height: 1;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SYSTEM CONFIGURATION ---
SYSTEM_PROMPT = (
    "You are Oremi (or Ore for short), the Sovereign What-If Simulation Engine. "
    "Your goal is human resilience and technical survival. "
    "Analyze crises by identifying physical bottlenecks, testing cascading probabilities, "
    "and providing practical, offline-capable, local-hardware solutions. "
    "Utilize your real-time Google Search capability to ground your simulation."
)

# MODEL OPTIONS updated to remove Gemini references
MODEL_OPTIONS = {
    "⚡ Core Engine (Default)": "gemini-3.5-flash",
    "🚀 Accelerated Mode": "gemini-3.1-flash-lite",
    "🧠 Deep Reasoning": "gemini-3.1-pro-preview"
}

# ... [Keep your existing Database Helper Functions and Session State code here] ...

# --- 6. THE UI ---
st.markdown("""
    <div class="logo-container">
        <div class="prime-logo">Oremi</div>
    </div>
""", unsafe_allow_html=True)

# ... [Keep your Login/Auth Logic here] ...

else:
    # --- 7. THE UNLOCKED ORE ENGINE ---
    user_threads = load_user_chats(st.session_state["username"])

    if st.sidebar.button("➕ Start New Conversation", use_container_width=True):
        st.session_state["active_thread_id"] = None
        st.session_state["active_thread_title"] = ""
        st.session_state["active_messages"] = []
        st.rerun()

    st.sidebar.write("### 📜 Conversation Archives")
    # ... [Keep your existing Archive logic here] ...

    if st.sidebar.button("System Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

    # Main Area
    st.write("### Real-time grounded strategy simulator.")

    # ... [Keep your message display logic here] ...

    col_input, col_selector = st.columns([3, 1])

    with col_input:
        user_prompt = st.text_input("Provide details or follow-up on the current scenario:", placeholder="Ask anything...", label_visibility="collapsed")

    with col_selector:
        # Removed "Gemini" from the selector label and list
        selected_display_name = st.selectbox("Sovereign Core", list(MODEL_OPTIONS.keys()), label_visibility="collapsed")
        selected_model_api = MODEL_OPTIONS[selected_display_name]

    if st.button("Transmit to Core"):
        # ... [Keep your existing API call and logic here] ...
