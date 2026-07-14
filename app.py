import streamlit as st
import google.generativeai as genai

# Define Vantux Sovereign Rules
SYSTEM_PROMPT = (
    "You are the Sovereign What-If Simulation Engine. "
    "Your goal is human resilience and technical survival. "
    "Analyze crises by identifying physical bottlenecks, testing cascading probabilities, "
    "and providing practical, offline-capable, local-hardware solutions."
)

# Corrected Gemini Model Options for 2026
MODEL_OPTIONS = [
    "gemini-3.5-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

st.title("Vantux Sovereign Engine")
st.write("Welcome to the offline-ready strategy simulator for Vantux Corporation.")

# 1. SECURE MASTER KEY (No user hurdle!)
# This checks Streamlit's backend settings for your Master Key so users don't see it
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("System Error: Vantux Core Master Key missing. Please configure it in Streamlit Secrets.")

# 2. USER INTERFACE (Clean and Simple)
selected_model = st.selectbox("Select Sovereign Brain Core:", MODEL_OPTIONS)
scenario = st.text_area("Describe the crisis or scenario to simulate:", placeholder="e.g., Grid collapse in Lagos...")

# 3. RUN SIMULATION
if st.button("Run Simulation"):
    if not scenario.strip():
        st.warning("Please enter a scenario first.")
    elif "GEMINI_API_KEY" not in st.secrets:
        st.error("Cannot run simulation without a configured master key.")
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
