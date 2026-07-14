import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Oremi", page_icon="✨", layout="wide")

# --- 2. CSS: UNIFIED GALAXY ANIMATION ---
st.markdown("""
    <style>
    @keyframes galaxy-flow {
        0% { transform: translateY(0px) rotate(0deg); opacity: 0.8; }
        50% { transform: translateY(-5px) rotate(180deg); opacity: 1; }
        100% { transform: translateY(0px) rotate(360deg); opacity: 0.8; }
    }
    .galaxy-sparkle { display: inline-block; animation: galaxy-flow 3s ease-in-out infinite; }
    .stApp { background: radial-gradient(circle at top right, #0a192f, #020c1b, #000000); color: #e2e8f0; }
    .model-selector { background: #1e293b; padding: 10px; border-radius: 20px; border: 1px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---
if "model_choice" not in st.session_state:
    st.session_state["model_choice"] = "3.5 Flash"

# Sidebar/Header Model Toggle
st.markdown('<div class="model-selector">', unsafe_allow_html=True)
model_choice = st.radio("Select Sovereign Brain Core:", ["3.5 Flash Lite", "3.5 Flash", "3.5 Flash Pro"], horizontal=True)
st.session_state["model_choice"] = model_choice
st.markdown('</div>', unsafe_allow_html=True)

# Header with Animated Star
st.markdown(f'<h1 class="galaxy-sparkle">Oremi ✨</h1>', unsafe_allow_html=True)

# --- 4. ENGINE TRANSMISSION ---
prompt = st.text_input("Transmit scenario:")
if st.button("Transmit to Core"):
    try:
        # Map the clean names to the actual API requirements
        model_map = {
            "3.5 Flash Lite": "gemini-1.5-flash-lite", 
            "3.5 Flash": "gemini-1.5-flash",
            "3.5 Flash Pro": "gemini-1.5-pro"
        }
        model_name = model_map.get(st.session_state["model_choice"])
        
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content(prompt)
        st.write(response.text)
    except Exception as e:
        st.error(f"Transmission Error: Ensure your API keys are valid and the model string is correct. Details: {e}")
