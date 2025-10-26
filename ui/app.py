import os
import sys
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

load_dotenv()

from supervisor.supervisor_agent import SupervisorAgent

st.set_page_config(page_title="Loan Navigator Chat", layout="wide")

# -----------------------------
# Session state
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "context" not in st.session_state:
    st.session_state.context = {}

if "missing_fields" not in st.session_state:
    st.session_state.missing_fields = []

# Initialize agent
agent = SupervisorAgent()

# -----------------------------
# Helper: Submit user input
# -----------------------------
def submit_message():
    user_text = st.session_state.user_input.strip()
    if not user_text:
        return

    st.session_state.chat_history.append({"role": "user", "message": user_text})

    # Extract context from user input if missing_fields are present
    for field in st.session_state.missing_fields:
        if f"{field}:" in user_text:
            try:
                value = user_text.split(":")[1].strip()
                st.session_state.context[field] = value
            except IndexError:
                pass

    # Call agent
    response = agent.handle_query(user_text, context=st.session_state.context)
    st.session_state.chat_history.append({"role": "agent", "message": response["answer"]})

    # Update missing_fields for next turn
    st.session_state.missing_fields = response.get("missing_fields", [])

    # Clear input
    st.session_state.user_input = ""

# -----------------------------
# Chat UI
# -----------------------------
chat_box = st.empty()
input_col = st.empty()

with chat_box.container():
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f"**You:** {chat['message']}")
        else:
            st.markdown(f"**Agent:** {chat['message']}")

with input_col.container():
    st.text_input(
        "Type your message here...",
        key="user_input",
        on_change=submit_message,
        placeholder="Enter message and press Enter..."
    )

# Show missing fields prompt
if st.session_state.missing_fields:
    st.warning(
        f"Missing info: {', '.join(st.session_state.missing_fields)}. "
        f"Please provide them in the format field_name: value."
    )
