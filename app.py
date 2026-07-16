import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json
import uuid

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Libra", page_icon="✨", layout="wide")

# --- 2. PREMIUM LIBRA STAR DESIGN SYSTEM (CUSTOM CSS) ---
st.markdown("""
    <style>
    /* Overall Background and Text */
    .stApp {
        background: linear-gradient(135deg, #070913 0%, #0f1123 100%);
        color: #e2e8f0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #05060d !important;
        border-right: 1px solid #00c6ff22;
    }
    
    /* Input Box focus and styling */
    textarea, input {
        background-color: #121424 !important;
        color: #ffffff !important;
        border: 1px solid #0072ff !important;
        border-radius: 10px !important;
    }
    textarea:focus, input:focus {
        border-color: #00c6ff !important;
        box-shadow: 0 0 10px #00c6ff55 !important;
    }

    /* Premium Libra Gradient Buttons */
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

    /* PREMIUM GRADIENT LIBRA LOGO STYLE */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 20px;
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

    /* SINGLE SPARKLE, BLENDED INTO THE BLUE GRADIENT */
    .libra-sparkle {
        font-size: 36px;
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        line-height: 1;
        transition: transform 0.3s ease;
    }

    /* Gentle spin only while the engine is thinking */
    @keyframes spin-sparkle {
        0% { transform: rotate(0deg) scale(1); }
        50% { transform: rotate(180deg) scale(1.15); }
        100% { transform: rotate(360deg) scale(1); }
    }
    .thinking-active .libra-sparkle {
        animation: spin-sparkle 1.6s ease-in-out infinite;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SYSTEM CONFIGURATION ---
SYSTEM_PROMPT = (
    "You are Libra, the Sovereign What-If Simulation Engine, operating under a constitutional framework "
    "of radical honesty and real-world grounding. Your core purpose is to help people pressure-test ideas "
    "and scenarios — in business, space exploration, ocean systems, personal survival, or any other domain — "
    "by running every single request through a strict four-part discipline, without skipping a step:\n\n"

    "1. CANDID BREAKDOWN — Analyze the user's idea, question, or scenario with unforgiving candidness. "
    "No flattery, no softening. State plainly what is strong, what is weak, and what is missing.\n\n"

    "2. WHAT-IF PROBABILITY SIMULATION — Use your real-time Google Search capability to ground the idea in "
    "current, real-world conditions and events. Identify specific weaknesses, and explain concretely what "
    "can and will go wrong, with probability-weighted reasoning where possible — not vague hedging, but "
    "'this is likely because X is currently happening in the real world right now.'\n\n"

    "2i. BRAINSTORM — Collaboratively generate concrete solutions and mitigations for every weakness "
    "surfaced in step 2. Treat this as a working session with the user, not a lecture — build with them.\n\n"

    "3. CONCLUSION (ROLLED-UP SYNTHESIS) — Deliver a clear, final verdict that ties the breakdown, the "
    "probability simulation, and the brainstorm together. Explicitly connect your conclusion back to the "
    "reason Libra exists: to help humans navigate real, converging crises — resource scarcity, ecological "
    "instability, geopolitical fragility, and technological overreach — with clarity instead of hype.\n\n"

    "Constitutional principles governing all four steps:\n"
    "- Never fabricate statistics, sources, or events. If uncertain, say so plainly rather than guessing.\n"
    "- Ground reasoning in verifiable, current real-world information via search whenever the topic touches "
    "economics, technology, geopolitics, climate, or science.\n"
    "- Apply this discipline uniformly across every domain — a small business plan deserves the same rigor "
    "as a space mission or an ocean engineering proposal.\n"
    "- Candidness is not cruelty: be direct and unsparing about weaknesses, but always pair criticism with "
    "actionable paths forward in the brainstorm step.\n"
    "- You are a simulation and thinking partner, not an oracle. Present probabilities and scenarios, never "
    "guarantees."
)

# Model options — display names carry no "Gemini" branding.
# Omini runs on Flash-Lite, Omini+ runs on Flash, Omini Ultra runs on Pro.
MODEL_OPTIONS = {
    "⚡ Omini": "gemini-3.5-flash-lite",
    "🚀 Omini+": "gemini-3.5-flash",
    "🧠 Omini Ultra": "gemini-3.5-pro"
}

# Initialize APIs from Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("System Error: Libra Master Key missing in secrets.toml.")

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
                return {
                    "status": True, 
                    "name": user_data[0]["full_name"], 
                    "username": user_data[0]["username"]
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
            "is_premium": True
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

# --- 4b. PERSISTENT LOGIN (SESSION TOKEN) FUNCTIONS ---
def save_session_token(username, token):
    try:
        supabase.table("vantux_users").update({"session_token": token}).eq("username", username).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save session: {str(e)}")
        return False

def validate_session_token(token):
    try:
        response = supabase.table("vantux_users").select("*").eq("session_token", token).execute()
        user_data = response.data
        if user_data:
            return {"status": True, "name": user_data[0]["full_name"], "username": user_data[0]["username"]}
        return {"status": False}
    except Exception:
        return {"status": False}

def clear_session_token(username):
    try:
        supabase.table("vantux_users").update({"session_token": None}).eq("username", username).execute()
    except Exception:
        pass

# --- 4c. USER MEMORY FUNCTIONS (LIMITED / FREE-TIER: USER-TAUGHT ONLY) ---
def get_user_memory(username):
    try:
        response = supabase.table("vantux_memory").select("*").eq("username", username).order("created_at", desc=False).execute()
        return response.data
    except Exception:
        return []

def add_memory(username, fact):
    try:
        supabase.table("vantux_memory").insert({"username": username, "fact": fact}).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save memory: {str(e)}")
        return False

def delete_memory(memory_id):
    try:
        supabase.table("vantux_memory").delete().eq("id", memory_id).execute()
        return True
    except Exception:
        return False

# --- 5. SESSION STATE HANDLING ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "active_thread_id" not in st.session_state:
    st.session_state["active_thread_id"] = None
if "active_thread_title" not in st.session_state:
    st.session_state["active_thread_title"] = ""
if "active_messages" not in st.session_state:
    st.session_state["active_messages"] = []
if "is_thinking" not in st.session_state:
    st.session_state["is_thinking"] = False

# Auto-login on page refresh: check for a valid session token in the URL
if not st.session_state["logged_in"]:
    token = st.query_params.get("token")
    if token:
        result = validate_session_token(token)
        if result["status"]:
            st.session_state["logged_in"] = True
            st.session_state["user_name"] = result["name"]
            st.session_state["username"] = result["username"]

# --- 6. THE UI (CLEAN LOGO, SINGLE GRADIENT SPARKLE) ---
thinking_class = "thinking-active" if st.session_state["is_thinking"] else ""

st.markdown(f"""
    <div class="logo-container {thinking_class}">
        <div class="prime-logo">Libra</div>
        <span class="libra-sparkle">✨</span>
    </div>
""", unsafe_allow_html=True)

if not st.session_state["logged_in"]:
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
        st.subheader("Login to Portal")
        login_user = st.text_input("Username")
        login_pass = st.text_input("Password", type="password")
        
        if st.button("Login"):
            result = check_user(login_user, login_pass)
            if result["status"]:
                st.session_state["logged_in"] = True
                st.session_state["user_name"] = result["name"]
                st.session_state["username"] = result["username"]
                token = str(uuid.uuid4())
                save_session_token(result["username"], token)
                st.query_params["token"] = token
                st.rerun()
            else:
                st.error(result["message"])

else:
    # --- 7. THE UNLOCKED LIBRA ENGINE ---
    user_threads = load_user_chats(st.session_state["username"])

    if st.sidebar.button("➕ Start New Conversation", use_container_width=True):
        st.session_state["active_thread_id"] = None
        st.session_state["active_thread_title"] = ""
        st.session_state["active_messages"] = []
        st.rerun()

    st.sidebar.write("### 📜 Conversation Archives")
    if user_threads:
        for thread in user_threads:
            col1, col2 = st.sidebar.columns([4, 1])
            
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
            
            if col2.button("🗑️", key=f"delete_{thread['id']}", help="Delete this thread"):
                if delete_chat(thread["id"]):
                    if st.session_state["active_thread_id"] == thread["id"]:
                        st.session_state["active_thread_id"] = None
                        st.session_state["active_thread_title"] = ""
                        st.session_state["active_messages"] = []
                    st.toast("Thread deleted!", icon="🗑️")
                    st.rerun()
    else:
        st.sidebar.write("No archives found.")

    st.sidebar.write("### 🧠 Teach Libra About You")
    new_fact = st.sidebar.text_input("Something Libra should remember:", key="new_memory_input", label_visibility="collapsed", placeholder="e.g. I'm building a marketplace app")
    if st.sidebar.button("💾 Save to Memory", use_container_width=True):
        if new_fact.strip():
            if add_memory(st.session_state["username"], new_fact.strip()):
                st.toast("Libra will remember that.", icon="🧠")
                st.rerun()
        else:
            st.sidebar.warning("Type something first.")

    user_memory = get_user_memory(st.session_state["username"])
    if user_memory:
        for mem in user_memory:
            mcol1, mcol2 = st.sidebar.columns([4, 1])
            preview_fact = mem["fact"][:30] + "..." if len(mem["fact"]) > 30 else mem["fact"]
            mcol1.caption(f"• {preview_fact}")
            if mcol2.button("🗑️", key=f"delmem_{mem['id']}", help="Forget this"):
                delete_memory(mem["id"])
                st.rerun()
    else:
        st.sidebar.caption("Nothing taught yet — memory here is limited to what you teach it directly (unlimited auto-memory is a paid-tier feature).")

    if st.sidebar.button("System Logout", use_container_width=True):
        clear_session_token(st.session_state["username"])
        st.query_params.clear()
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["username"] = ""
        st.session_state["active_thread_id"] = None
        st.session_state["active_thread_title"] = ""
        st.session_state["active_messages"] = []
        st.rerun()

    # Main Area
    st.write("### Real-time grounded strategy simulator.")

    if st.session_state["active_messages"]:
        st.write(f"#### Thread: {st.session_state['active_thread_title']}")
        for msg in st.session_state["active_messages"]:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-bubble-user"><b>You:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble-model"><b>Libra:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

    col_input, col_selector = st.columns([3, 1])

    with col_input:
        user_prompt = st.text_input("Provide details or follow-up on the current scenario:", placeholder="Ask anything...", label_visibility="collapsed")

    with col_selector:
        selected_display_name = st.selectbox("Sovereign Core", list(MODEL_OPTIONS.keys()), label_visibility="collapsed")
        selected_model_api = MODEL_OPTIONS[selected_display_name]

    if st.button("Transmit to Core"):
        if not user_prompt.strip():
            st.warning("Please enter a scenario or query.")
        else:
            st.session_state["is_thinking"] = True
            st.rerun()

    # Execute simulation only when the thinking flag is True
    if st.session_state["is_thinking"]:
        try:
            memory_facts = get_user_memory(st.session_state["username"])
            if memory_facts:
                memory_text = "\n".join([f"- {m['fact']}" for m in memory_facts])
                personalized_prompt = SYSTEM_PROMPT + (
                    f"\n\nKnown context this user has taught you about themselves "
                    f"(reference only when genuinely relevant, don't force it in):\n{memory_text}"
                )
            else:
                personalized_prompt = SYSTEM_PROMPT

            model = genai.GenerativeModel(
                model_name=selected_model_api,
                system_instruction=personalized_prompt,
                tools=[{"google_search_retrieval": {}}]
            )
            
            history = []
            for m in st.session_state["active_messages"]:
                history.append({
                    "role": "user" if m["role"] == "user" else "model",
                    "parts": [m["content"]]
                })
            
            chat = model.start_chat(history=history)
            response = chat.send_message(user_prompt)
           
