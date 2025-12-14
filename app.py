import streamlit as st
import time
import backend as bk  # استدعاء الملف الشامل

# إعداد الصفحة
st.set_page_config(page_title="المنصة المركزية", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")

# تطبيق الستايل
bk.apply_custom_style()

def main():
    user = bk.get_current_user()

    # --- سيناريو تسجيل الدخول ---
    if not user:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("<h2 style='text-align: center;'>🔐 تسجيل الدخول</h2>", unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("البريد الإلكتروني")
                password = st.text_input("كلمة المرور", type="password")
                if st.form_submit_button("دخول", use_container_width=True):
                    ok, msg = bk.login_procedure(email, password)
                    if ok:
                        st.success(msg)
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(msg)
    
    # --- سيناريو لوحة التحكم (Dashboard) ---
    else:
        # عرض الشريط العلوي الجديد (بدلاً من الجانبي)
        bk.render_header() 

        st.markdown("### 📊 نظرة عامة")
        
        # إحصائيات سريعة
        c1, c2, c3 = st.columns(3)
        c1.metric("📂 الأقسام", len(bk.SectionModel.get_all_sections()))
        c2.metric("👥 المستخدمين", len(bk.UserModel.get_all_users()))
        c3.metric("📅 التاريخ", time.strftime("%Y-%m-%d"))

        st.markdown("### 🚀 الوصول السريع")

        # تقسيم الصفحة إلى 4 مربعات باستخدام st.columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📑 بلاغاتي", use_container_width=True):
                st.markdown(f"[فتح بلاغاتي](https://script.google.com/macros/s/AKfycbwgYz-2HGU1Ofo7vt4--ISAZCofFH_Ef9Baxpksqnj_s7cqShX3sy1NMwYJyLGr1zhCGA/exec)", unsafe_allow_html=True)

        with col2:
            if st.button("🏡 المنزل الذكي", use_container_width=True):
                st.markdown(f"[فتح المنزل الذكي](https://script.google.com/macros/s/AKfycbwiH3bco-iYo4Ut3sRTIs3gLxTVd9bqgpY-FQoTLRsJ3SApkmS7d_uTriaedmm0wHg/exec)", unsafe_allow_html=True)

        with col3:
            if st.button("🍽️ قائمة الطعام", use_container_width=True):
                st.markdown(f"[فتح قائمة الطعام](https://script.google.com/macros/s/AKfycbzJV83UzzjiFLaaWqon3jtTXWXUWEmzbiFN92MhDi50JodQKSK6scgDWpKm5AEXCEfM/exec)", unsafe_allow_html=True)

        with col4:
            if st.button("👪 شجرة الأسرة", use_container_width=True):
                st.markdown(f"[فتح شجرة الأسرة](https://joghaiman.streamlit.app/%D8%B4%D8%AC%D8%B1%D8%A9_%D8%A7%D9%84%D8%B9%D8%A7%D8%A6%D9%84%D8%A9)", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
