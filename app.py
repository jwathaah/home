import streamlit as st
import time
import backend as bk  # استدعاء الملف الشامل

# إعداد الصفحة

st.set_page_config(page_title="المنصة المركزية", page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")

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
        # عرض القائمة الجانبية الموحدة
        bk.render_sidebar()

        st.title(f"مرحباً بك، {user.name} 👋")
        st.caption(f"الصلاحية: {user.role_name}")
        st.markdown("---")

        # إحصائيات سريعة
        c1, c2, c3 = st.columns(3)
        c1.metric("📂 الأقسام", len(bk.SectionModel.get_all_sections()))
        c2.metric("👥 المستخدمين", len(bk.UserModel.get_all_users()))
        c3.metric("📅 التاريخ", time.strftime("%Y-%m-%d"))

        st.markdown("### 🚀 وصول سريع")
        qc1, qc2, qc3 = st.columns(3)
        with qc1:
            if st.button("📂 تصفح الأقسام", use_container_width=True): st.switch_page("pages/01_الاقسام.py")
        with qc2:
            if st.button("🖼️ رفع ملفات", use_container_width=True): st.switch_page("pages/03_Media_Upload.py")
        with qc3:
            if st.button("☑️ المهام والنماذج", use_container_width=True): st.switch_page("pages/04_النماذج.py")

if __name__ == "__main__":
    main()
