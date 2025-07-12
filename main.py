import streamlit as st
import pandas as pd
from streamlit_theme import st_theme

# Set page configuration
st.session_state.pages = {
        "Bot": [
             st.Page("./pages/ChatBot.py", title="Chatbot"),
        ]}

pg = st.navigation(st.session_state.pages)
pg.run()