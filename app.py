import streamlit as st
from core.auth import login_user, get_current_user
from ui.layout import render_sidebar, render_footer

# 1. إعدادات الصفحة (يجب أن تكون أول سطر)
st.set_page_config(
    page_title="المنصة المركزية لإدارة المحتوى",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. التحقق من حالة الدخول
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

user = get_current_user()

# 3. سيناريو 1: المستخدم غير مسجل دخول -> عرض شاشة الدخول
if not user:
    # تنسيق شاشة الدخول لتكون في المنتصف
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.write("") # مسافة فارغة
        st.write("") 
        st.markdown("## 🔐 تسجيل الدخول للنظام")
        st.info("يرجى إدخال بيانات حسابك للمتابعة")
        
        with st.form("login_form"):
            username = st.text_input("اسم المستخدم", placeholder="username123")
            password = st.text_input("كلمة المرور", type="password")
            submitted = st.form_submit_button("دخول", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("الرجاء تعبئة جميع الحقول!")
                else:
                    success, msg = login_user(username, password)
                    if success:
                        st.success(msg)
                        st.rerun() # إعادة تحميل الصفحة للدخول
                    else:
                        st.error(msg)
    
    st.markdown("---")
    st.caption("للحصول على حساب جديد، يرجى التواصل مع إدارة النظام.")

# 4. سيناريو 2: المستخدم مسجل دخول -> عرض لوحة التحكم
else:
    # استدعاء القائمة الجانبية الموحدة
    render_sidebar()
    
    # محتوى الصفحة الرئيسية
    st.title(f"مرحباً بك، {user.name} 👋")
    st.markdown("---")
    
    # إحصائيات سريعة (Dashboard)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="حالة النظام", value="Active 🟢")
    with col2:
        st.metric(label="الصلاحية", value=user.role_id) # يمكن تحسينها لعرض الاسم لاحقاً
    with col3:
        st.metric(label="تاريخ التسجيل", value=user.created_at[:10])
    
    st.markdown("### 🚀 الوصول السريع")
    st.info("👈 استخدم القائمة الجانبية للتنقل بين أقسام النظام وإدارة المحتوى.")
    
    # تذييل الصفحة
    render_footer()
