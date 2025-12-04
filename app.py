import streamlit as st
from streamlit_option_menu import option_menu
import os

from core.auth import get_current_user, logout_user
from utils.formatting import apply_custom_style
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN

# -------------------------------
# إعدادات البداية
# -------------------------------
st.set_page_config(page_title="منظومة الإدارة الذكية", page_icon="⚙️", layout="wide")
apply_custom_style()

# -------------------------------
# التحقق من المستخدم
# -------------------------------
user = get_current_user()
logged_in = user is not None

if not logged_in:
    st.warning("يجب تسجيل الدخول أولاً")
    if os.path.exists("pages/01_الدخول.py"):
        st.switch_page("pages/01_الدخول.py")
    else:
        st.error("ملف تسجيل الدخول غير موجود: pages/01_الدخول.py")
    st.stop()

# -------------------------------
# تعريف عناصر القائمة
# -------------------------------
menu_items = [
    {"name": "الصفحة الرئيسية", "page": "app.py", "icon": "house"},
    {"name": "الأقسام", "page": "pages/01_الاقسام.py", "icon": "grid"},
    {"name": "الصلاحيات", "page": "pages/02_الصلاحيات.py", "icon": "lock"},
    {"name": "رفع الوسائط", "page": "pages/03_رفع_الوسائط.py", "icon": "upload"},
    {"name": "النماذج", "page": "pages/04_النماذج.py", "icon": "file-text"},
    {"name": "التقارير", "page": "pages/05_التقارير.py", "icon": "bar-chart-2"},
    {"name": "إعدادات الموقع", "page": "pages/06_اعدادات_الموقع.py", "icon": "settings"},
    {"name": "المستخدمين", "page": "pages/07_المستخدمين.py", "icon": "users"},
]

# -------------------------------
# رسم القائمة الجانبية
# -------------------------------
with st.sidebar:
    st.subheader(f"مرحباً، {user.role_name}")

    selected_page_name = option_menu(
        menu_title="القائمة الرئيسية",
        options=[item["name"] for item in menu_items],
        icons=[item["icon"] for item in menu_items],
        default_index=0,
    )

    st.divider()
    if st.button("🚪 تسجيل الخروج"):
        logout_user()
        st.success("تم تسجيل الخروج بنجاح")
        st.experimental_rerun()

# -------------------------------
# التوجيه إلى الصفحة
# -------------------------------
selected_page = next((item for item in menu_items if item["name"] == selected_page_name), None)

if not selected_page:
    st.error("لم يتم العثور على الصفحة المطلوبة.")
    st.stop()

# إذا كانت الصفحة الرئيسية
if selected_page["page"] == "app.py":
    st.header("🏡 الصفحة الرئيسية")
    st.info(f"مرحباً بك في منظومة الإدارة الذكية. أنت مسجل كـ **{user.role_name}**.")
else:
    target = selected_page["page"]

    # التحقق من وجود الملف قبل التنقل
    if os.path.exists(target):
        st.switch_page(target)
    else:
        st.error(f"ملف الصفحة غير موجود: {target}")
