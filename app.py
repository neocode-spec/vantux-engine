import streamlit as st
import google.generativeai as genai
import streamlit_authenticator as stauth

# --- 1. SYSTEM CONFIGURATION ---
SYSTEM_PROMPT = (
    "You are the Sovereign What-If Simulation Engine. "
    "Your goal is human resilience and technical survival. "
    "Analyze crises by identifying physical bottlenecks, testing cascading probabilities, "
    "and providing practical, offline-capable, local-hardware solutions."
)

MODEL_OPTIONS = ["gemini-3.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

# Configure Google Gemini Master Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("System Error: Vantux Core Master Key missing.")

# --- 2. USER CREDENTIALS (Case-Insensitive Fix!) ---
credentials = {
    "usernames": {
        "believe": {
            "name": "Believe",
            "password": "2020Believe"
        },
        "Believe": {
            "name": "Believe",
            "password": "2020Believe"
        }
    }
}

# Pre-registering a test user for your friends to test
if "registered_users" not in st.session_state:
    st.session_state["registered_users"] = {
        "tester": {"name": "Vantux Tester", "password": "password123"}
    }

# Combine static credentials with newly registered users
for username, data in st.session_state["registered_users"].items():
    credentials["usernames"][username] = data

# Initialize the authenticator object
authenticator = stauth.Authenticate(
    credentials,
    cookie_name="vantux_auth_cookie",
    key="signature_key_for_cookies",
    cookie_expiry_days=30
)

# --- 3. THE GATEKEEPER UI ---
st.title("Vantux Sovereign Engine")

# Choose between Login and Registration
auth_action = st.radio("Access Portal:", ["Login", "Create Account"], horizontal=True)

if auth_action == "Create Account":
    st.subheader("Register New Vantux Account")
    new_email = st.text_input("Username / Email")
    new_name = st.text_input("Full Name")
    new_password = st.text_input("Password", type="password")
    
    if st.button("Sign Up"):
        if new_email and new_password and new_name:
            if new_email in credentials["usernames"]:
                st.error("Username already exists!")
            else:
                st.session_state["registered_users"][new_email] = {
                    "name": new_name,
                    "password": new_password
                }
                st.success("Account created successfully! Switch to 'Login' to enter.")
        else:
            st.warning("Please fill in all fields.")

elif auth_action == "Login":
    # 1. Trigger the login UI
    authenticator.login(location='main')

    # 2. Check the memory state
    if st.session_state.get("authentication_status") == False:
        st.error('Username/password is incorrect')
    elif st.session_state.get("authentication_status") == None:
        st.info('Please enter your username and password')
    elif st.session_state.get("authentication_status"):
        # --- 4. THE UNLOCKED APP (Only runs if logged in!) ---
        st.sidebar.success(f"Welcome, {st.session_state['name']}!")
        authenticator.logout('Logout', 'sidebar')
        
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
