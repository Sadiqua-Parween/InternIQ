"""
InternIQ Streamlit User Interface
Owner: Samriddhi Raj (Team HumanBot)
Status: Interface Stub
"""

import streamlit as st


def main():
    st.set_page_config(page_title="InternIQ - Internship Assistant", layout="wide")
    st.title("InternIQ: Agentic Internship Assistant")
    st.markdown(
        "Welcome to InternIQ. This interface connects the LangGraph agent core, "
        "vetting, ranking, document generation, and application tracker."
    )
    st.info("System is initializing. Core verification modules are fully active.")


if __name__ == "__main__":
    main()
