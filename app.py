import streamlit as st

# إعداد الصفحة
st.set_page_config(
    page_title="اهلا وغلا",
    page_icon="🏠",
    layout="centered"
)

# تنسيق CSS للمربعات
st.markdown("""
    <style>
    .card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        transition: 0.2s;
    }
    .card:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
    }
    a {
        text-decoration: none !important;
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)



st.markdown("---")

# ======== القائمة الرئيسية ========

links = [
    ("📑 بلاغاتي",
     "https://script.google.com/macros/s/AKfycbwgYz-2HGU1Ofo7vt4--ISAZCofFH_Ef9Baxpksqnj_s7cqShX3sy1NMwYJyLGr1zhCGA/exec"),

    ("📅 التقويم الدراسي",
     "https://sites.google.com/jwatha.com/eid"),

    ("🌙 إمساكية ومقارنة رمضان",
     "https://sites.google.com/jwatha.com/emsak/"),

    ("👪 شجرة الأسرة",
     "https://joghaiman.streamlit.app/%D8%B4%D8%AC%D8%B1%D8%A9_%D8%A7%D9%84%D8%B9%D8%A7%D8%A6%D9%84%D8%A9"),

    ("📇 معالج جهات الاتصال",
     "https://sites.google.com/jwatha.com/contact/"),

    ("💬 جهات الاتصال للواتس",
     "https://sites.google.com/jwatha.com/contacts/"),
]

for title, link in links:
    st.markdown(
        f"<a href='{link}' target='_blank'>"
        f"<div class='card'>{title}</div>"
        f"</a>",
        unsafe_allow_html=True
    )

st.markdown("---")

# ======== البقية ========

st.markdown("### خدمات أخرى")

other_links = [
    ("🏡 المنزل الذكي",
     "https://script.google.com/macros/s/AKfycbwmyBe53Xhw5RuJxL60k7nE3BXb2wsYSVqCEO4jaeo_Xjt0mMMsM0IwO_xvgkizOaTO/exec"),

    ("🍽️ قائمة الطعام",
     "https://script.google.com/macros/s/AKfycbzJV83UzzjiFLaaWqon3jtTXWXUWEmzbiFN92MhDi50JodQKSK6scgDWpKm5AEXCEfM/exec"),
]

for title, link in other_links:
    st.markdown(
        f"<a href='{link}' target='_blank'>"
        f"<div class='card'>{title}</div>"
        f"</a>",
        unsafe_allow_html=True
    )
