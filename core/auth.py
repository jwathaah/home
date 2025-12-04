import streamlit as st
import hashlib
from models.user_model import UserModel

def hash_password(password):
    """تشفير كلمة المرور (SHA256) لمطابقتها مع قاعدة البيانات"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def login_user(email, password):
    """
    دالة تسجيل الدخول:
    1. تبحث عن الايميل
    2. تتأكد أن الحساب مفعل
    3. تطابق كلمة المرور
    4. تحفظ المستخدم في الجلسة (Session)
    """
    # جلب المستخدم وكلمة المرور المشفرة
    user_obj, stored_hash = UserModel.get_user_by_email(email)
    
    if not user_obj:
        return False, "البريد الإلكتروني غير مسجل في النظام."
    
    if not user_obj.is_active:
        return False, "هذا الحساب معطل (Inactive)، يرجى مراجعة المدير."
        
    # مطابقة الباسورد
    input_hash = hash_password(password)
    
    if input_hash == stored_hash:
        # نجاح الدخول: حفظ البيانات في متصفح المستخدم
        st.session_state['logged_in'] = True
        st.session_state['current_user'] = user_obj
        return True, "تم تسجيل الدخول بنجاح!"
    else:
        return False, "كلمة المرور غير صحيحة."

def logout_user():
    """تسجيل الخروج ومسح البيانات من الذاكرة"""
    if 'logged_in' in st.session_state:
        del st.session_state['logged_in']
    if 'current_user' in st.session_state:
        del st.session_state['current_user']
    st.rerun()

def get_current_user():
    """إرجاع كائن المستخدم الحالي إذا كان مسجلاً للدخول"""
    if st.session_state.get('logged_in'):
        return st.session_state.get('current_user')
    return None
