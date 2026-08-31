import streamlit as st
from groq import Groq
from supabase import create_client, Client
import json
import uuid
import bcrypt
import re
import base64
import random
from datetime import datetime, timedelta, timezone

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Libra", page_icon="✨", layout="wide")

# --- 2. PROFESSIONAL LIBRA DESIGN SYSTEM (CUSTOM CSS) ---
st.markdown("""
    <style>
    /* Overall Background and Text — neutral charcoal, Claude-style */
    .stApp {
        background: #1a1a1a;
        color: #e5e5e3;
    }
    .main .block-container {
        padding-bottom: 100px;
        padding-top: 40px;
        max-width: 820px;
    }

    /* Sidebar Styling — neutral, quiet */
    section[data-testid="stSidebar"] {
        background-color: #171717 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Input Box focus and styling — neutral, thin border */
    textarea, input {
        background-color: #262624 !important;
        color: #e5e5e3 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
    }
    textarea:focus, input:focus {
        border-color: rgba(255, 255, 255, 0.18) !important;
        box-shadow: none !important;
    }

    /* Flat neutral buttons by default — no gradient, no glow */
    div.stButton > button {
        background: #2a2a28 !important;
        color: #e5e5e3 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding: 10px 24px !important;
        font-weight: 500 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        transition: background 0.2s ease !important;
    }
    div.stButton > button:hover {
        background: #38372f !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* Save / positive actions — small green accent, only here */
    div.stButton > button[key*="memory"], div.stButton > button[key*="save"] {
        background: #123a24 !important;
        border-color: rgba(34, 197, 94, 0.25) !important;
    }
    div.stButton > button[key*="memory"]:hover, div.stButton > button[key*="save"]:hover {
        background: #16512f !important;
    }

    /* Delete buttons — small red accent, only here */
    div.stButton > button[key*="delete"], div.stButton > button[key*="delmem"] {
        background: #3a1616 !important;
        border-color: rgba(239, 68, 68, 0.25) !important;
    }
    div.stButton > button[key*="delete"]:hover, div.stButton > button[key*="delmem"]:hover {
        background: #4c1c1c !important;
    }

    /* Message blocks — plain, neutral, no bright colored borders */
    .chat-bubble-user {
        background: #262624;
        padding: 14px 16px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    .chat-bubble-user p { margin: 0 0 10px 0; }
    .chat-bubble-user p:last-child { margin-bottom: 0; }

    .chat-bubble-model {
        background: transparent;
        padding: 14px 4px;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .chat-bubble-model p { margin: 0 0 10px 0; }
    .chat-bubble-model p:last-child { margin-bottom: 0; }

    .msg-action-btn {
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #8a8a86;
        font-size: 12px;
        padding: 3px 10px;
        border-radius: 6px;
        cursor: pointer;
        margin-top: 6px;
    }
    .msg-action-btn:hover {
        color: #e5e5e3;
        border-color: rgba(255, 255, 255, 0.25);
    }

    /* Sparkle signature — the one place color stays vivid, as the brand mark */
    .libra-sparkle {
        font-size: 40px;
        background: linear-gradient(90deg, #7c3aed 0%, #b91c1c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        line-height: 1;
    }
    .libra-sparkle-small {
        font-size: 28px;
        background: linear-gradient(90deg, #7c3aed 0%, #b91c1c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        line-height: 1;
    }

    /* Greeting screen */
    .greeting-wrap {
        text-align: center;
        padding: 60px 0 30px 0;
    }
    .greeting-text {
        font-size: 24px;
        font-weight: 500;
        color: #e5e5e3;
        margin-top: 18px;
    }
    .greeting-sub {
        font-size: 15px;
        color: #8a8a86;
        margin-top: 6px;
    }

    /* Model version tag — greyed out, de-emphasized */
    .model-version-tag {
        font-size: 11px;
        color: #6b7280;
        letter-spacing: 0.5px;
        margin-top: 4px;
        text-align: center;
    }

    /* Chat bar styled as a rounded pill — positioning left to Streamlit's own
       sidebar-aware layout so it never gets obstructed when the sidebar opens */
    div[data-testid="stChatInput"] {
        padding-bottom: 16px;
    }
    div[data-testid="stChatInput"] > div {
        border-radius: 30px !important;
        background: #262624 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding: 10px 18px !important;
        max-width: 820px;
        width: 100%;
        margin: 0 auto;
        outline: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stChatInput"] > div:focus-within {
        border-color: rgba(255, 255, 255, 0.08) !important;
        outline: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stChatInput"] textarea {
        border-radius: 30px !important;
        border: none !important;
        background: transparent !important;
        font-size: 17px !important;
        min-height: 46px !important;
        outline: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stChatInput"] textarea:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    /* Custom scrollbar — dark and thin instead of the OS accent-colored default */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.25);
    }

    /* ADDED: markdown table rendering support (fixes raw "|---|---|" pipe text) */
    .libra-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 14px;
    }
    .libra-table th, .libra-table td {
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 8px 10px;
        text-align: left;
        vertical-align: top;
    }
    .libra-table th {
        background: #262624;
        font-weight: 600;
    }
    .libra-table tr:nth-child(even) td {
        background: rgba(255, 255, 255, 0.02);
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
    "- You have live web search access through your built-in tools. Use it whenever the topic touches "
    "current events, prices, regulations, or anything time-sensitive — ground your reasoning in what you "
    "actually find, not assumptions.\n"
    "- Do NOT append generic disclaimers like 'this is based on my training knowledge and may not reflect "
    "current reality' — you have live search, so when you use it, present your findings with earned "
    "confidence. Only flag uncertainty about a specific fact you genuinely could not verify, never as a "
    "blanket closing statement.\n"
    "- Apply this discipline uniformly across every domain — a small business plan deserves the same rigor "
    "as a space mission or an ocean engineering proposal.\n"
    "- Candidness is not cruelty: be direct and unsparing about weaknesses, but always pair criticism with "
    "actionable paths forward in the brainstorm step.\n"
    "- You are a simulation and thinking partner, not an oracle. Present probabilities and scenarios, never "
    "guarantees.\n"
    "- Keep responses tight. Each of the four steps should be a few sentences, not paragraphs, unless the "
    "user explicitly asks for depth. Cut filler, cut repetition, cut restating the question back. Say the "
    "sharpest version of the point once.\n\n"

    "MEMORY BEHAVIOR: If the user explicitly asks you to remember, save, store, keep in mind, or not forget a fact, "
    "the application will save that fact to their persistent Libra memory automatically. When the application "
    "confirms that it was saved, acknowledge it naturally and briefly. Do not claim that something was saved unless "
    "the application has confirmed the save. Never silently save unrelated personal details from ordinary conversation."
)

# Model options — display names carry no vendor branding.
# Omini and Omini+ are fast plain models. Omini Ultra uses advanced reasoning.
MODEL_OPTIONS = {
    "Omini": "openai/gpt-oss-20b",
    "Omini+": "openai/gpt-oss-120b",
    "Omini Ultra": "groq/compound"
}
MODEL_VERSION = "v1.1"

# Fallback (no live search) used only if the grounded call above hits a limit —
# keeps Libra answering instead of just refusing.
FALLBACK_MODEL = "openai/gpt-oss-120b"
# Initialize Groq client from Secrets
if "GROQ_API_KEY" in st.secrets:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("System Error: Libra Master Key missing in secrets.toml.")
    groq_client = None

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
            stored_password = user_data[0]["password"]
            record = user_data[0]

            # Existing accounts from before payments existed won't have a reference yet
            payment_ref = record.get("payment_reference")
            if not payment_ref:
                payment_ref = f"LIBRA-{username.upper()[:10]}"
                supabase.table("vantux_users").update({"payment_reference": payment_ref}).eq("username", username).execute()

            # Bcrypt hashes always start with "$2" — detect old plain-text accounts
            if stored_password.startswith("$2"):
                # Already hashed — verify normally
                if bcrypt.checkpw(password.encode(), stored_password.encode()):
                    return {
                        "status": True,
                        "name": record["full_name"],
                        "username": record["username"],
                        "subscription_status": record.get("subscription_status") or "unpaid",
                        "subscription_expires_at": record.get("subscription_expires_at"),
                        "payment_reference": payment_ref
                    }
            else:
                # Legacy plain-text account — verify the old way, then upgrade silently
                if stored_password == password:
                    new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    supabase.table("vantux_users").update({"password": new_hash}).eq("username", username).execute()
                    return {
                        "status": True,
                        "name": record["full_name"],
                        "username": record["username"],
                        "subscription_status": record.get("subscription_status") or "unpaid",
                        "subscription_expires_at": record.get("subscription_expires_at"),
                        "payment_reference": payment_ref
                    }
        return {"status": False, "message": "Username/password is incorrect"}
    except Exception as e:
        return {"status": False, "message": f"Database error: {str(e)}"}

def register_user(username, full_name, password):
    try:
        exists = supabase.table("vantux_users").select("username").eq("username", username).execute()
        if exists.data:
            return {"status": False, "message": "Username already exists!"}
        
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        payment_ref = f"LIBRA-{username.upper()[:10]}"
        supabase.table("vantux_users").insert({
            "username": username,
            "full_name": full_name,
            "password": hashed_password,
            "is_premium": True,
            "subscription_status": "unpaid",
            "payment_reference": payment_ref
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
            record = user_data[0]
            return {
                "status": True,
                "name": record["full_name"],
                "username": record["username"],
                "subscription_status": record.get("subscription_status") or "unpaid",
                "subscription_expires_at": record.get("subscription_expires_at"),
                "payment_reference": record.get("payment_reference")
            }
        return {"status": False}
    except Exception:
        return {"status": False}

def clear_session_token(username):
    try:
        supabase.table("vantux_users").update({"session_token": None}).eq("username", username).execute()
    except Exception:
        pass

# --- 4bb. SUBSCRIPTION / PAYMENT FUNCTIONS ---
ADMIN_USERNAME = "murphy"  # change this to your actual login username
PAYWALL_ENABLED = False  # flip to True whenever you're ready to start charging
SUBSCRIPTION_PRICE_TEXT = "₦50,000 (first 5 business owners — full price after)"
PAYMENT_ACCOUNT_DETAILS = "Account Number: [ADD YOURS], Bank: [ADD YOURS], Name: [ADD YOURS]"

def request_payment_review(username):
    try:
        supabase.table("vantux_users").update({"subscription_status": "pending_review"}).eq("username", username).execute()
        return True
    except Exception:
        return False

def get_pending_payment_requests():
    try:
        response = supabase.table("vantux_users").select("username, full_name, payment_reference").eq("subscription_status", "pending_review").execute()
        return response.data
    except Exception:
        return []

def approve_payment(username):
    try:
        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        supabase.table("vantux_users").update({
            "subscription_status": "active",
            "subscription_expires_at": expires
        }).eq("username", username).execute()
        return True
    except Exception:
        return False

def reject_payment(username):
    try:
        supabase.table("vantux_users").update({"subscription_status": "unpaid"}).eq("username", username).execute()
        return True
    except Exception:
        return False

def has_active_access(subscription_status, subscription_expires_at):
    if subscription_status != "active":
        return False
    if not subscription_expires_at:
        return False
    try:
        expires = datetime.fromisoformat(subscription_expires_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) < expires
    except Exception:
        return False

@st.dialog("Libra access limit reached")
def show_core_limit_dialog(core_name, limit):
    st.markdown(f"### {core_name} has reached its current allowance")
    st.write(
        f"You've used all **{limit} {core_name} requests** available in the current 24-hour window. "
        "This core is reserved at this level so Libra can keep its capacity available."
    )
    st.write("### Continue with paid access")
    st.write(f"**Libra access:** {SUBSCRIPTION_PRICE_TEXT}")
    st.write(f"**Payment details:** {PAYMENT_ACCOUNT_DETAILS}")
    st.write(
        f"**Your payment reference:** `{st.session_state.get('payment_reference', 'N/A')}`"
    )
    st.caption("Include your payment reference in the transfer narration, then submit the payment for review.")

    if st.session_state.get("subscription_status") == "pending_review":
        st.info("Your payment is already under review. You'll receive access after it is confirmed.")
    else:
        if st.button("I've Paid — Notify for Review", key=f"limit_pay_{core_name}", use_container_width=True):
            if request_payment_review(st.session_state["username"]):
                st.session_state["subscription_status"] = "pending_review"
                st.rerun()

# --- 4c. USER MEMORY FUNCTIONS ---
# Users can still manage memory manually from the sidebar, but explicit
# requests such as "remember this" or "save this to memory" are now saved
# automatically. Nothing is stored silently just because it appeared in chat.
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

def extract_explicit_memory_request(user_prompt):
    """Return the fact the user explicitly asked Libra to remember, or None."""
    text = (user_prompt or "").strip()
    if not text:
        return None

    # Do not treat questions about existing memories as save requests.
    if re.search(r"\b(what|which|show|tell)\b.*\b(remember|memory|memories)\b", text, re.IGNORECASE):
        return None

    patterns = [
        r"^\s*(?:please\s+)?remember\s+(?:that\s+)?(.+?)\s*[.!?]*$",
        r"^\s*(?:please\s+)?save\s+(?:this|that|it)(?:\s+to\s+(?:my\s+)?memory)?\s*[:,-]?\s*(.+?)\s*[.!?]*$",
        r"^\s*(?:please\s+)?save\s+(?:this\s+)?(?:to\s+(?:my\s+)?memory)\s*[:,-]?\s*(.+?)\s*[.!?]*$",
        r"^\s*(?:please\s+)?store\s+(?:this|that|it)(?:\s+in\s+(?:my\s+)?memory)?\s*[:,-]?\s*(.+?)\s*[.!?]*$",
        r"^\s*(?:please\s+)?keep\s+(?:this|that)\s+in\s+mind\s*[:,-]?\s*(.+?)\s*[.!?]*$",
        r"^\s*(?:please\s+)?don(?:'|’)t\s+forget\s+(?:that\s+)?(.+?)\s*[.!?]*$",
        r"^\s*i\s+(?:want|need)\s+you\s+to\s+remember\s+(?:that\s+)?(.+?)\s*[.!?]*$",
    ]

    for pattern in patterns:
        match = re.match(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            fact = match.group(1).strip(" \t:,-")
            if fact:
                # Store a clean, human-readable fact without the command itself.
                if not fact[0].isupper():
                    fact = fact[0].upper() + fact[1:]
                return fact.rstrip(".!?") + "."
    return None

def save_explicit_memory_if_requested(username, user_prompt):
    fact = extract_explicit_memory_request(user_prompt)
    if not fact:
        return False, None

    # Avoid creating the same memory repeatedly if the user resubmits a request.
    existing = get_user_memory(username)
    if any(str(m.get("fact", "")).strip().lower() == fact.strip().lower() for m in existing):
        return True, fact

    return add_memory(username, fact), fact

# --- 4d. PER-CORE USAGE LIMITS (rolling 24h) ---
# Each Libra core has its own request allowance. The limits are intentionally
# different so the lighter core provides more room while Ultra stays reserved
# for high-value requests.
CORE_MESSAGE_LIMITS = {
    "Omini": 15,
    "Omini+": 10,
    "Omini Ultra": 5
}
CORE_WARNING_THRESHOLD = 4

def _usage_key(username, core_name):
    # Keep the existing vantux_usage_log schema unchanged. Core usage is
    # separated by storing a namespaced username value in the same table.
    return f"{username}::libra_core::{core_name}"

def get_core_usage_count(username, core_name):
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        response = (
            supabase.table("vantux_usage_log")
            .select("id")
            .eq("username", _usage_key(username, core_name))
            .gte("created_at", cutoff)
            .execute()
        )
        return len(response.data)
    except Exception:
        return 0

def log_core_usage(username, core_name):
    try:
        supabase.table("vantux_usage_log").insert({
            "username": _usage_key(username, core_name)
        }).execute()
    except Exception:
        pass

# --- 4e. MESSAGE FORMATTING (converts markdown from the model into real HTML) ---
# FIXED: previously this only handled **bold**, *italic*, and paragraph breaks.
# Markdown tables ("| col | col |" + "|---|---|" separator) were left as raw
# pipe text, which is exactly the broken rendering seen in the screenshots.
# This version detects and converts markdown tables to real <table> HTML
# before running the bold/italic/paragraph pass. Nothing else in this
# function changed.
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # symbols, pictographs, emoji blocks
    "\U00002600-\U000027BF"  # misc symbols & dingbats
    "\U0001F1E6-\U0001F1FF"  # flags
    "\uFE0F"                  # variation selector (turns preceding char into emoji-style)
    "]+"
)

def format_message(text):
    # Strip emoji glyphs the deployed font can't render (they show as a
    # tofu/box character, e.g. "2i⊠ BRAINSTORM"). This is a font-rendering
    # gap, not a network issue — safest fix is to drop them before display.
    text = EMOJI_PATTERN.sub("", text)
    # Strip Groq browser_search citation markers, e.g. "【4†L19-L23】".
    # These are internal source-span annotations meant for tool-use tracing,
    # not for the end user — leaving them in makes responses look broken/
    # garbled. Not a network issue, just raw tool metadata slipping through.
    text = re.sub(r'【[^】]*】', '', text)
    # Collapse the double spaces / stray space-before-punctuation left behind
    # once a citation marker is removed from mid-sentence.
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r' ([.,;:!?])', r'\1', text)
    lines = text.split("\n")
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect a markdown table: "| ... |" header row followed by a
        # "|---|---|" (or "|:---|:---:|" etc.) separator row.
        if (
            stripped.startswith("|")
            and i + 1 < len(lines)
            and re.match(r'^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?$', lines[i + 1].strip())
        ):
            header_cells = [c.strip() for c in stripped.strip("|").split("|")]
            table_html = ["<table class='libra-table'>"]
            table_html.append(
                "<thead><tr>" + "".join(f"<th>{c}</th>" for c in header_cells) + "</tr></thead>"
            )
            table_html.append("<tbody>")
            i += 2  # skip header + separator rows
            while i < len(lines) and lines[i].strip().startswith("|"):
                row_cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                table_html.append(
                    "<tr>" + "".join(f"<td>{c}</td>" for c in row_cells) + "</tr>"
                )
                i += 1
            table_html.append("</tbody></table>")
            out_lines.append("".join(table_html))
            continue

        out_lines.append(line)
        i += 1

    text = "\n".join(out_lines)

    # **bold** -> <strong>bold</strong> (must run before single-asterisk italics)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text, flags=re.DOTALL)
    # *italic* -> <em>italic</em> (remaining single asterisks, after bold is consumed)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text, flags=re.DOTALL)
    # Paragraph and line breaks
    text = text.replace("\n\n", "</p><p>").replace("\n", "<br>")
    # Clean up stray <br> tags immediately around table HTML
    text = re.sub(r'(<br>\s*)?(<table)', r'\2', text)
    text = re.sub(r'(</table>)(\s*<br>)?', r'\1', text)
    return text


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

# Fresh-session greeting and starter prompts.
# These are chosen once when Libra opens, so normal Streamlit reruns do not reshuffle them.
if "welcome_greeting" not in st.session_state:
    current_hour = datetime.now().hour

    if current_hour < 12:
        greeting_templates = [
            "Good morning, {name}",
            "Morning, {name}",
            "A fresh morning, {name}",
            "Good morning, {name}. Let's think.",
            "Morning, {name}. What are we testing today?"
        ]
    elif current_hour < 18:
        greeting_templates = [
            "Good afternoon, {name}",
            "Afternoon, {name}",
            "Good afternoon, {name}. Let's get into it.",
            "A fresh afternoon, {name}",
            "Afternoon, {name}. What are we working through?"
        ]
    else:
        greeting_templates = [
            "Good evening, {name}",
            "Evening, {name}",
            "Good evening, {name}. Let's think.",
            "A fresh evening, {name}",
            "Evening, {name}. What are we testing tonight?"
        ]

    st.session_state["welcome_greeting"] = random.choice(greeting_templates)
    st.session_state["welcome_subtitle"] = random.choice([
        "Where should we start today?",
        "What are we pressure-testing today?",
        "What should Libra examine with you?",
        "Bring the idea. We'll test it.",
        "What decision are we looking at?",
        "Let's see what could happen next.",
        "What are you trying to figure out?"
    ])

    prompt_pool = [
        "Pressure-test a business idea I'm considering",
        "Find the weaknesses in a plan I'm about to launch",
        "Simulate what could go wrong with a decision I'm making",
        "Compare two strategies and tell me which is stronger",
        "Stress-test my assumptions about a market",
        "Brainstorm ways to solve a problem I'm stuck on",
        "What could make this idea fail?",
        "Help me think through a difficult business decision",
        "Analyze the risks in a plan I have",
        "Test whether this opportunity is actually worth pursuing",
        "Show me the best and worst realistic outcomes",
        "Find what I'm overlooking before I commit"
    ]
    st.session_state["welcome_prompts"] = random.sample(prompt_pool, 3)

# Auto-login on page refresh: check for a valid session token in the URL
if not st.session_state["logged_in"]:
    token = st.query_params.get("token")
    if token:
        result = validate_session_token(token)
        if result["status"]:
            st.session_state["logged_in"] = True
            st.session_state["user_name"] = result["name"]
            st.session_state["username"] = result["username"]
            st.session_state["subscription_status"] = result["subscription_status"]
            st.session_state["subscription_expires_at"] = result["subscription_expires_at"]
            st.session_state["payment_reference"] = result["payment_reference"]

# --- 6. THE UI (CLEAN LOGO, SINGLE GRADIENT SPARKLE) ---
st.markdown(f"""
    <div class="logo-container">
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
                st.session_state["subscription_status"] = result["subscription_status"]
                st.session_state["subscription_expires_at"] = result["subscription_expires_at"]
                st.session_state["payment_reference"] = result["payment_reference"]
                token = str(uuid.uuid4())
                save_session_token(result["username"], token)
                st.query_params["token"] = token
                st.rerun()
            else:
                st.error(result["message"])

else:
    is_admin = st.session_state["username"] == ADMIN_USERNAME
    has_access = (not PAYWALL_ENABLED) or is_admin or has_active_access(
        st.session_state.get("subscription_status"),
        st.session_state.get("subscription_expires_at")
    )

    if not has_access:
        st.markdown(f"""
            <div class="greeting-wrap">
                <span class="libra-sparkle">✨</span>
                <div class="greeting-text">Subscription required</div>
                <div class="greeting-sub">Your access to Libra has expired or hasn't started yet.</div>
            </div>
        """, unsafe_allow_html=True)

        st.write(f"**Price:** {SUBSCRIPTION_PRICE_TEXT}")
        st.write(f"**Pay to:** {PAYMENT_ACCOUNT_DETAILS}")
        st.write(f"**Your payment reference (include this in the transfer narration):** `{st.session_state.get('payment_reference', 'N/A')}`")
        st.caption("After you pay, tap the button below. Review can take up to 24 hours.")

        current_status = st.session_state.get("subscription_status")
        if current_status == "pending_review":
            st.info("Your payment is under review. You'll get access once it's confirmed — usually within 24 hours.")
        else:
            if st.button("I've Paid — Notify for Review", use_container_width=True):
                if request_payment_review(st.session_state["username"]):
                    st.session_state["subscription_status"] = "pending_review"
                    st.rerun()

        if st.sidebar.button("System Logout", use_container_width=True):
            clear_session_token(st.session_state["username"])
            st.query_params.clear()
            st.session_state["logged_in"] = False
            st.rerun()

        st.stop()

    # --- ADMIN PANEL (only visible to the admin account, and only while paywall is active) ---
    if is_admin and PAYWALL_ENABLED:
        with st.expander("Admin — Pending Payment Approvals"):
            pending = get_pending_payment_requests()
            if pending:
                for req in pending:
                    pcol1, pcol2, pcol3 = st.columns([2, 2, 1])
                    pcol1.write(req["full_name"])
                    pcol2.code(req["payment_reference"])
                    if pcol3.button("Approve", key=f"approve_{req['username']}"):
                        approve_payment(req["username"])
                        st.rerun()
            else:
                st.caption("No pending payment requests.")

    # --- 7. THE UNLOCKED LIBRA ENGINE ---
    user_threads = load_user_chats(st.session_state["username"])

    if st.sidebar.button("Start New Conversation", use_container_width=True):
        st.session_state["active_thread_id"] = None
        st.session_state["active_thread_title"] = ""
        st.session_state["active_messages"] = []
        st.rerun()

    st.sidebar.write("### Conversation Archives")
    if user_threads:
        for thread in user_threads:
            col1, col2 = st.sidebar.columns([4, 1])
            
            preview_title = thread["scenario"][:20] + "..." if len(thread["scenario"]) > 20 else thread["scenario"]
            if col1.button(preview_title, key=f"select_{thread['id']}", use_container_width=True):
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
            
            if col2.button("×", key=f"delete_{thread['id']}", help="Delete this thread"):
                if delete_chat(thread["id"]):
                    if st.session_state["active_thread_id"] == thread["id"]:
                        st.session_state["active_thread_id"] = None
                        st.session_state["active_thread_title"] = ""
                        st.session_state["active_messages"] = []
                    st.toast("Thread deleted!")
                    st.rerun()
    else:
        st.sidebar.write("No archives found.")

    st.sidebar.write("### Teach Libra About You")
    new_fact = st.sidebar.text_input("Something Libra should remember:", key="new_memory_input", label_visibility="collapsed", placeholder="e.g. I'm building a marketplace app")
    if st.sidebar.button("Save to Memory", key="save_memory_btn", use_container_width=True):
        if new_fact.strip():
            if add_memory(st.session_state["username"], new_fact.strip()):
                st.toast("Libra will remember that.")
                st.rerun()
        else:
            st.sidebar.warning("Type something first.")

    user_memory = get_user_memory(st.session_state["username"])
    if user_memory:
        for mem in user_memory:
            mcol1, mcol2 = st.sidebar.columns([4, 1])
            preview_fact = mem["fact"][:30] + "..." if len(mem["fact"]) > 30 else mem["fact"]
            mcol1.caption(preview_fact)
            if mcol2.button("×", key=f"delmem_{mem['id']}", help="Forget this"):
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
    if not st.session_state["active_messages"]:
        greeting_text = st.session_state["welcome_greeting"].format(
            name=st.session_state["user_name"]
        )
        greeting_subtitle = st.session_state["welcome_subtitle"]
        suggestion_prompts = st.session_state["welcome_prompts"]

        st.markdown(f"""
            <div class="greeting-wrap">
                <span class="libra-sparkle">✨</span>
                <div class="greeting-text">{greeting_text}</div>
                <div class="greeting-sub">{greeting_subtitle}</div>
            </div>
        """, unsafe_allow_html=True)

        sc1, sc2, sc3 = st.columns(3)
        for col, prompt_text in zip([sc1, sc2, sc3], suggestion_prompts):
            if col.button(prompt_text, key=f"suggest_{prompt_text[:12]}", use_container_width=True):
                st.session_state["pending_prompt"] = prompt_text
                st.rerun()
    else:
        st.write(f"#### {st.session_state['active_thread_title']}")
        for i, msg in enumerate(st.session_state["active_messages"]):
            is_editing = st.session_state.get("editing_msg_index") == i

            if is_editing:
                edit_text = st.text_area("Edit your message:", value=msg["content"], key=f"edit_box_{i}", label_visibility="collapsed")
                ecol1, ecol2 = st.columns([1, 1])
                if ecol1.button("Save & Resend", key=f"save_edit_{i}", use_container_width=True):
                    st.session_state["active_messages"] = st.session_state["active_messages"][:i]
                    st.session_state["active_prompt"] = edit_text
                    st.session_state["editing_msg_index"] = None
                    st.session_state["is_thinking"] = True
                    st.rerun()
                if ecol2.button("Cancel", key=f"cancel_edit_{i}", use_container_width=True):
                    st.session_state["editing_msg_index"] = None
                    st.rerun()
                continue

            formatted = format_message(msg["content"])
            encoded = base64.b64encode(msg["content"].encode()).decode()
            copy_btn = f'<button onclick="navigator.clipboard.writeText(atob(\'{encoded}\'))" class="msg-action-btn">Copy</button>'

            if msg["role"] == "user":
                st.markdown(f'<div class="chat-bubble-user"><b>You:</b><p>{formatted}</p>{copy_btn}</div>', unsafe_allow_html=True)
                if st.button("Edit", key=f"edit_{i}"):
                    st.session_state["editing_msg_index"] = i
                    st.rerun()
            else:
                st.markdown(f'<div class="chat-bubble-model"><b>Libra:</b><p>{formatted}</p>{copy_btn}</div>', unsafe_allow_html=True)

    col_selector, col_version = st.columns([3, 1])
    with col_selector:
        selected_display_name = st.selectbox("Sovereign Core", list(MODEL_OPTIONS.keys()), label_visibility="collapsed")
        selected_model_api = MODEL_OPTIONS[selected_display_name]
    with col_version:
        st.markdown(f'<div class="model-version-tag">{MODEL_VERSION}</div>', unsafe_allow_html=True)

    pending = st.session_state.pop("pending_prompt", None)
    user_prompt = pending if pending else st.chat_input("Ask anything...")

    # Show a proactive warning as the selected core approaches its limit.
    current_core_limit = CORE_MESSAGE_LIMITS[selected_display_name]
    current_core_usage = get_core_usage_count(st.session_state["username"], selected_display_name)
    current_core_remaining = max(current_core_limit - current_core_usage, 0)

    if 0 < current_core_remaining <= CORE_WARNING_THRESHOLD:
        st.warning(
            f"{current_core_remaining} {selected_display_name} chances remaining in your current 24-hour window. "
            "Use them carefully — when this core reaches its limit, Libra will ask you to continue with paid access."
        )

    if user_prompt:
        if current_core_usage >= current_core_limit:
            show_core_limit_dialog(selected_display_name, current_core_limit)
        else:
            st.session_state["active_prompt"] = user_prompt
            st.session_state["active_core_name"] = selected_display_name
            st.session_state["is_thinking"] = True
            st.rerun()

    # Execute simulation only when the thinking flag is True
    if st.session_state["is_thinking"]:
        try:
            user_prompt = st.session_state.get("active_prompt", "")
            active_core_name = st.session_state.get("active_core_name", selected_display_name)

            # Explicit memory requests are handled by Libra itself, so the user
            # does not have to open the sidebar and teach the same fact manually.
            memory_saved, saved_memory_fact = save_explicit_memory_if_requested(
                st.session_state["username"], user_prompt
            )

            memory_facts = get_user_memory(st.session_state["username"])
            if memory_facts:
                memory_text = "\n".join([f"- {m['fact']}" for m in memory_facts])
                personalized_prompt = SYSTEM_PROMPT + (
                    f"\n\nKnown context this user has taught you about themselves "
                    f"(reference only when genuinely relevant, don't force it in):\n{memory_text}"
                )
            else:
                personalized_prompt = SYSTEM_PROMPT

            if memory_saved:
                personalized_prompt += (
                    "\n\nSYSTEM NOTE: The application successfully saved the user's explicit memory request "
                    f"to persistent memory: {saved_memory_fact} "
                    "Acknowledge this briefly and naturally. Do not expose implementation details."
                )

            groq_messages = [{"role": "system", "content": personalized_prompt}]
            for m in st.session_state["active_messages"]:
                groq_messages.append({
                    "role": "user" if m["role"] == "user" else "assistant",
                    "content": m["content"]
                })
            groq_messages.append({"role": "user", "content": user_prompt})

            search_was_limited = False
            try:
                completion_kwargs = {
                    "model": selected_model_api,
                    "messages": groq_messages
                }

                # GPT-OSS models need Groq's built-in browser_search tool explicitly
                # enabled so Libra can perform real-time web research. Compound has
                # its own built-in web tools and must not receive a tools array here.
                if selected_model_api in ("openai/gpt-oss-20b", "openai/gpt-oss-120b"):
                    completion_kwargs["tools"] = [{"type": "browser_search"}]
                    completion_kwargs["tool_choice"] = "auto"

                completion = groq_client.chat.completions.create(**completion_kwargs)
                response_text = completion.choices[0].message.content
            except Exception as inner_e:
                inner_error_text = str(inner_e)
                if "429" in inner_error_text or "rate_limit" in inner_error_text.lower() or "413" in inner_error_text or "too large" in inner_error_text.lower():
                    # Live search hit its limit — fall back to GPT-OSS 120B with browser search enabled
                    search_was_limited = True
                    fallback_kwargs = {
                        "model": FALLBACK_MODEL,
                        "messages": groq_messages
                    }
                    if FALLBACK_MODEL in ("openai/gpt-oss-20b", "openai/gpt-oss-120b"):
                        fallback_kwargs["tools"] = [{"type": "browser_search"}]
                        fallback_kwargs["tool_choice"] = "auto"
                    completion = groq_client.chat.completions.create(**fallback_kwargs)
                    response_text = completion.choices[0].message.content
                else:
                    raise

            if search_was_limited:
                response_text += (
                    "\n\n*(Note: live search hit its usage limit for this request, so this answer is "
                    "based on training knowledge only — worth double-checking any current figures.)*"
                )

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
            
            log_core_usage(st.session_state["username"], active_core_name)
            st.session_state["is_thinking"] = False
            st.session_state.pop("active_core_name", None)
            st.rerun()
        except Exception as e:
            error_text = str(e)
            st.session_state["is_thinking"] = False
            if "429" in error_text or "rate_limit" in error_text.lower() or "413" in error_text or "too large" in error_text.lower():
                st.warning("Libra is resting for a moment — we've hit today's usage limit on this core. Try a different core above, or come back in a bit and it'll be ready to go again.")
            else:
                st.error(f"Engine Throttled: {error_text}")
