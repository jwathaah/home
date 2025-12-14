import streamlit as st

# إعداد الصفحة
st.set_page_config(
    page_title="المنصة المركزية",
    page_icon="🏠",
    layout="wide"
)

# عنوان الصفحة
st.markdown(
    "<h1 style='text-align:center;'>🏠 المنصة المركزية</h1>"
    "<p style='text-align:center;'>اختر الخدمة التي تريد الدخول إليها</p>",
    unsafe_allow_html=True
)

st.markdown("---")

# 4 مربعات
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 📑 بلاغاتي")
    st.link_button(
        "الدخول",
        "https://script.google.com/macros/s/AKfycbwgYz-2HGU1Ofo7vt4--ISAZCofFH_Ef9Baxpksqnj_s7cqShX3sy1NMwYJyLGr1zhCGA/exec",
        use_container_width=True
    )

with col2:
    st.markdown("### 🏡 المنزل الذكي")
    st.link_button(
        "الدخول",
        "https://script.google.com/macros/s/AKfycbwiH3bco-iYo4Ut3sRTIs3gLxTVd9bqgpY-FQoTLRsJ3SApkmS7d_uTriaedmm0wHg/exec",
        use_container_width=True
    )

with col3:
    st.markdown("### 🍽️ قائمة الطعام")
    st.link_button(
        "الدخول",
        "https://script.google.com/macros/s/AKfycbzJV83UzzjiFLaaWqon3jtTXWXUWEmzbiFN92MhDi50JodQKSK6scgDWpKm5AEXCEfM/exec",
        use_container_width=True
    )

with col4:
    st.markdown("### 👪 شجرة الأسرة")
    st.link_button(
        "الدخول",
        "https://joghaiman.streamlit.app/%D8%B4%D8%AC%D8%B1%D8%A9_%D8%A7%D9%84%D8%B9%D8%A7%D8%A6%D9%84%D8%A9",
        use_container_width=True
    )
