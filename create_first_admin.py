import streamlit as st
import hashlib
from datetime import datetime
from services.google_sheets import add_row
from utils.id_generator import generate_uuid
from core.constants import TABLE_USERS, ROLE_SUPER_ADMIN, STATUS_ACTIVE

def create_root_user():
    # بيانات الحساب المطلوبة
    email = "admin"
    password = "admin"
    name = "Super Admin"
    
    print(f"⏳ جاري إنشاء الحساب: {email} ...")

    # 1. تشفير كلمة المرور (Hashing)
    # لا نقوم بتخزين 'admin' كنص واضح أبداً للأمان
    password_hash = hashlib.sha256(str.encode(password)).hexdigest()

    # 2. تجهيز البيانات
    user_id = generate_uuid()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ترتيب الأعمدة حسب ملف users.csv:
    # user_id, name, email, password_hash, role_id, status, created_at
    user_data = [
        user_id,
        name,
        email,
        password_hash,
        ROLE_SUPER_ADMIN,  # رقم 1
        STATUS_ACTIVE,     # active
        created_at
    ]

    # 3. الحفظ في Google Sheets
    success = add_row(TABLE_USERS, user_data)
    
    if success:
        print("\n✅✅ تم إنشاء حساب المدير بنجاح!")
        print(f"   👤 User:  {email}")
        print(f"   🔑 Pass:  {password}")
        print(" يمكنك الآن تشغيل الموقع وتسجيل الدخول.")
    else:
        print("\n❌ حدث خطأ أثناء الاتصال بقاعدة البيانات.")

if __name__ == "__main__":
    create_root_user()
