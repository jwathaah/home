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
        # 1. عرض الشريط العلوي الجديد (بدلاً من الجانبي)
        bk.render_header() 

        # 2. بقية المحتوى كما هو...
        # (يمكنك حذف الترحيب القديم st.title لأنه موجود الآن في الهيدر، أو تركه حسب رغبتك)
        # st.title(f"مرحباً بك، {user.name} 👋") <--- يمكن حذف هذا السطر لتجنب التكرار
        
        st.markdown("### 📊 نظرة عامة")
        
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
            if st.button("🛠️ مهام العمل", use_container_width=True): st.switch_page("pages/05_المهام.py")
        with qc3:
            if st.button("⚙️ الإدارة", use_container_width=True):
                 if user.role_id in [bk.ROLE_SUPER_ADMIN, bk.ROLE_ADMIN]:
                     st.switch_page("pages/02_ادارة_النظام.py")
                 else:
                     st.warning("غير مصرح")
if __name__ == "__main__":
    main()
