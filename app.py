import streamlit as st
import time
from streamlit_option_menu import option_menu
from core.auth import get_current_user, logout_user
from utils.formatting import apply_custom_style
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN

# ------------------------------------
# 1. إعدادات البداية
# ------------------------------------
st.set_page_config(page_title="منظومة الإدارة الذكية", page_icon="⚙️", layout="wide")
apply_custom_style()
import streamlit as st
import time
from streamlit_option_menu import option_menu
from core.auth import get_current_user, logout_user
from utils.formatting import apply_custom_style
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN

# ------------------------------------
# 1. إعدادات البداية
# ------------------------------------
st.set_page_config(page_title="منظومة الإدارة الذكية", page_icon="⚙️", layout="wide")
apply_custom_style()

user = get_current_user()
logged_in = user is not None

# 🚨🚨 الخطأ كان هنا: يجب التحقق من الدخول فوراً قبل رسم أي شيء
if not logged_in:
    st.switch_page("pages/01_الدخول.py")


# الآن، بعد أن تأكدنا أن المستخدم مسجل للدخول:
is_admin = logged_in and user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]

# ------------------------------------
# 2. منطقة الترويسة الأفقية (الـ Navbar)
# ------------------------------------
# ... (باقي كود app.py كما هو) ...
# ------------------------------------
# 2. منطقة الترويسة الأفقية (الـ Navbar)
# ------------------------------------

# تحديد عناصر القائمة
menu_items = [
    {"icon": "house", "name": "الرئيسية", "page": "app.py"},
]

# إضافة صفحات الإدارة/النماذج إذا كان المستخدم مسجلاً
if logged_in:
    menu_items.append({"icon": "list-task", "name": "النماذج", "page": "pages/04_النماذج.py"})
    if is_admin:
        # يمكنك إضافة صفحات إدارية أخرى هنا
        menu_items.append({"icon": "person-gear", "name": "إدارة المستخدمين", "page": "pages/02_إدارة_المستخدمين.py"})


# ------------------------------------
# عرض شريط التنقل الأفقي والتحكم بالدخول
# ------------------------------------

# تقسيم الترويسة (القائمة على اليمين والحالة على اليسار)
col_menu, col_status = st.columns([10, 2])

with col_menu:
    # استخدام option_menu الأفقي للتنقل
    page_names = [item["name"] for item in menu_items]
    page_icons = [item["icon"] for item in menu_items]

    # حفظ حالة الصفحة المختارة
    selected_page_name = option_menu(
        menu_title=None,  # لا نحتاج لعنوان
        options=page_names,
        icons=page_icons,
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important"},
            "icon": {"color": "#ff4b4b", "font-size": "18px"},
            "nav-link-selected": {"background-color": "#ff4b4b", "color": "white"},
        }
    )

# ------------------------------------
# 3. عرض حالة المستخدم (Login/Logout)
# ------------------------------------
with col_status:
    if logged_in:
        # عرض اسم المستخدم وزر الخروج
        st.write(f"مرحباً، **{user.name}**")
        st.button("↩️ خروج", on_click=logout_user)
    else:
        # عرض زر الدخول للمستخدم غير المسجل
        if st.button("🔐 تسجيل الدخول"):
            st.switch_page("pages/01_الدخول.py")


# ------------------------------------
# 4. توجيه الصفحة بناءً على الاختيار
# ------------------------------------

# البحث عن الصفحة المقابلة للاسم المختار
selected_page = next((item for item in menu_items if item["name"] == selected_page_name), None)

if selected_page:
    # التوجيه للصفحة المختارة (باستخدام المسار المحفوظ)
    if selected_page["page"] == "app.py":
        st.header("🏡 الصفحة الرئيسية")
        st.info(f"مرحباً بك في منظومة الإدارة الذكية. أنت مسجل كـ **{user.role_name if logged_in else 'زائر'}**.")
        # هنا يمكنك وضع محتوى الصفحة الرئيسية
    else:
        # استخدام switch_page للانتقال للصفحات الفرعية
        st.switch_page(selected_page["page"])
