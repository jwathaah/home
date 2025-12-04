import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta
import hashlib
from models.user_model import UserModel
from models.session_model import SessionModel

# إعداد مدير الكوكيز (يجب أن يكون خارج الدوال)
def get_cookie_manager():
    return stx.CookieManager()

def hash_password(password):
    """تشفير كلمة المرور"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def login_user(email, password):
    """تسجيل الدخول وإنشاء كوكيز لمدة 30 يوم"""
    user, stored_hash = UserModel.get_user_by_email(email)
    
    if user and stored_hash == hash_password(password):
        if user.is_active:
            # 1. حفظ في الذاكرة المؤقتة
            st.session_state['user'] = user
            
            # 2. إنشاء توكن جلسة وحفظه في القاعدة
            token = SessionModel.create_session(user.user_id)
            
            # 3. حفظ التوكن في متصفح المستخدم (كوكيز) لمدة 30 يوم
            cookie_manager = get_cookie_manager()
            expires = datetime.now() + timedelta(days=30)
            cookie_manager.set('auth_token', token, expires_at=expires)
            
            return True, "تم تسجيل الدخول بنجاح"
        else:
            return False, "هذا الحساب غير نشط"
    return False, "البريد الإلكتروني أو كلمة المرور غير صحيحة"

def logout_user():
    """تسجيل الخروج وحذف الكوكيز والجلسة"""
    cookie_manager = get_cookie_manager()
    token = cookie_manager.get('auth_token')
    
    if token:
        # حذف الجلسة من قاعدة البيانات
        SessionModel.delete_session(token)
    
    # حذف الكوكيز من المتصفح
    cookie_manager.delete('auth_token')
    
    # تنظيف الذاكرة
    if 'user' in st.session_state:
        del st.session_state['user']
    
    st.rerun()

def get_current_user():
    """
    جلب المستخدم الحالي سواء من الذاكرة أو من الكوكيز المحفوظة
    """
    # 1. المحاولة الأولى: من الذاكرة (سريع)
    if 'user' in st.session_state:
        return st.session_state['user']
    
    # 2. المحاولة الثانية: من الكوكيز (للدخول التلقائي)
    cookie_manager = get_cookie_manager()
    # ننتظر قليلاً لضمان تحميل مدير الكوكيز
    token = cookie_manager.get('auth_token')
    
    if token:
        # التحقق من صحة التوكن في قاعدة البيانات
        user_id = SessionModel.get_user_id_by_token(token)
        if user_id:
            # جلب بيانات المستخدم
            all_users = UserModel.get_all_users()
            user = next((u for u in all_users if u.user_id == user_id), None)
            
            if user and user.is_active:
                st.session_state['user'] = user
                return user
    
    return None
