import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta
import hashlib
from models.user_model import UserModel
from models.session_model import SessionModel

# ---------------------------------------------------------
# المدير الوحيد للكوكيز (يتم استدعاؤه مرة واحدة فقط)
# ---------------------------------------------------------
def get_manager():
    # نستخدم مفتاحاً واحداً ثابتاً لمنع تكرار العناصر
    return stx.CookieManager(key="auth_manager_key")

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# ---------------------------------------------------------
# دالة تسجيل الدخول (منطق فقط - بدون كوكيز)
# ---------------------------------------------------------
def login_user(username, password):
    """
    تقوم فقط بالتحقق من البيانات وتحديث الذاكرة المؤقتة.
    مهمة حفظ الكوكيز ستتولاها دالة get_current_user تلقائياً.
    """

    # جلب المستخدم عبر اسم المستخدم
    user, stored_hash = UserModel.get_user_by_username(username)

    if user and stored_hash == hash_password(password):
        if user.is_active:
            # 1. تحديث الذاكرة الحالية
            st.session_state['user'] = user
            
            # 2. وضع علامة أننا نحتاج لإنشاء جلسة (سيلتقطها الكود الآخر)
            st.session_state['needs_new_session'] = True
            
            return True, "تم تسجيل الدخول بنجاح"
        else:
            return False, "هذا الحساب غير نشط"

    return False, "اسم المستخدم أو كلمة المرور غير صحيحة"

# ---------------------------------------------------------
# دالة تسجيل الخروج
# ---------------------------------------------------------
def logout_user():
    # نحتاج المدير هنا للحذف
    cookie_manager = get_manager()
    
    # محاولة الحذف من القاعدة
    token = cookie_manager.get('auth_token')
    if token:
        SessionModel.delete_session(token)
    
    # الحذف من المتصفح
    cookie_manager.delete('auth_token')
    
    # تنظيف الذاكرة
    if 'user' in st.session_state:
        del st.session_state['user']
    
    st.rerun()

# ---------------------------------------------------------
# الدالة الرئيسية: قلب النظام النابض
# ---------------------------------------------------------
def get_current_user():
    """
    هذه الدالة تقوم بكل شيء:
    1. تتحقق من الذاكرة.
    2. تقرأ الكوكيز للدخول التلقائي.
    3. تكتب الكوكيز إذا سجلت الدخول للتو.
    """
    
    # 1. استدعاء مدير الكوكيز (مرة واحدة في الصفحة)
    cookie_manager = get_manager()
    
    # انتظار تحميل الكوكيز لتجنب الصفحة البيضاء
    stored_token = cookie_manager.get('auth_token')

    # -------------------------------------------
    # السيناريو أ: المستخدم موجود في الذاكرة (مسجل دخول حالياً)
    # -------------------------------------------
    if 'user' in st.session_state:
        user = st.session_state['user']
        
        # هل نحتاج لإنشاء جلسة جديدة؟ (جاء من login_user)
        if st.session_state.get('needs_new_session'):
            # إنشاء توكن جديد في القاعدة
            new_token = SessionModel.create_session(user.user_id)
            
            # زرع الكوكيز في المتصفح
            expires = datetime.now() + timedelta(days=30)
            cookie_manager.set('auth_token', new_token, expires_at=expires)
            
            # إزالة العلامة
            del st.session_state['needs_new_session']
            
        return user

    # -------------------------------------------
    # السيناريو ب: المستخدم غير موجود في الذاكرة (فحص الكوكيز)
    # -------------------------------------------
    if stored_token:
        # وجدنا كوكيز! لنتحقق من صحته
        user_id = SessionModel.get_user_id_by_token(stored_token)
        
        if user_id:
            # التوكن صحيح، لنجلب بيانات المستخدم
            all_users = UserModel.get_all_users()
            user = next((u for u in all_users if u.user_id == user_id), None)
            
            if user and user.is_active:
                # إعادة تسجيل الدخول في الذاكرة
                st.session_state['user'] = user
                return user
    
    return None
