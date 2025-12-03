import streamlit as st
from models.setting_model import SettingModel
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN

# 1. إعداد الصفحة
st.set_page_config(page_title="إعدادات النظام", page_icon="⚙️", layout="wide")

user = get_current_user()

# التحقق من الصلاحيات (للمدراء فقط)
if not user or user.role_id not in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
    st.warning("⛔ هذه الصفحة مخصصة لمدراء النظام فقط.")
    st.stop()

from ui.layout import render_sidebar
render_sidebar()

st.title("⚙️ إعدادات الموقع العامة")
st.markdown("تحكم في خصائص المنصة الأساسية.")
st.divider()

# 2. التأكد من وجود القيم الافتراضية
# هذه الخطوة تضمن عدم تعطل الصفحة إذا كان الجدول فارغاً
SettingModel.initialize_defaults(user.name)

# جلب الإعدادات الحالية
current_settings = SettingModel.get_all_settings()

def get_val(key):
    """دالة مساعدة لجلب القيمة أو نص فارغ"""
    if key in current_settings:
        return current_settings[key].value
    return ""

# 3. نموذج التعديل
with st.form("settings_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 الهوية والعرض")
        new_title = st.text_input("اسم الموقع (Site Title)", value=get_val("site_title"))
        announcement = st.text_area("شريط إعلانات (يظهر في الأعلى)", value=get_val("announcement_bar"), help="اتركه فارغاً لإخفائه")
    
    with col2:
        st.subheader("🛡️ الأمان والحالة")
        
        status_opts = ["active", "maintenance"]
        curr_status = get_val("system_status")
        idx = 0
        if curr_status in status_opts:
            idx = status_opts.index(curr_status)
            
        new_status = st.radio("حالة النظام", status_opts, index=idx, format_func=lambda x: "🟢 يعمل (Active)" if x == "active" else "🔴 وضع الصيانة (Maintenance)")
        
        allow_guest = st.checkbox("السماح للزوار (غير المسجلين) بالتصفح؟", value=(get_val("allow_guest_view") == "True"))

    st.markdown("---")
    submitted = st.form_submit_button("💾 حفظ الإعدادات", use_container_width=True)

    if submitted:
        # حفظ التغييرات
        SettingModel.update_setting("site_title", new_title, user.name)
        SettingModel.update_setting("announcement_bar", announcement, user.name)
        SettingModel.update_setting("system_status", new_status, user.name)
        SettingModel.update_setting("allow_guest_view", str(allow_guest), user.name)
        
        st.success("✅ تم تحديث إعدادات النظام بنجاح!")
        st.info("سيتم تطبيق التغييرات فوراً على جميع المستخدمين.")
        
        # عرض معلومات آخر تحديث
        if "site_title" in current_settings:
            last_update = current_settings["site_title"].updated_at
            by_user = current_settings["site_title"].updated_by
            st.caption(f"آخر تحديث: {last_update} بواسطة {by_user}")

# 4. معلومات تقنية
with st.expander("ℹ️ معلومات النسخة والخادم"):
    st.write("**الإصدار الحالي:** v1.0.0")
    st.write(f"**متصل بقاعدة بيانات:** {st.secrets['google']['spreadsheet_id'][:10]}...")
