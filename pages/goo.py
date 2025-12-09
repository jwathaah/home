import streamlit as st
import time

# الرابط المراد التحويل إليه
url = "https://script.google.com/a/macros/jwatha.com/s/AKfycbz-th2hB4BH92aOgMyFBuJ1_TJshq73UPjLwjWbwymRziqJJx7Mg4bAmGwSXEvvJT8y/exec"

st.write("سيتم تحويلك بعد ثانيتين...")

# الانتظار
time.sleep(2)

# التحويل
st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={url}" />
""", unsafe_allow_html=True)
