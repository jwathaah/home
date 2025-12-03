import streamlit as st
from core.auth import get_current_user, logout_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN

def setup_page(title="CMS Platform"):
    """إعدادات الصفحة الأساسية التي يجب أن تكون في بداية كل ملف"""
    # ملاحظة: set_page_config يجب أن تكون أول أمر في ملف الصفحة (pages/*.py)
    # لذلك لن نضعها هنا، بل سنستدعي هذه الدالة لرسم الهيدر والتحقق من الدخول
    
    # 1. التحقق من تسجيل الدخول
    user = get_current_user()
    if not user:
        st.warning("🔒 يجب عليك تسجيل الدخول للوصول إلى هذه الصفحة.")
        st.stop() # إيقاف تحميل باقي الصفحة
    
    return user

def render_sidebar():
    """رسم القائمة الجانبية الموحدة"""
    user = get_current_user()
    
    with st.sidebar:
        if user:
            st.image("assets/logo.png", width=100) if user else None # (اختياري لو عندك لوقو)
            st.markdown(f"### 👤 {user.name}")
            st.caption(f"البريد: {user.email}")
            
            st.divider()
            
            # القوائم الخاصة بالمدراء فقط
            if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
                st.markdown("##### 🛠 اختصارات الإدارة")
                st.page_link("pages/06_اعدادات_الموقع.py", label="إعدادات الموقع", icon="⚙️")
                st.page_link("pages/07_المستخدمين.py", label="إدارة المستخدمين", icon="👥")
                st.divider()

            # زر تسجيل الخروج
            if st.button("🚪 تسجيل الخروج", use_container_width=True):
                logout_user()
        else:
            st.error("غير مسجل دخول")

def render_footer():
    """تذييل الصفحة"""
    st.markdown("---")
    st.caption("© 2025 Smart Home CMS - جميع الحقوق محفوظة.")
