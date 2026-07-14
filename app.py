import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json

# --- 1. SET PAGE CONFIG (Only 1 sparkle icon on the browser tab) ---
st.set_page_config(page_title="Oremi", page_icon="✨", layout="wide")

# --- 2. THE NEON DESIGN SYSTEM (CUSTOM CSS WITH SHINY TEXT GRADIENTS) ---
st.markdown("""
    <style>
    /* Overall Background and Text */
    .stApp {
        background: linear-gradient(135deg, #0d0e15 0%, #1a1c29 100%);
        color: #e2e8f0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #11131f !important;
        border-right: 1px solid #ff007f33;
    }
    
    /* Input Box focus and styling */
    textarea, input {
        background-color: #1a1d30 !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 10px !important;
    }
    textarea:focus, input:focus {
        border-color: #ff007f !important;
        box-shadow: 0 0 10px #ff007f55 !important;
    }

    /* Premium Neon Gradient Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #ff007f 0%, #7928ca 100%) !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(255, 0, 127, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(255, 0, 127, 0.6) !important;
    }

    /* Secondary/Delete Buttons styling override */
    div.stButton > button[key*="delete"] {
        background: #ef4444 !important;
        box-shadow: 0 4px 10px rgba(239, 68, 68, 0.4) !important;
    }

    /* Message card layout */
    .chat-bubble-user {
        background: rgba(121, 40, 202, 0.2);
        border-left: 4px solid #7928ca;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .chat-bubble-model {
        background: rgba(255, 0, 127, 0.1);
        border-left: 4px solid #ff007f;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    
    /* Paywall Alert Banner */
    .paywall-banner {
        background: linear-gradient(90deg, #ff007f 0%, #7928ca 100%);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: white;
        font-weight: bold;
        box-shadow: 0 4px 20px rgba(255, 0, 127, 0.5);
        margin-bottom: 25px;
    }

    /* PREMIUM GRADIENT OREMI LOGO STYLE */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 15px;
    }
    .oremi-logo {
        font-size: 50px;
        font-weight: 800;
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 45%, #ff007f 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        font-family: 'Inter', sans-serif;
        line-height: 1;
    }
    .oremi-stars {
        font-size: 45px;
        background: linear-gradient(90deg, #ff007f 0%, #00c6ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
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
    "Utilize your real-time Google Search capability to ground your simulation in up-to-date real world news "
    "and pair real world events with systemic crises."
)

MODEL_OPTIONS = ["gemini-1.5-flash", "gemini-1.5-pro"]

# Initialize APIs from Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("System Error: Oremi Master Key missing.")

# Connect to Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error(f"Database Connection Failed: {str(e)}")

# --- 4. DATABASE HELPER FUNCTIONS ---
def check_user(username, password):
    try:
        response = supabase.table("vantux_users").select("*").eq("username", username).execute()
        user_data = response.data
        if user_data:
            if user_data[0]["password"] == password:
                is_premium = user_data[0].get("is_premium", False)
                return {
                    "status": True, 
                    "name": user_data[0]["full_name"], 
                    "username": user_data[0]["username"],
                    "is_premium": is_premium
                }
        return {"status": False, "message": "Username/password is incorrect"}
    except Exception as e:
        return {"status": False, "message": f"Database error: {str(e)}"}

def register_user(username, full_name, password):
    try:
        exists = supabase.table("vantux_users").select("username").eq("username", username).execute()
        if exists.data:
            return {"status": False, "message": "Username already exists!"}
        
        supabase.table("vantux_users").insert({
            "username": username,
            "full_name": full_name,
            "password": password,
            "is_premium": False
        }).execute()
        return {"status": True, "message": "Account created successfully! Switch to 'Login' to enter."}
    except Exception as e:
        return {"status": False, "message": f"Registration failed: {str(e)}"}

def save_or_update_thread(username, thread_id, title, messages):
    try:
        response_json = json.dumps(messages)
        if thread_id:
            supabase.table("vantux_chats").update({
                "scenario": title,
                "response": response_json
            }).eq("id", thread_id).execute()
            return thread_id
        else:
            result = supabase.table("vantux_chats").insert({
                "username": username,
                "scenario": title,
                "response": response_json
            }).execute()
            if result.data:
                return result.data[0]["id"]
    except Exception as e:
        st.error(f"Failed to sync thread to Cloud: {str(e)}")
    return None

def load_user_chats(username):
    try:
        response = supabase.table("vantux_chats").select("*").eq("username", username).order("created_at",
