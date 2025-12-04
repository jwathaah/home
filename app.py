import streamlit as st
from streamlit_option_menu import option_menu
from core.auth import get_current_user, logout_user
from utils.formatting import apply_custom_style
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN

# ------------------------------------
# 1. إعدادات البداية والتحقق الأمني
# ------------------------------------
st.set_page_config(page_title="منظومة الإدارة الذكية", page_icon="⚙️", layout="wide")
apply_custom_style()

# جلب حالة المستخدم
user = get_current_user()
logged_in = user is not None

# 🚨 التوجيه الأمني:
# إذا لم يكن مسجلاً، اذهب لصفحة الدخول فوراً
if not logged_in:
    st.switch_page("pages/01_Login.py") 

# تحديد صلاحية المدير
is_admin = logged_in and user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]

# ------------------------------------
# 2. القائمة العلوية (Navbar)
# ------------------------------------

# تعريف الصفحات
menu_items = [
    {"icon": "house", "name": "الرئيسية", "page": "app.py"},
]

# إضافة الصفحات حسب الصلاحية
if logged_in:
    menu_items.append({"icon": "list-task", "name": "النماذج", "page": "pages/04_النماذج.py"})
    
    if is_admin:
        menu_items.append({"icon": "person-gear", "name": "إدارة المستخدمين", "page": "pages/02_إدارة_المستخدمين.py"})

# رسم الشريط العلوي
col_menu, col_status = st.columns([10, 2])

with col_menu:
    page_names = [item["name"] for item in menu_items]
    page_icons = [item["icon"] for item in menu_items]

    selected_page_name = option_menu(
        menu_title=None,
        options=page_names,
        icons=page_icons,
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "#ff4b4b", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px"},
            "nav-link-selected": {"background-color": "#ff4b4b", "color": "white"},
        }
    )

# زر الخروج ومعلومات المستخدم
with col_status:
    if user:
        st.caption(f"مرحباً، {user.name}")
        st.button("↩️ خروج", on_click=logout_user, key="logout_btn_top")

# ------------------------------------
# 3. توجيه الصفحة
# ------------------------------------
selected_page = next((item for item in menu_items if item["name"] == selected_page_name), None)

if selected_page:
    if selected_page["page"] == "app.py":
        # === محتوى الصفحة الرئيسية ===
        st.header("🏡 الصفحة الرئيسية")
        st.success(f"أهلاً بك في النظام يا **{user.name}**")
        st.info("يمكنك التنقل عبر الشريط العلوي.")
    else:
        st.switch_page(selected_page["page"])
