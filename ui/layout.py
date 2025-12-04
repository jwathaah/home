import streamlit as st
from core.auth import get_current_user, logout_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN
from utils.formatting import apply_custom_style  # استدعاء دالة التنسيق

# 👇 التعديل هنا: إضافة (current_page=None) لتقبل الدالة المتغير بدون مشاكل
def render_navbar(current_page=None):
    """رسم الشريط العلوي الموحد (بديل القائمة الجانبية)"""
    
    # 1. تطبيق التصميم (CSS)
    apply_custom_style()
    
    user = get_current_user()
    
    # نستخدم حاوية علوية بدلاً من الـ sidebar
    if user:
        with st.container():
            # تقسيم الشريط: يمين (معلومات) | وسط (روابط) | يسار (خروج)
            col_info, col_links, col_logout = st.columns([3, 5, 1.5])
            
            # 1. قسم المعلومات (يمين)
            with col_info:
                from core.constants import ROLE_NAMES
                role_name = ROLE_NAMES.get(user.role_id, "مستخدم")
                st.markdown(f"**👤 {user.name}** | <span style='color:gray; font-size:0.8em'>{role_name}</span>", unsafe_allow_html=True)
            
            # 2. قسم الروابط (وسط) - يظهر للمدراء فقط
            with col_links:
                if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
                    # عرض الروابط بجانب بعضها
                    c1, c2 = st.columns(2)
                    with c1:
                        st.page_link("pages/06_اعدادات_الموقع.py", label="الإعدادات", icon="⚙️")
                    with c2:
                        st.page_link("pages/07_المستخدمين.py", label="المستخدمين", icon="👥")
            
            # 3. قسم الخروج (يسار)
            with col_logout:
                if st.button("🚪 خروج", key="nav_logout_btn", use_container_width=True):
                    logout_user()
        
        st.divider()

    else:
        # حالة نادرة (للزوار غير المسجلين)
        pass

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
