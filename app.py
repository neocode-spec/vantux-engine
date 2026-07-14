import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Oremi", page_icon="✨", layout="wide")

# --- 2. CSS DESIGN SYSTEM (Added 'galaxy-spin' Animation) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #0a192f, #020c1b, #000000); color: #e2e8f0; }
    section[data-testid="stSidebar"] { background-color: #0a192f !important; border-right: 1px solid #1e3a8a; }
    textarea, input { background-color: #0f172a !important;
