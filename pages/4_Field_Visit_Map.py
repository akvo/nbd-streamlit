import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(
    page_title="Field Visit Map",
    page_icon="📍",
    layout="wide"
)

st.title("Field Visit Map")

html_file = Path(__file__).parent.parent / "field_visit_map.html"

if html_file.exists():
    html_content = html_file.read_text(encoding='utf-8')
    components.html(html_content, height=750, scrolling=True)
else:
    st.warning("Field visit map not found.")
    st.info("Expected path: " + str(html_file))
