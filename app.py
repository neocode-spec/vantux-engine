import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json

# --- 1. SET PAGE CONFIG (Matches your premium brand logo in the browser tab) ---
st.set_page_config(page_title="Oremi ✨", page_icon="✨", layout="wide")

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
        response = supabase.table("vantux_chats").select("*").eq("username", username).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        return []

def delete_chat(chat_id):
    try:
        supabase.table("vantux_chats").delete().eq("id", chat_id).execute()
        return True
    except Exception as e:
        st.error(f"Failed to delete thread: {str(e)}")
        return False

# --- 5. SESSION STATE HANDLING ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "is_premium" not in st.session_state:
    st.session_state["is_premium"] = False
if "active_thread_id" not in st.session_state:
    st.session_state["active_thread_id"] = None
if "active_thread_title" not in st.session_state:
    st.session_state["active_thread_title"] = ""
if "active_messages" not in st.session_state:
    st.session_state["active_messages"] = []

# --- 6. THE UI (OREMI GRADIENT HEADER WITH ✨ ICON) ---
st.markdown("""
    <div class="logo-container">
        <div class="oremi-logo">Oremi</div>
        <div class="oremi-stars">✨</div>
    </div>
""", unsafe_allow_html=True)

if not st.session_state["logged_in"]:
    # Auth portal
    st.markdown("### Secure Access Portal")
    auth_action = st.radio("Access Portal:", ["Login", "Create Account"], horizontal=True)

    if auth_action == "Create Account":
        st.subheader("Register New Account")
        new_user = st.text_input("Username / Email")
        new_name = st.text_input("Full Name")
        new_pass = st.text_input("Password", type="password")
        
        if st.button("Sign Up"):
            if new_user and new_name and new_pass:
                result = register_user(new_user, new_name, new_pass)
                if result["status"]:
                    st.success(result["message"])
                else:
                    st.error(result["message"])
            else:
                st.warning("Please fill in all fields.")

    elif auth_action == "Login":
        st.subheader("Login to Oremi Portal")
        login_user = st.text_input("Username")
        login_pass = st.text_input("Password", type="password")
        
        if st.button("Login"):
            result = check_user(login_user, login_pass)
            if result["status"]:
                st.session_state["logged_in"] = True
                st.session_state["user_name"] = result["name"]
                st.session_state["username"] = result["username"]
                st.session_state["is_premium"] = result["is_premium"]
                st.rerun()
            else:
                st.error(result["message"])

else:
    # --- 7. THE UNLOCKED ORE ENGINE ---
    user_threads = load_user_chats(st.session_state["username"])
    thread_count = len(user_threads)
    is_premium = st.session_state["is_premium"]

    # Sidebar UI
    st.sidebar.success(f"User Active: {st.session_state['user_name']}")
    
    # Show Plan Type in Sidebar
    if is_premium:
        st.sidebar.markdown("👑 **Premium Active**")
    else:
        st.sidebar.markdown(f"📊 **Plan: Free Tier ({thread_count}/20 Chats Used)**")

    # Start New Conversation logic (Checking limit for free users)
    can_create_new = is_premium or (thread_count < 20)
    
    if st.sidebar.button("➕ Start New Conversation", use_container_width=True):
        if can_create_new:
            st.session_state["active_thread_id"] = None
            st.session_state["active_thread_title"] = ""
            st.session_state["active_messages"] = []
            st.rerun()
        else:
            st.sidebar.error("Sovereign Limit Reached! Upgrade to start a new thread.")

    st.sidebar.write("### 📜 Conversation Archives")
    if user_threads:
        for thread in user_threads:
            col1, col2 = st.sidebar.columns([4, 1])
            
            # Select thread button
            preview_title = thread["scenario"][:20] + "..." if len(thread["scenario"]) > 20 else thread["scenario"]
            if col1.button(f"💬 {preview_title}", key=f"select_{thread['id']}", use_container_width=True):
                st.session_state["active_thread_id"] = thread["id"]
                st.session_state["active_thread_title"] = thread["scenario"]
                try:
                    st.session_state["active_messages"] = json.loads(thread["response"])
                except:
                    st.session_state["active_messages"] = [
                        {"role": "user", "content": thread["scenario"]},
                        {"role": "model", "content": thread["response"]}
                    ]
                st.rerun()
            
            # Delete thread button
            if col2.button("🗑️", key=f"delete_{thread['id']}", help="Delete this thread"):
                if delete_chat(thread["id"]):
                    if st.session_state["active_thread_id"] == thread["id"]:
                        st.session_state["active_thread_id"] = None
                        st.session_state["active_thread_title"] = ""
                        st.session_state["active_messages"] = []
                    st.toast("Thread deleted from database!", icon="🗑️")
                    st.rerun()
    else:
        st.sidebar.write("No archives found.")

    if st.sidebar.button("System Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["username"] = ""
        st.session_state["is_premium"] = False
        st.session_state["active_thread_id"] = None
        st.session_state["active_thread_title"] = ""
        st.session_state["active_messages"] = []
        st.rerun()

    # Main Area
    st.write("### Real-time grounded strategy simulator powered by Neon UI Engine.")
