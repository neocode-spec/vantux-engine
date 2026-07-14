import google.generativeai as genai
import streamlit as st


SYSTEM_PROMPT = (
    "You are the Sovereign What-If Simulation Engine. "
    "Your goal is human resilience and technical survival. "
    "Analyze crises by identifying physical bottlenecks, testing cascading probabilities, "
    "and providing practical, offline-capable, local-hardware solutions."
)
"MODEL_OPTIONS = [
"gemini-3.5-flash",
"gemini-1.5-flash"
]
]


def run_simulation(api_key: str, model_name: str, scenario: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT,
    )
    response = model.generate_content(scenario)

    response_text = getattr(response, "text", "") or ""
    if response_text.strip():
        return response_text.strip()

    return "The model returned no visible text for this simulation."


st.set_page_config(
    page_title="Sovereign What-If Simulation Engine",
    page_icon="AI",
    layout="wide",
)

if "simulation_result" not in st.session_state:
    st.session_state.simulation_result = ""

st.title("Sovereign What-If Simulation Engine")
st.caption(
    "Explore crisis scenarios, pressure-test bottlenecks, and generate practical survival guidance."
)

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Gemini API Key", type="password")
    model_name = st.selectbox("Model", options=MODEL_OPTIONS, index=0)
    st.caption("Your API key is used only for the current session.")

scenario = st.text_area(
    "What-If Crisis Scenario",
    height=280,
    placeholder=(
        "Describe a crisis scenario to simulate. Example: A prolonged regional power "
        "outage disrupts internet access, fuel distribution, refrigeration, and fresh "
        "water pumping for 10 days."
    ),
)

if st.button("Run Simulation", type="primary", use_container_width=True):
    if not api_key.strip():
        st.warning("Enter your Gemini API key in the sidebar.")
    elif not scenario.strip():
        st.warning("Enter a crisis scenario before running the simulation.")
    else:
        try:
            with st.spinner("Running simulation..."):
                st.session_state.simulation_result = run_simulation(
                    api_key=api_key.strip(),
                    model_name=model_name,
                    scenario=scenario.strip(),
                )
        except Exception as exc:
            st.session_state.simulation_result = ""
            st.error(f"Gemini request failed: {exc}")

st.text_area(
    "Simulation Output",
    value=st.session_state.simulation_result,
    height=360,
    disabled=True,
    placeholder="The simulation result will appear here after you run it.",
)
