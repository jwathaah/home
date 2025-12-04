import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta
import hashlib
from models.user_model import UserModel
from models.session_model import SessionModel

def get_manager():
    return stx.CookieManager(key="auth_manager_key")

def hash_password(password):
    return hashlib.sha256(str(password).encode()).hexdigest()

def login_user(username, password):
    """
    تسجيل الدخول باستخدام اسم المستخدم فقط.
    """
    # توحيد اسم المستخدم قبل البحث
    username = str(username).strip().lower()

    user, stored_hash = UserModel.get_user_by_username(username)

    if user and stored_hash and stored_hash == hash_password(password):
        if user.is_active:
            st.session_state['user'] = user
            st.session_state['needs_new_session'] = True
            return True, "تم تسجيل الدخول بنجاح"
        else:
            return False, "هذا الحساب غير نشط"

    return False, "اسم المستخدم أو كلمة المرور غير صحيحة"

def logout_user():
    try:
        cookie_manager = get_manager()
        token = cookie_manager.get('auth_token')
        if token:
            SessionModel.delete_session(token)
        cookie_manager.delete('auth_token')
    except Exception:
        # تحمّل أي خطأ في الكوكيز بدون كسر التطبيق
        pass

    if 'user' in st.session_state:
        del st.session_state['user']
    st.rerun()

def get_current_user():
    cookie_manager = None
    stored_token = None
    try:
        cookie_manager = get_manager()
        stored_token = cookie_manager.get('auth_token')
    except Exception:
        # بعض الأنماط قد ترفع استثناء قبل تحميل الكوكيز — امنع الكسر
        stored_token = None

    # إذا المستخدم موجود بالجلسة
    if 'user' in st.session_state:
        user = st.session_state['user']
        if st.session_state.get('needs_new_session'):
            new_token = SessionModel.create_session(user.user_id)
            try:
                expires = datetime.now() + timedelta(days=30)
                if cookie_manager:
                    cookie_manager.set('auth_token', new_token, expires_at=expires)
            except Exception:
                # تجاهل أخطاء الكتابة على الكوكيز
                pass
            del st.session_state['needs_new_session']
        return user

    # فحص التوكن من الكوكيز (إذا وجد)
    if stored_token:
        user_id = SessionModel.get_user_id_by_token(stored_token)
        if user_id:
            all_users = UserModel.get_all_users()
            user = next((u for u in all_users if u.user_id == user_id), None)
            if user and user.is_active:
                st.session_state['user'] = user
                return user

    return None
