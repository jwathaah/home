import streamlit as st
import pandas as pd
import time
from models.user_model import UserModel
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_NAMES
# 👇 التعديل هنا: استدعاء render_navbar بدلاً من render_sidebar
from ui.layout import render_navbar

# 1. إعداد الصفحة
st.set_page_config(page_title="إدارة المستخدمين", page_icon="👥", layout="wide")

# 2. التحقق من المستخدم والصلاحيات
user = get_current_user()
ALLOWED_ROLES = [ROLE_SUPER_ADMIN, ROLE_ADMIN]

if not user or user.role_id not in ALLOWED_ROLES:
    st.toast("⛔ عذراً، ليس لديك صلاحية لدخول هذه الصفحة! جارِ تحويلك...", icon="🚫")
    time.sleep(1.5)
    st.switch_page("app.py")

# 3. عرض الشريط العلوي (Navbar)
# 👇 التعديل هنا: استدعاء الدالة الجديدة وتمرير اسم الصفحة
render_navbar(current_page="pages/07_المستخدمين.py")

st.title("👥 إدارة المستخدمين والموظفين")
st.markdown("إضافة أعضاء جدد والتحكم في صلاحيات الوصول.")
st.divider()

# 4. إحصائيات سريعة
all_users = UserModel.get_all_users()
active_count = len([u for u in all_users if u.status == 'active'])

c1, c2, c3 = st.columns(3)
c1.metric("إجمالي المستخدمين", len(all_users))
c2.metric("الحسابات النشطة", active_count)
c3.metric("الحسابات الموقوفة", len(all_users) - active_count)

st.divider()

# 5. تبويبات الإدارة
tab1, tab2 = st.tabs(["📋 قائمة المستخدمين", "➕ إضافة مستخدم جديد"])

# --- تبويب 1: قائمة المستخدمين ---
with tab1:
    if not all_users:
        st.info("لا يوجد مستخدمين.")
    else:
        # تحويل البيانات لجدول عرض
        user_data = []
        for u in all_users:
            role_name = ROLE_NAMES.get(u.role_id, "غير معروف")
            status_icon = "🟢" if u.status == "active" else "🔴"
            
            user_data.append({
                "ID": u.user_id,
                "الاسم": u.name,
                "البريد الإلكتروني": u.email,
                "الدور": role_name,
                "الحالة": f"{status_icon} {u.status}",
                "تاريخ التسجيل": u.created_at
            })
        
        df = pd.DataFrame(user_data)
        st.dataframe(df, use_container_width=True)
        
        st.subheader("🛠 إجراءات على مستخدم")
        
        # اختيار مستخدم للتعديل
        user_options = {f"{u.name} ({u.email})": u for u in all_users}
        if user_options:
            selected_label = st.selectbox("اختر مستخدم للتعديل:", list(user_options.keys()))
            selected_u = user_options[selected_label]
            
            # لا نسمح بتعديل المدير العام من هنا (لحماية النظام)
            if selected_u.role_id == ROLE_SUPER_ADMIN and user.user_id != selected_u.user_id:
                 st.warning("لا يمكن تعديل حساب المدير العام الرئيسي.")
            else:
                with st.expander(f"تعديل بيانات: {selected_u.name}", expanded=True):
                    col_e1, col_e2 = st.columns(2)
                    
                    with col_e1:
                        # تعديل الحالة (تجميد/تفعيل)
                        new_status = st.selectbox(
                            "حالة الحساب", 
                            ["active", "inactive"], 
                            index=0 if selected_u.status == "active" else 1
                        )
                        if st.button("تحديث الحالة"):
                            UserModel.update_user_status(selected_u.user_id, new_status)
                            st.success("تم تحديث الحالة بنجاح!")
                            time.sleep(1)
                            st.rerun()

                    with col_e2:
                        # زر الحذف
                        st.write("منطقة الخطر ⚠️")
                        if st.button("🗑 حذف المستخدم نهائياً", type="primary"):
                            # تأكد من وجود دالة الحذف في المودل
                            if hasattr(UserModel, 'delete_user'):
                                UserModel.delete_user(selected_u.user_id)
                                st.warning(f"تم حذف المستخدم {selected_u.name}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("دالة الحذف غير موجودة في المودل")

# --- تبويب 2: إضافة مستخدم جديد ---
with tab2:
    st.header("تسجيل عضو جديد")
    with st.form("add_user_form"):
        col_new1, col_new2 = st.columns(2)
        
        with col_new1:
            u_name = st.text_input("الاسم الكامل")
            u_email = st.text_input("البريد الإلكتروني")
        
        with col_new2:
            u_pass = st.text_input("كلمة المرور", type="password")
            # قائمة الأدوار
            role_options = {v: k for k, v in ROLE_NAMES.items()}
            u_role_name = st.selectbox("الدور الوظيفي", list(role_options.keys()))
            u_role_id = role_options[u_role_name]
            
        submitted = st.form_submit_button("إضافة المستخدم")
        
        if submitted:
            if u_name and u_email and u_pass:
                success, msg = UserModel.create_user(u_name, u_email, u_pass, u_role_id)
                if success:
                    st.success(f"✅ {msg}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.error("جميع الحقول مطلوبة.")
