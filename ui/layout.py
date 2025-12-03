import streamlit as st
from core.auth import get_current_user, logout_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN
from utils.formatting import apply_custom_style  # استدعاء دالة التنسيق

def render_sidebar():
    """رسم القائمة الجانبية الموحدة وتطبيق التصميم العام"""
    
    # 1. تطبيق التصميم (CSS) فور استدعاء القائمة
    apply_custom_style()
    
    user = get_current_user()
    
    with st.sidebar:
        if user:
            # صورة المستخدم أو الشعار (اختياري)
            # st.image("assets/logo.png", width=100)
            
            st.markdown(f"### 👤 {user.name}")
            st.caption(f"البريد: {user.email}")
            
            # عرض الدور الوظيفي بشكل جميل
            from core.constants import ROLE_NAMES
            role_name = ROLE_NAMES.get(user.role_id, "مستخدم")
            st.info(f"الصلاحية: {role_name}")
            
            st.divider()
            
            # القوائم الخاصة بالمدراء فقط
            if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
                st.markdown("##### 🛠 لوحة الإدارة")
                st.page_link("pages/06_اعدادات_الموقع.py", label="إعدادات الموقع", icon="⚙️")
                st.page_link("pages/07_المستخدمين.py", label="إدارة المستخدمين", icon="👥")
                st.divider()

            # زر تسجيل الخروج
            if st.button("🚪 تسجيل الخروج", use_container_width=True):
                logout_user()
        else:
            st.warning("غير مسجل دخول")

def render_footer():
    """تذييل الصفحة"""
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: gray; font-size: 0.8rem;">
            © 2025 Smart Home CMS | تم التطوير بواسطة فريق العمل
        </div>
        """, 
        unsafe_allow_html=True
    )
