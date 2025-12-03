import streamlit as st
import hashlib
from datetime import datetime
from services.google_sheets import add_row
from utils.id_generator import generate_uuid
from core.constants import TABLE_USERS, ROLE_SUPER_ADMIN, STATUS_ACTIVE

st.set_page_config(page_title="SETUP ADMIN", layout="centered")

st.error("⚠️ **صفحة طوارئ:** هذه الصفحة مخصصة لإنشاء أول حساب مدير فقط. يرجى حذف هذا الملف `pages/99_setup.py` فور الانتهاء.")

st.title("🛠 إنشاء حساب المدير الأول")

# بيانات الحساب الثابتة
email = "admin"
password = "admin"

st.info(f"سيتم إنشاء حساب بصلاحية كاملة (Super Admin) بالبيانات التالية:\n- **User:** `{email}`\n- **Pass:** `{password}`")

if st.button("🚀 اضغط هنا لإنشاء الحساب الآن", type="primary", use_container_width=True):
    
    # 1. التشفير
    password_hash = hashlib.sha256(str.encode(password)).hexdigest()
    user_id = generate_uuid()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. تجهيز البيانات (user_id, name, email, password_hash, role_id, status, created_at)
    user_data = [
        user_id,
        "Super Admin",
        email,
        password_hash,
        ROLE_SUPER_ADMIN,
        STATUS_ACTIVE,
        created_at
    ]

    # 3. الحفظ
    try:
        success = add_row(TABLE_USERS, user_data)
        if success:
            st.balloons()
            st.success("✅ تم إنشاء الحساب بنجاح!")
            st.write("---")
            st.write("### 🛑 الخطوة التالية (مهم جداً):")
            st.write("1. اذهب الآن إلى GitHub أو مجلد المشروع.")
            st.write("2. **احذف** ملف `pages/99_setup.py`.")
            st.write("3. ارجع للصفحة الرئيسية وسجل الدخول.")
        else:
            st.error("❌ حدث خطأ أثناء الحفظ في Google Sheets.")
    except Exception as e:
        st.error(f"Error: {e}")
