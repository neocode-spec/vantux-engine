import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Oremi", page_icon="✨", layout="wide")

# --- 2. CSS DESIGN SYSTEM (FIXED) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #0a192f, #020c1b, #000000); color: #e2e8f0; }
    section[data-testid="stSidebar"] { background-color: #0a192f !important; border-right: 1px solid #1e3a8a; }
    textarea, input { background-color: #0f172a !important; color: #ffffff !important; border: 1px solid #3b82f6 !important; border-radius: 10px !important; }
    div.stButton > button { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%) !important; color: white !important; border: none !important; border-radius: 12px !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important; }
    .chat-bubble-user { background: rgba(30, 58, 138, 0.3); border-left: 4px solid #3b82f6; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
    .chat-bubble-model { background: rgba(59, 130, 246, 0.1); border-left: 4px solid #60a5fa; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
    
    /* LOGO & BLUE GRADIENT STAR */
    .logo-container { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
    .oremi-logo { font-size: 50px; font-weight: 800; background: linear-gradient(90deg, #60a5fa 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .blue-star { font-size: 40px; background: linear-gradient(90deg, #60a5fa 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND SETUP ---
SYSTEM_PROMPT = "You are Oremi, the Sovereign What-If Simulation Engine. You are now allocated under the Prime Corporation division."

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "active_messages": []})

# --- 4. HEADER (With the new Blue Gradient Star) ---
st.markdown("""
    <div class="logo-container">
        <div class="oremi-logo">Oremi</div>
        <div class="blue-star">★</div>
    </div>
""", unsafe_allow_html=True)

# --- 5. LOGIC FLOW ---
if not st.session_state["logged_in"]:
    auth = st.radio("Access Portal:", ["Login", "Create Account"], horizontal=True)
    if auth == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            res = supabase.table("vantux_users").select("*").eq("username", u).execute()
            if res.data and res.data[0]["password"] == p:
                st.session_state.update({"logged_in": True, "username": u, "user_name": res.data[0]["full_name"]})
                st.rerun()
            else:
                st.error("Invalid credentials.")
else:
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.rerun()
    
    st.write("### Simulation Engine Active")
    
    # Message Loop
    for msg in st.session_state["active_messages"]:
        cls = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-model"
        st.markdown(f'<div class="{cls}"><b>{msg["role"].capitalize()}:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
    
    prompt = st.text_input("Transmit scenario:", key="input")
    if st.button("Transmit to Core") and prompt:
        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
            resp = model.generate_content(prompt)
            st.session_state["active_messages"].extend([{"role": "user", "content": prompt}, {"role": "model", "content": resp.text}])
            st.rerun()
        except Exception as e:
            st.error(f"System Error: {e}")
