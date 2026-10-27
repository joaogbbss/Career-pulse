import os
import streamlit as st
import streamlit.components.v1 as components
from engine.build_web_app import build_interactive_webapp

st.set_page_config(
    page_title="CareerPulse // Motor Estatístico de Carreiras",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: 100%; }
  header { visibility: hidden; }
  body { background-color: #07090e; }
</style>
""", unsafe_allow_html=True)

index_path = os.path.join("web", "index.html")
if not os.path.exists(index_path):
    build_interactive_webapp("web")

with open(index_path, "r", encoding="utf-8") as f:
    html_content = f.read()

components.html(html_content, height=920, scrolling=True)
