import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client

# --- 1. THE NEON DESIGN SYSTEM (CUSTOM CSS) ---
st.set_page_config(page_title="Vantux Sovereign Engine", page_icon="⚡", layout="wide")

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

    /* Simulation Result Card */
    .result-card {
        background: rgba(26, 29, 48, 0.6);
        border: 1px solid #7928ca55;
        padding: 25px;
        border-radius: 16px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SYSTEM CONFIGURATION ---
SYSTEM_PROMPT = (
    "You are the Sovereign What-If Simulation Engine. "
    "Your goal is human resilience and technical survival. "
    "Analyze crises by identifying physical bottlenecks, testing cascading probabilities, "
    "and providing practical, offline-capable, local-hardware solutions."
)

MODEL_OPTIONS = ["gemini-1.5-flash", "gemini-1.5-pro"]

# Initialize APIs from Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("System Error: Vantux Core Master Key missing.")

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

# --- 3. DATABASE HELPER FUNCTIONS ---
def check_user(username, password):
    try:
        response = supabase.table("vantux_users").select("*").eq("username", username).execute()
        user_data = response.data
        if user_data:
            if user_data[0]["password"] == password:
                return {"status": True, "name": user_data[0]["full_name"], "username": user_data[0]["username"]}
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
            "password": password
        }).execute()
        return {"status": True, "message": "Account created successfully! Switch to 'Login' to enter."}
    except Exception as e:
        return {"status": False, "message": f"Registration failed: {str(e)}"}

def save_chat(username, scenario, response_text):
    try:
        supabase.table("vantux_chats").insert({
            "username": username,
            "scenario": scenario,
            "response": response_text
        }).execute()
    except Exception as e:
        st.error(f"Failed to save chat: {str(e)}")

def load_user_chats(username):
    try:
        response = supabase.table("vantux_chats").select("*").eq("username", username).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        return []

# --- 4. SESSION STATE HANDLING ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "current_response" not in st.session_state:
    st.session_state["current_response"] = ""

# --- 5. THE UI ---
st.title("⚡ Vantux Sovereign Engine")

if not st.session_state["logged_in"]:
    # Auth portal
    st.markdown("### Secure Access Portal")
    auth_action = st.radio("Access Portal:", ["Login", "Create Account"], horizontal=True)

    if auth_action == "Create Account":
        st.subheader("Register New Vantux Account")
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
        st.subheader("Login to Vantux Core")
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
    # --- 6. THE UNLOCKED NEON ENGINE ---
    user_chats = load_user_chats(st.session_state["username"])

    # Sidebar UI
    st.sidebar.success(f"User Active: {st.session_state['user_name']}")
    
    st.sidebar.write("### 📜 Simulation Archives")
    if user_chats:
        for chat in user_chats:
            preview = chat["scenario"][:25] + "..." if len(chat["scenario"]) > 25 else chat["scenario"]
            if st.sidebar.button(preview, key=f"chat_{chat['id']}"):
                st.session_state["current_response"] = {
                    "scenario": chat["scenario"],
                    "response": chat["response"]
                }
    else:
        st.sidebar.write("No archives found.")

    if st.sidebar.button("System Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["username"] = ""
        st.session_state["current_response"] = ""
        st.rerun()

    # Main Area
    st.write("### Offline-ready strategy simulator powered by Neon UI Engine.")
    
    selected_model = st.selectbox("Select Sovereign Brain Core:", MODEL_OPTIONS)
    scenario = st.text_area("Describe the crisis or scenario to simulate:", placeholder="e.g., Power grid failure in Rivers State...")

    if st.button("Initialize Simulation"):
        if not scenario.strip():
            st.warning("Please enter a scenario.")
        else:
            with st.spinner("Neon Core compiling probabilities..."):
                try:
                    model = genai.GenerativeModel(
                        model_name=selected_model,
                        system_instruction=SYSTEM_PROMPT
                    )
                    response = model.generate_content(scenario)
                    response_text = response.text
                    
                    save_chat(st.session_state["username"], scenario, response_text)
                    
                    st.session_state["current_response"] = {
                        "scenario": scenario,
                        "response": response_text
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"Engine Throttled: {str(e)}")

    # Display Active Chat Result inside a beautiful CSS Card
    if st.session_state["current_response"]:
        st.markdown(f"""
            <div class="result-card">
                <h3 style="color: #ff007f;">Simulation Run: {st.session_state['current_response']['scenario']}</h3>
                <p style="line-height: 1.6; color: #f1f5f9;">{st.session_state['current_response']['response']}</p>
            </div>
        """, unsafe_allow_html=True)
