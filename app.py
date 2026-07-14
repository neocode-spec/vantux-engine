import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json

# --- 1. SET PAGE CONFIG (Blue Galaxy Theme) ---
st.set_page_config(page_title="Oremi", page_icon="✨", layout="wide")

# --- 2. THE BLUE GALAXY DESIGN SYSTEM (RESTORED) ---
st.markdown("""
    <style>
    /* Galaxy Background */
    .stApp {
        background: radial-gradient(circle at top right, #0a192f, #020c1b, #000000);
        color: #e2e8f0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0a192f !important;
        border-right: 1px solid #1e3a8a;
    }
    
    /* Input Box */
    textarea, input {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 10px !important;
    }
    
    /* Blue Glow Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Message Bubbles */
    .chat-bubble-user { background: rgba(30, 58, 138, 0.3); border-left: 4px solid #3b82f6; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
    .chat-bubble-model { background: rgba(59, 130, 246, 0.1); border-left: 4px solid #60a5fa; padding: 15px; border-radius: 10px; margin-bottom: 15px; }

    /* RESTORED OREMI BLUE LOGO */
    .logo-container { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
    .oremi-logo { 
        font-size: 50px; font-weight: 800; 
        background: linear-gradient(90deg, #60a5fa 0%, #3b82f6 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .oremi-stars { font-size: 45px; color: #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# --- 3. UPDATED MODEL ENDPOINTS (Fixing 404 Errors) ---
SYSTEM_PROMPT = "You are Oremi, the Sovereign What-If Simulation Engine. You are now allocated under the Prime Corporation division."
MODEL_OPTIONS = {
    "⚡ Flash Core": "gemini-3.5-flash", 
    "👑 Pro Core": "gemini-3.1-pro-preview"
}

# Initialize (Add your new API Key in Streamlit Secrets)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# [Rest of your logic remains exactly as you had it, now stabilized with the new endpoints]
# Ensure line 284/328 errors are fixed by keeping string literals on one line.
