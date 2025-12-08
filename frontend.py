import streamlit as st
import extra_streamlit_components as stx
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import hashlib
from backend import (
    UserModel, SessionModel, 
    ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_NAMES
)

# ==========================================
# 1. التنسيق (Styling) - تنسيق جمالي فقط
# ==========================================
def apply_custom_style():
    style = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
    
    /* توحيد الخط واتجاه النص */
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
    .stApp { direction: rtl; text-align: right; }
    
    /* تنسيق النصوص والعناوين لليمين */
    h1, h2, h3, h4, h5, h6, p, div, label, .stMarkdown, .stButton { text-align: right !important; }
    
    /* تحسين شكل التبويبات */
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 8px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #ff4b4b !important; color: white !important; }
    
    /* إخفاء الهيدر والهوامش الزائدة في الجوال فقط للترتيب */
    @media (max-width: 768px) {
        .block-container { padding-top: 2rem !important; }
    }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# ... (باقي دوال المصادقة والميديا كما هي دون تغيير) ...
# (انسخ باقي الدوال: get_manager, login_user, logout_user, get_current_user, render_navbar, render_social_media من ملفك السابق)
# سأضع لك الدوال باختصار لضمان عمل الكود إذا نسخت الكل:

def get_manager(): return stx.CookieManager(key="auth_manager_key")
def hash_password(p): return hashlib.sha256(str.encode(p)).hexdigest()

def login_user(email, password):
    user, stored_hash = UserModel.get_user_by_email(email)
    if user and stored_hash == hash_password(password):
        if user.is_active:
            st.session_state['user'] = user
            st.session_state['needs_new_session'] = True
            return True, "تم الدخول"
        return False, "حساب غير نشط"
    return False, "بيانات خطأ"

def logout_user():
    cm = get_manager()
    token = cm.get('auth_token')
    if token:
        SessionModel.delete_session(token)
        cm.delete('auth_token')
    if 'user' in st.session_state: del st.session_state['user']
    st.rerun()

def get_current_user():
    cm = get_manager()
    stored_token = cm.get('auth_token')
    if 'user' in st.session_state:
        user = st.session_state['user']
        if st.session_state.get('needs_new_session'):
            new_token = SessionModel.create_session(user.user_id)
            expires = datetime.now() + timedelta(days=30)
            cm.set('auth_token', new_token, expires_at=expires)
            del st.session_state['needs_new_session']
        return user
    if stored_token:
        uid = SessionModel.get_user_id_by_token(stored_token)
        if uid:
            all_users = UserModel.get_all_users()
            user = next((u for u in all_users if u.user_id == uid), None)
            if user and user.is_active:
                st.session_state['user'] = user
                return user
    return None

def render_navbar(current_page=None):
    apply_custom_style()
    user = get_current_user()
    if user:
        with st.container():
            c1, c2, c3 = st.columns([2.5, 4, 1.5])
            with c1:
                rname = ROLE_NAMES.get(user.role_id, "مستخدم")
                st.markdown(f"**👤 {user.name}** | <span style='color:gray; font-size:0.9em'>{rname}</span>", unsafe_allow_html=True)
            with c2:
                if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
                    st.page_link("pages/02_ادارة_النظام.py", label="لوحة الإدارة", icon="⚙️")
            with c3:
                if st.button("🚪 خروج", key="nav_logout", use_container_width=True): logout_user()
        st.divider()

def render_social_media(url):
    if not url: return
    st.info(f"رابط: {url}")
    st.link_button("فتح", url)
