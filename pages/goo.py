import streamlit as st
import time

# الرابط المراد التحويل إليه
url = "https://script.google.com/macros/s/AKfycbxgbwEG71vZqLUwmtbb9nkChdD9bxGj8MBTNEuICjfoDEAPyXKCOLdWSTQOX-VtAzN8/exec"

st.write("سيتم تحويلك بعد ثانيتين...")

# الانتظار
time.sleep(2)

# التحويل
st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={url}" />
""", unsafe_allow_html=True)
