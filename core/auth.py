import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta
import hashlib
from models.user_model import UserModel
from models.session_model import SessionModel

# 1. تحديث دالة المدير لتقبل مفتاحاً فريداً
def get_cookie_manager(key_suffix="default"):
    return stx.CookieManager(key=f"cookie_manager_{key_suffix}")

def hash_password(password):
    """تشفير كلمة المرور"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def login_user(email, password):
    """تسجيل الدخول وإنشاء كوكيز لمدة 30 يوم"""
    user, stored_hash = UserModel.get_user_by_email(email)
    
    if user and stored_hash == hash_password(password):
        if user.is_active:
            # حفظ في الذاكرة
            st.session_state['user'] = user
            
            # إنشاء توكن
            token = SessionModel.create_session(user.user_id)
            
            # --- استخدام مفتاح خاص (login) ---
            cookie_manager = get_cookie_manager(key_suffix="login")
            expires = datetime.now() + timedelta(days=30)
            cookie_manager.set('auth_token', token, expires_at=expires)
            
            return True, "تم تسجيل الدخول بنجاح"
        else:
            return False, "هذا الحساب غير نشط"
    return False, "البريد الإلكتروني أو كلمة المرور غير صحيحة"

def logout_user():
    """تسجيل الخروج وحذف الكوكيز والجلسة"""
    # --- استخدام مفتاح خاص (logout) ---
    cookie_manager = get_cookie_manager(key_suffix="logout")
    token = cookie_manager.get('auth_token')
    
    if token:
        SessionModel.delete_session(token)
    
    cookie_manager.delete('auth_token')
    
    if 'user' in st.session_state:
        del st.session_state['user']
    
    st.rerun()

def get_current_user():
    """
    جلب المستخدم الحالي
    """
    if 'user' in st.session_state:
        return st.session_state['user']
    
    # --- استخدام مفتاح خاص (getter) ---
    cookie_manager = get_cookie_manager(key_suffix="getter")
    
    # ننتظر قليلاً للتأكد من تحميل الكوكيز
    token = cookie_manager.get('auth_token')
    
    if token:
        user_id = SessionModel.get_user_id_by_token(token)
        if user_id:
            all_users = UserModel.get_all_users()
            user = next((u for u in all_users if u.user_id == user_id), None)
            
            if user and user.is_active:
                st.session_state['user'] = user
                return user
    
    return None
