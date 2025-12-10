import streamlit as st
import time

# الرابط المراد التحويل إليه
url = "https://script.google.com/macros/s/AKfycbzohEcyBXZZ-jUWTUYzDdKwfeA89ZCawAFUvKycBcKRR9e3rJUd3_sSWBokk3nIoR1j/exec"

st.write("سيتم تحويلك بعد ثانية...")

# الانتظار
time.sleep(1)

# التحويل
st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={url}" />
""", unsafe_allow_html=True)
