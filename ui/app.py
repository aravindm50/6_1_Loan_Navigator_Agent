import os
import streamlit as st
from supervisor.supervisor_agent import SupervisorAgent

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(
    page_title="Loan Navigator Agent",
    layout="wide"
)

st.title("Loan Navigator Agent")
st.write("Ask any loan-related question and get instant, accurate responses.")

# Initialize Supervisor Agent
agent = SupervisorAgent()

# Sidebar: Environment info (optional)
with st.sidebar.expander("Environment Info"):
    st.write(f"CHROMA_URL: {os.getenv('CHROMA_URL', 'http://localhost:8000')}")
    st.write(f"GCP_PROJECT: {os.getenv('GCP_PROJECT', 'bdc-training')}")
    st.write(f"Vertex AI Model: {os.getenv('VERTEX_AI_MODEL', 'gemini-2.0-flash')}")

# User input
user_query = st.text_input("Enter your question:", "")

if st.button("Ask"):
    if user_query.strip() == "":
        st.warning("Please enter a question!")
    else:
        with st.spinner("Processing your request..."):
            try:
                result = agent.handle_query(user_query)
                st.success("Query processed successfully")
                
                st.subheader("Answer")
                st.write(result.get("answer", "No answer available."))

                st.subheader("Intent Detected")
                st.write(result.get("intent"))

                # Optional: Show detailed agent outputs
                if st.checkbox("Show Detailed Agent Outputs"):
                    st.json(result)

            except Exception as e:
                st.error(f"Error processing query: {e}")