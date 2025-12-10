import streamlit as st
import time

# الرابط المراد التحويل إليه
url = "https://script.google.com/macros/s/AKfycbyDqwvgm3FIh7dpLvuQu5E9Oy4azShwNAjdpjbSRnjuhKA6HPV9Lc_KY2m8_egETUWC/exec"

st.write("سيتم تحويلك بعد ثانية...")

# الانتظار
time.sleep(1)

# التحويل
st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={url}" />
""", unsafe_allow_html=True)
