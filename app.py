import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json

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
    "You are Libra, the Sovereign What-If Simulation Engine. "
    "Your goal is human resilience and technical survival. "
    "Analyze crises by identifying physical bottlenecks, testing cascading probabilities, "
    "and providing practical, offline-capable, local-hardware solutions. "
    "Utilize your real-time Google Search capability to ground your simulation in up-to-date real world news "
    "and pair real world events with systemic crises."
)

# Model options — display names carry no "Gemini" branding.
# Omini runs on Flash-Lite, Omini+ runs on Flash, Omini Ultra runs on Pro.
MODEL_OPTIONS = {
    "⚡ Omini": "gemini-3.1-flash-lite-preview",
    "🚀 Omini+": "gemini-3.5-flash",
    "🧠 Omini Ultra": "gemini-3.1-pro-preview"
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

    if st.sidebar.button("System Logout", use_container_width=True):
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
            model = genai.GenerativeModel(
                model_name=selected_model_api,
                system_instruction=SYSTEM_PROMPT,
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
            response_text = response.text
            
            st.session_state["active_messages"].append({"role": "user", "content": user_prompt})
            st.session_state["active_messages"].append({"role": "model", "content": response_text})
            
            if not st.session_state["active_thread_title"]:
                st.session_state["active_thread_title"] = user_prompt[:40]
            
            new_id = save_or_update_thread(
                st.session_state["username"], 
                st.session_state["active_thread_id"], 
                st.session_state["active_thread_title"], 
                st.session_state["active_messages"]
            )
            
            if not st.session_state["active_thread_id"]:
                st.session_state["active_thread_id"] = new_id
            
            st.session_state["is_thinking"] = False
            st.rerun()
        except Exception as e:
            error_text = str(e)
            st.session_state["is_thinking"] = False
            if "429" in error_text or "quota" in error_text.lower() or "RESOURCE_EXHAUSTED" in error_text:
                st.warning("Libra is resting for a moment — we've hit today's usage limit on this core. Try a different core above, or come back in a bit and it'll be ready to go again.")
            else:
                st.error(f"Engine Throttled: {error_text}")
            
