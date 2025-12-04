import streamlit as st
from core.auth import get_current_user, logout_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN
from utils.formatting import apply_custom_style  # استدعاء دالة التنسيق

def render_navbar(): # تم تغيير الاسم من render_sidebar ليعكس مكانه الجديد
    """رسم القائمة العلوية الموحدة وتطبيق التصميم العام"""
    
    # 1. تطبيق التصميم (CSS) فور استدعاء القائمة
    apply_custom_style()
    
    user = get_current_user()
    
    # --- التعديل هنا: إزالة with st.sidebar واستخدام الحاوية العلوية ---
    if user:
        # إنشاء حاوية للشريط العلوي
        with st.container():
            # تقسيم الشريط إلى 3 أقسام أفقية:
            # يمين (المستخدم) - وسط (روابط الإدارة) - يسار (الخروج)
            col_user, col_admin, col_logout = st.columns([2.5, 4, 1.5])

            # 1. قسم معلومات المستخدم (يمين)
            with col_user:
                from core.constants import ROLE_NAMES
                role_name = ROLE_NAMES.get(user.role_id, "مستخدم")
                # عرض الاسم والصلاحية بشكل أفقي
                st.markdown(f"**👤 {user.name}** | <span style='color:gray; font-size:0.9em'>{role_name}</span>", unsafe_allow_html=True)
                # st.caption(f"{user.email}") # تم إخفاء الإيميل لتوفير المساحة في الأعلى

            # 2. قسم لوحة الإدارة (وسط) - يظهر للمدراء فقط
            with col_admin:
                if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
                    # وضع الروابط بجانب بعضها
                    c1, c2 = st.columns(2)
                    with c1:
                        st.page_link("pages/06_اعدادات_الموقع.py", label="الإعدادات", icon="⚙️")
                    with c2:
                        st.page_link("pages/07_المستخدمين.py", label="المستخدمين", icon="👥")

            # 3. زر تسجيل الخروج (يسار)
            with col_logout:
                if st.button("🚪 خروج", use_container_width=True, key="top_nav_logout"):
                    logout_user()
        
        # خط فاصل لفصل الشريط عن محتوى الصفحة
        st.divider()

    else:
        # في حال عدم وجود مستخدم (نادر الحدوث لأن الصفحات محمية)
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
