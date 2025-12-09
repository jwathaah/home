import streamlit as st
import time

# الرابط المراد التحويل إليه
url = "https://script.google.com/macros/s/AKfycbzW09dRNF5SJR1RjdLRC1V3uQoY2lA7gjSvtNDiDA2TtVugRyXWPJSGhbXuLmvTOJ-9/exec"

st.write("سيتم تحويلك بعد ثانيتين...")

# الانتظار
time.sleep(2)

# التحويل
st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={url}" />
""", unsafe_allow_html=True)
