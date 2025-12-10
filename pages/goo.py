import streamlit as st
import time

# الرابط المراد التحويل إليه
url = "https://script.google.com/macros/s/AKfycbwL17vYpI50BPZDdksY7bLrb60jswu-lebvLmWPmMO5b7Q62lzgXMeerunOQDN4MFrJ/exec"

st.write("سيتم تحويلك بعد ثانية...")

# الانتظار
time.sleep(1)

# التحويل
st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={url}" />
""", unsafe_allow_html=True)
