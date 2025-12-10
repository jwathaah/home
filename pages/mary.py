import streamlit as st
import time

# الرابط المراد التحويل إليه
url = "https://script.google.com/macros/s/AKfycbzTPA1yv4Bbkb40hosp_XxcNxbn5tCPUYtpPeeLi24ugWL34IwoNOPwhEJvurl6c24GQA/exec"

st.write("سيتم تحويلك بعد ثانية...")

# الانتظار
time.sleep(1)

# التحويل
st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={url}" />
""", unsafe_allow_html=True)
