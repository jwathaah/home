import streamlit as st
import time

# ==========================================
# 1. إعدادات الصفحة (يجب أن تكون دائماً في أول سطر)
# ==========================================
st.set_page_config(
    page_title="المنصة المركزية لإدارة المحتوى",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. الاستدعاءات (Imports)
# ==========================================
# ملاحظة: نفترض وجود المجلدات core و ui كما هو في نسختك الأصلية
try:
    from core.auth import login_user, get_current_user
    from ui.layout import render_sidebar, render_footer
    # استدعاء المودلز لجلب الإحصائيات (تأكد من وجود backend.py)
    from backend import UserModel, SectionModel, ContentModel, ROLE_NAMES
except ImportError as e:
    st.error(f"هناك ملفات مفقودة في المشروع. تأكد من وجود core/auth.py و backend.py. \n\nError: {e}")
    st.stop()

# ==========================================
# 3. دوال مساعدة (Optimized Helpers)
# ==========================================

# تحسين الأداء: تخزين الإحصائيات في الكاش لمدة 60 ثانية لتقليل الضغط على قاعدة البيانات/Google Sheets
@st.cache_data(ttl=60)
def load_dashboard_stats():
    """جلب إحصائيات سريعة للوحة التحكم"""
    try:
        users = UserModel.get_all_users()
        active_users = len([u for u in users if u.status == 'active'])
        
        # محاولة جلب الأقسام والمحتوى إذا كانت الدوال موجودة
        try:
            sections_count = len(SectionModel.get_all_sections())
        except:
            sections_count = 0
            
        try:
            # افتراض وجود دالة لجلب كل المحتوى أو جلبه بطريقة أخرى
            # هنا مثال بسيط، يمكن تعديله حسب هيكلية ContentModel لديك
            content_count = 0 
            # content_count = len(ContentModel.get_all_content()) 
        except:
            content_count = 0
            
        return {
            "total_users": len(users),
            "active_users": active_users,
            "sections": sections_count,
            "content": content_count
        }
    except Exception as e:
        # في حال حدوث خطأ في الاتصال، نعيد أصفار لتجنب توقف الموقع
        return {"total_users": 0, "active_users": 0, "sections": 0, "content": 0}

def init_session():
    """تهيئة متغيرات الجلسة"""
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

# ==========================================
# 4. المنطق الرئيسي (Main Logic)
# ==========================================

def main():
    init_session()
    user = get_current_user()

    # --- السيناريو 1: المستخدم غير مسجل دخول ---
    if not user:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.write("") 
            st.write("") 
            st.markdown("## 🔐 تسجيل الدخول للنظام")
            st.info("يرجى إدخال بيانات حسابك للمتابعة")
            
            with st.form("login_form"):
                email = st.text_input("البريد الإلكتروني", placeholder="example@domain.com")
                password = st.text_input("كلمة المرور", type="password")
                submitted = st.form_submit_button("دخول", use_container_width=True)
                
                if submitted:
                    if not email or not password:
                        st.warning("⚠️ الرجاء تعبئة جميع الحقول!")
                    else:
                        with st.spinner("جارٍ التحقق من البيانات..."):
                            success, msg = login_user(email, password)
                            if success:
                                st.success(msg)
                                time.sleep(0.5) # مهلة بسيطة ليقرأ المستخدم الرسالة
                                st.rerun()
                            else:
                                st.error(msg)
        
        st.divider()
        st.caption("للحصول على حساب جديد، يرجى التواصل مع إدارة النظام.")

    # --- السيناريو 2: المستخدم مسجل دخول (لوحة التحكم) ---
    else:
        # 1. القائمة الجانبية
        render_sidebar()
        
        # 2. الترويسة
        role_name = ROLE_NAMES.get(user.role_id, "مستخدم")
        st.title(f"مرحباً بك، {user.name} 👋")
        st.caption(f"صلاحية الحساب: {role_name} | الحالة: نشط 🟢")
        st.markdown("---")
        
        # 3. إحصائيات النظام (Dashboard)
        # نستخدم الدالة المحسنة (Cached)
        stats = load_dashboard_stats()
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("👥 إجمالي المستخدمين", stats["total_users"], delta=f"{stats['active_users']} نشط")
        with c2:
            st.metric("📂 الأقسام", stats["sections"])
        with c3:
            st.metric("📄 المحتوى المنشور", stats["content"] if stats["content"] > 0 else "-")
        with c4:
            st.metric("📅 تاريخ تسجيلك", user.created_at[:10] if hasattr(user, 'created_at') else "-")

        st.markdown("---")
        
        # 4. وصول سريع (Quick Actions)
        st.subheader("🚀 وصول سريع")
        qc1, qc2, qc3 = st.columns(3)
        
        with qc1:
            with st.container(border=True):
                st.markdown("#### 📂 تصفح الأقسام")
                st.write("استعراض المحتوى والملفات المتاحة.")
                if st.button("الذهاب للأقسام", key="btn_go_sections", use_container_width=True):
                    st.switch_page("pages/01_الاقسام.py")
                    
        with qc2:
            with st.container(border=True):
                st.markdown("#### 🖼️ مكتبة الوسائط")
                st.write("رفع واستعراض الصور والملفات.")
                if st.button("الذهاب للمكتبة", key="btn_go_media", use_container_width=True):
                    st.switch_page("pages/03_Media_Upload.py")
        
        # إظهار زر الإدارة فقط للمدراء
        if user.role_id in [1, 2]: # Assuming 1 & 2 are Admin roles based on constants
            with qc3:
                with st.container(border=True):
                    st.markdown("#### ⚙️ إدارة النظام")
                    st.write("التحكم بالمستخدمين والإعدادات.")
                    if st.button("لوحة التحكم", key="btn_go_admin", use_container_width=True):
                        st.switch_page("pages/02_ادارة_النظام.py")

        # 5. التذييل
        render_footer()

if __name__ == "__main__":
    main()
