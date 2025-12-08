import streamlit as st
import extra_streamlit_components as stx
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import hashlib
from backend import (
    UserModel, SessionModel, 
    ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_NAMES
)

# ==========================================
# ==========================================
# 1. التنسيق (Styling)
# ==========================================
def apply_custom_style():
    style = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
    
    /* 1. الخطوط والاتجاه العام */
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
    .stApp { direction: rtl; text-align: right; }
    
    /* 2. ضبط الشريط الجانبي الأصلي (الحل السلمي) */
    section[data-testid="stSidebar"] > div {
        direction: rtl; /* ضمان أن المحتوى داخل الشريط عربي */
        text-align: right;
        padding-left: 15px !important;  /* هام جداً: يمنع النص من الانقطاع يساراً */
        padding-right: 10px !important;
    }
    
    /* تصغير زر إغلاق الشريط الجانبي (X) ليتناسب مع التصميم */
    button[kind="header"] {
        float: left !important; /* نقله لليسار */
    }

    /* 3. تنسيق المحتوى الرئيسي */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    
    /* تحسين المظهر العام للعناوين */
    h1, h2, h3, h4, h5, h6, p, div, label, .stMarkdown, .stButton { text-align: right !important; }
    
    /* تحسين التبويبات */
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 8px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #ff4b4b !important; color: white !important; }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# ==========================================
# 2. المصادقة (Auth)
# ==========================================
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
            all = UserModel.get_all_users()
            user = next((u for u in all if u.user_id == uid), None)
            if user and user.is_active:
                st.session_state['user'] = user
                return user
    return None

# ==========================================
# 3. التخطيط (Layout & Navbar)
# ==========================================
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
                # إذا كان مديراً، يظهر له زر واحد "إدارة النظام" بدلاً من زرين
                if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
                    st.page_link("pages/02_ادارة_النظام.py", label="لوحة التحكم والإدارة", icon="⚙️")
            with c3:
                if st.button("🚪 خروج", use_container_width=True, key="top_nav_logout"): logout_user()
        st.divider()

---

### 3. تحديث ملف `app.py` (تعديل القائمة الرئيسية)
استبدل محتوى ملف `app.py` بهذا الكود الجديد الذي يشير للملف الموحد:


http://googleusercontent.com/immersive_entry_chip/1

---

### 4. التنظيف 🗑️
بعد التأكد من أن الملف الجديد يعمل، يمكنك الآن حذف الملفات التالية من مجلد `pages`:
* `pages/02_الصلاحيات.py`
* `pages/06_اعدادات_الموقع.py`
* `pages/07_المستخدمين.py`

الآن أصبح لديك ملف إدارة واحد قوي وشامل! 🚀
# ==========================================
# 4. مشغل الميديا (Media Embedder)
# ==========================================
def render_social_media(url):
    if not url: return
    clean = url.split("?")[0].strip()
    
    def inject_white(html, h=700):
        full = f"""<!DOCTYPE html><html style="background:#fff;"><head><style>html,body{{background:#fff !important;margin:0;padding:0;width:100%;height:100%;overflow:hidden;}} .container{{display:flex;justify-content:center;align-items:center;width:100%;height:100%;}} .card{{background:#fff;width:100%;max-width:450px;}}</style></head><body><div class="container"><div class="card">{html}</div></div></body></html>"""
        components.html(full, height=h, scrolling=True)

    if "youtube" in url or "youtu.be" in url: st.video(url)
    elif "instagram" in url:
        embed = clean.rstrip("/") + "/embed" if "/embed" not in clean else clean
        inject_white(f'<iframe src="{embed}" width="100%" height="600" frameborder="0" scrolling="no" allowtransparency="true" style="background:#fff;"></iframe>', 620)
    elif "tiktok" in url:
        vid = clean.split("/")[-1]
        inject_white(f'<blockquote class="tiktok-embed" cite="{clean}" data-video-id="{vid}" style="max-width:100%;background:#fff;"><section><a target="_blank" href="{clean}">Watch</a></section></blockquote><script async src="[https://www.tiktok.com/embed.js](https://www.tiktok.com/embed.js)"></script>', 780)
    elif "twitter" in url or "x.com" in url:
        inject_white(f'<blockquote class="twitter-tweet" data-theme="light" align="center"><a href="{url}"></a></blockquote><script async src="[https://platform.twitter.com/widgets.js](https://platform.twitter.com/widgets.js)"></script>', 600)
    else:
        st.info(f"رابط: {url}")
        st.link_button("فتح", url)
