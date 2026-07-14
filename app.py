import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client

# --- 1. SYSTEM CONFIGURATION ---
SYSTEM_PROMPT = (
    "You are the Sovereign What-If Simulation Engine. "
    "Your goal is human resilience and technical survival. "
    "Analyze crises by identifying physical bottlenecks, testing cascading probabilities, "
    "and providing practical, offline-capable, local-hardware solutions."
)

MODEL_OPTIONS = ["gemini-3.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

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

# --- 2. AUTHENTICATION FUNCTIONS (SUPABASE BACKEND) ---
def check_user(username, password):
    try:
        # Search for the user in Supabase
        response = supabase.table("vantux_users").select("*").eq("username", username).execute()
        user_data = response.data
        if user_data:
            # Check if password matches (Using plain text for quick setup; can hash later!)
            if user_data[0]["password"] == password:
                return {"status": True, "name": user_data[0]["full_name"]}
        return {"status": False, "message": "Username/password is incorrect"}
    except Exception as e:
        return {"status": False, "message": f"Database error: {str(e)}"}

def register_user(username, full_name, password):
    try:
        # Check if username already exists
        exists = supabase.table("vantux_users").select("username").eq("username", username).execute()
        if exists.data:
            return {"status": False, "message": "Username already exists!"}
        
        # Insert new user row
        supabase.table("vantux_users").insert({
            "username": username,
            "full_name": full_name,
            "password": password
        }).execute()
        return {"status": True, "message": "Account created successfully! Switch to 'Login' to enter."}
    except Exception as e:
        return {"status": False, "message": f"Registration failed: {str(e)}"}

# --- 3. SESSION STATE HANDLING ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

# --- 4. THE UI ---
st.title("Vantux Sovereign Engine")

if not st.session_state["logged_in"]:
    # Auth portal
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
                st.rerun()
            else:
                st.error(result["message"])

else:
    # --- 5. THE UNLOCKED ENGINE ---
    st.sidebar.success(f"Welcome, {st.session_state['user_name']}!")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.rerun()

    st.write("### Welcome to the offline-ready strategy simulator for Vantux Corporation.")
    
    selected_model = st.selectbox("Select Sovereign Brain Core:", MODEL_OPTIONS)
    scenario = st.text_area("Describe the crisis or scenario to simulate:", placeholder="e.g., Grid collapse in Port Harcourt...")

    if st.button("Run Simulation"):
        if not scenario.strip():
            st.warning("Please enter a scenario first.")
        else:
            with st.spinner("Sovereign Engine compiling probabilities..."):
                try:
                    model = genai.GenerativeModel(
                        model_name=selected_model,
                        system_instruction=SYSTEM_PROMPT
                    )
                    response = model.generate_content(scenario)
                    st.subheader("Simulation Analysis & Resolution Plan")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Engine Throttled: {str(e)}")
