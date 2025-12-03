import streamlit as st
from models.user_model import UserModel
from models.section_model import SectionModel, TabModel
from models.permission_model import PermissionModel
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN

# 1. إعداد الصفحة
st.set_page_config(page_title="إدارة الصلاحيات", page_icon="🔐", layout="wide")

# التحقق من الصلاحية (فقط المدير العام والمدير يمكنهم الدخول هنا)
user = get_current_user()
if not user or user.role_id not in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
    st.warning("⛔ عذراً، هذه الصفحة مخصصة للمسؤولين فقط.")
    st.stop()

# القائمة الجانبية
from ui.layout import render_sidebar
render_sidebar()

st.title("🔐 توزيع الصلاحيات")
st.markdown("هنا يمكنك تحديد الأقسام والتبويبات التي يحق لكل مستخدم رؤيتها أو تعديلها.")
st.divider()

# 2. اختيار المستخدم
# جلب جميع المستخدمين باستثناء المدير العام (لا أحد يعدل صلاحيات المدير العام)
all_users = UserModel.get_all_users()
target_users = [u for u in all_users if u.role_id != ROLE_SUPER_ADMIN]

if not target_users:
    st.info("لا يوجد مستخدمين آخرين لتعديل صلاحياتهم.")
    st.stop()

# إنشاء قائمة للاختيار: "الاسم (البريد)"
user_options = {f"{u.name} ({u.email})": u for u in target_users}
selected_label = st.selectbox("👤 اختر المستخدم:", list(user_options.keys()))
selected_user = user_options[selected_label]

st.info(f"جاري تعديل صلاحيات: **{selected_user.name}** (الدور: {selected_user.role_id})")

# 3. جدول الصلاحيات (Matrix)
# جلب الصلاحيات الحالية للمستخدم لتعبئة الخانات تلقائياً
current_perms = PermissionModel.get_permissions_by_user(selected_user.user_id)

def find_perm(section_id, tab_id=""):
    """دالة مساعدة للبحث عن صلاحية مسجلة سابقاً"""
    for p in current_perms:
        if p.section_id == str(section_id) and p.tab_id == str(tab_id):
            return p
    return None

all_sections = SectionModel.get_all_sections()

if not all_sections:
    st.warning("لا توجد أقسام في الموقع حتى الآن.")
    st.stop()

# نموذج الحفظ الكبير
with st.form("permissions_matrix"):
    
    # رأس الجدول
    h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
    h1.write("📂 **الهيكل التنظيمي**")
    h2.write("👁️ **عرض**")
    h3.write("✏️ **تعديل**")
    h4.write("🚫 **حجب نهائي**")
    st.markdown("---")

    for sec in all_sections:
        # البحث عن صلاحية القسم الحالية
        p_sec = find_perm(sec.section_id)
        
        # القيم الافتراضية للقسم
        sec_view_val = p_sec.view if p_sec else False
        sec_edit_val = p_sec.edit if p_sec else False
        sec_hide_val = p_sec.hidden if p_sec else False

        # صف القسم
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        c1.markdown(f"### {sec.name}")
        
        # مفاتيح فريدة (Keys) لكل Checkbox
        s_view = c2.checkbox("عرض", value=sec_view_val, key=f"sv_{sec.section_id}")
        s_edit = c3.checkbox("تعديل", value=sec_edit_val, key=f"se_{sec.section_id}")
        s_hide = c4.checkbox("حجب", value=sec_hide_val, key=f"sh_{sec.section_id}")
        
        # التبويبات داخل القسم
        tabs = TabModel.get_tabs_by_section(sec.section_id)
        if tabs:
            st.caption(f"└ إعدادات التبويبات لـ {sec.name}:")
            for tab in tabs:
                p_tab = find_perm(sec.section_id, tab_id=tab.tab_id)
                
                # القيم الافتراضية للتبويب
                tab_view_val = p_tab.view if p_tab else False
                tab_edit_val = p_tab.edit if p_tab else False
                tab_hide_val = p_tab.hidden if p_tab else False
                
                tc1, tc2, tc3, tc4 = st.columns([3, 1, 1, 1])
                tc1.text(f"    📄 {tab.name}")
                
                t_view = tc2.checkbox("", value=tab_view_val, key=f"tv_{tab.tab_id}")
                t_edit = tc3.checkbox("", value=tab_edit_val, key=f"te_{tab.tab_id}")
                t_hide = tc4.checkbox("", value=tab_hide_val, key=f"th_{tab.tab_id}")
        
        st.divider()

    # زر الحفظ النهائي
    submitted = st.form_submit_button("💾 حفظ وتحديث الصلاحيات", use_container_width=True)

    if submitted:
        # عند الضغط على حفظ، نقرأ جميع القيم من Session State ونخزنها
        progress_bar = st.progress(0)
        total_steps = len(all_sections)
        
        for i, sec in enumerate(all_sections):
            # 1. حفظ صلاحية القسم
            v = st.session_state[f"sv_{sec.section_id}"]
            e = st.session_state[f"se_{sec.section_id}"]
            h = st.session_state[f"sh_{sec.section_id}"]
            
            PermissionModel.grant_permission(
                selected_user.user_id, 
                section_id=sec.section_id, 
                view=v, edit=e, hidden=h
            )
            
            # 2. حفظ صلاحيات التبويبات التابعة له
            tabs = TabModel.get_tabs_by_section(sec.section_id)
            for tab in tabs:
                tv = st.session_state[f"tv_{tab.tab_id}"]
                te = st.session_state[f"te_{tab.tab_id}"]
                th = st.session_state[f"th_{tab.tab_id}"]
                
                PermissionModel.grant_permission(
                    selected_user.user_id,
                    section_id=sec.section_id,
                    tab_id=tab.tab_id,
                    view=tv, edit=te, hidden=th
                )
            
            # تحديث شريط التقدم
            progress_bar.progress((i + 1) / total_steps)

        st.success(f"✅ تم تحديث صلاحيات المستخدم {selected_user.name} بنجاح!")
        st.balloons()
