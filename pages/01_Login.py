import streamlit as st
from frontend import login_user, apply_custom_style

st.set_page_config(page_title="دخول", layout="centered")
apply_custom_style()

st.title("🔐 تسجيل الدخول")
email = st.text_input("البريد")
password = st.text_input("كلمة المرور", type="password")

if st.button("دخول", type="primary"):
    ok, msg = login_user(email, password)
    if ok:
        st.success(msg)
        st.switch_page("app.py")
    else:
        st.error(msg)
