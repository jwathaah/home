import streamlit as st
import time # <--- مكتبة الوقت للطرد
from models.section_model import SectionModel, TabModel, CategoryModel
from models.content_model import ContentModel
from models.permission_model import PermissionModel
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR
from utils.formatting import apply_custom_style
from utils.media_embedder import render_social_media
from streamlit_quill import st_quill

# 1. إعداد الصفحة
st.set_page_config(page_title="تصفح الأقسام", page_icon="📂", layout="wide")

# التحقق من الدخول (أول خطوة للطرد)
user = get_current_user()
if not user:
    st.toast("🔒 يجب تسجيل الدخول أولاً!", icon="🔐")
    time.sleep(1)
    st.switch_page("app.py") # طرد

apply_custom_style()

# --- دوال الصلاحيات ---
def is_super_admin():
    return user.role_id == ROLE_SUPER_ADMIN

def can_edit_structure():
    return user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]

def can_edit_content(section_id=None):
    if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]: return True
    if user.role_id == ROLE_SUPERVISOR:
        can_view, can_edit = PermissionModel.check_access(user.user_id, section_id=section_id)
        return can_edit
    return False

# ==========================================
# 1. القائمة الجانبية + منطق الطرد الذكي
# ==========================================
with st.sidebar:
    st.title("📌 الأقسام الرئيسية")
    
    all_sections = SectionModel.get_all_sections()
    available_sections = []
    
    # فلترة الأقسام بناءً على الصلاحيات
    for sec in all_sections:
        # المدير يرى كل شيء
        if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
            available_sections.append(sec) 
        # القسم العام يراه الجميع
        elif sec.is_public:
            available_sections.append(sec)
        # المستخدم العادي والزائر: نفحص جدول الصلاحيات
        else:
            can_view, _ = PermissionModel.check_access(user.user_id, section_id=sec.section_id)
            if can_view:
                available_sections.append(sec)
    
    # 🛑🛑 منطق الطرد الذكي 🛑🛑
    # إذا كانت القائمة فارغة (لا يوجد أي قسم متاح له) وليس مديراً (المدير قد يريد إضافة قسم)
    if not available_sections and not can_edit_structure():
        st.toast("🚫 لا توجد أقسام مصرح لك برؤيتها حالياً.", icon="🚷")
        time.sleep(2)
        st.switch_page("app.py") # طرد للصفحة الرئيسية
    
    # عرض القائمة
    if not available_sections:
        if can_edit_structure():
            st.info("لا توجد أقسام، أضف قسماً جديداً.")
        selected_section = None
    else:
        sec_map = {s.name: s for s in available_sections}
        selected_sec_name = st.radio("اختر القسم:", list(sec_map.keys()), label_visibility="collapsed")
        selected_section = sec_map[selected_sec_name]

    st.divider()
    
    if can_edit_structure():
        with st.expander("➕ إضافة قسم رئيسي"):
            with st.form("add_sec_sidebar"):
                new_sec_name = st.text_input("اسم القسم")
                is_public = st.checkbox("عام للجميع؟", value=False)
                if st.form_submit_button("إضافة"):
                    SectionModel.create_section(new_sec_name, user.name, is_public)
                    st.rerun()

# ==========================================
# 2. منطقة المحتوى
# ==========================================

if selected_section:
    c1, c2 = st.columns([6, 1])
    c1.header(f"📂 {selected_section.name}")
    
    if is_super_admin():
        if c2.button("🗑 حذف القسم", key=f"del_sec_{selected_section.section_id}"):
            SectionModel.delete_section(selected_section.section_id)
            st.rerun()
            
    st.markdown("---")

    tabs = TabModel.get_tabs_by_section(selected_section.section_id)

    if can_edit_structure():
        with st.popover("➕ إضافة قسم فرعي (Tab)"):
            with st.form("add_tab_form"):
                new_tab_name = st.text_input("اسم القسم الفرعي")
                if st.form_submit_button("حفظ"):
                    TabModel.create_tab(selected_section.section_id, new_tab_name, user.name)
                    st.rerun()

    if not tabs:
        st.info("القسم فارغ.")
    else:
        tab_names = [t.name for t in tabs]
        st_tabs = st.tabs(tab_names)

        for i, tab in enumerate(tabs):
            with st_tabs[i]:
                categories = CategoryModel.get_categories_by_tab(tab.tab_id)
                
                if can_edit_structure():
                    with st.expander("⚙️ إدارة التصنيفات"):
                        with st.form(f"add_cat_{tab.tab_id}"):
                            new_cat_name = st.text_input("اسم التصنيف الجديد")
                            if st.form_submit_button("إضافة تصنيف"):
                                CategoryModel.create_category(tab.tab_id, new_cat_name, user.name)
                                st.rerun()

                if not categories:
                    st.warning("لا توجد تصنيفات.")
                else:
                    cat_map = {c.name: c for c in categories}
                    selected_cat_name = st.radio(
                        "تصنيفات القسم:", 
                        list(cat_map.keys()), 
                        horizontal=True, 
                        key=f"cat_radio_{tab.tab_id}",
                        label_visibility="collapsed"
                    )
                    
                    selected_category = cat_map[selected_cat_name]
                    st.divider()
                    
                    st.markdown(f"### 🏷️ {selected_category.name}")
                    
                    if can_edit_content(selected_section.section_id):
                        with st.expander("📝 إضافة محتوى جديد", expanded=False):
                            with st.form(f"add_cnt_{selected_category.category_id}"):
                                ct_title = st.text_input("عنوان الخبر / المقال")
                                
                                st.write("نص المحتوى:")
                                ct_body = st_quill(
                                    placeholder="اكتب المحتوى هنا...",
                                    html=True,
                                    key=f"quill_{selected_category.category_id}"
                                )
                                
                                st.markdown("---")
                                st.write("🔗 **إرفاق ميديا:**")
                                social_link = st.text_input("رابط الميديا", placeholder="https://...")
                                
                                if st.form_submit_button("نشر المحتوى"):
                                    ContentModel.create_content(
                                        selected_category.category_id, 
                                        "mixed", 
                                        ct_title, 
                                        body=ct_body, 
                                        social_link=social_link,
                                        created_by=user.name
                                    )
                                    st.rerun()
                    
                    contents = ContentModel.get_content_by_category(selected_category.category_id)
                    
                    if not contents:
                        st.caption("لا يوجد محتوى.")
                    else:
                        for item in contents:
                            with st.container(border=True):
                                c_tit, c_del = st.columns([6, 1])
                                c_tit.markdown(f"### {item.title}")
                                
                                if is_super_admin():
                                    if c_del.button("🗑", key=f"del_c_{item.content_id}"):
                                        ContentModel.delete_content(item.content_id)
                                        st.rerun()
                                
                                st.markdown(item.body, unsafe_allow_html=True)
                                
                                if item.social_link:
                                    st.divider()
                                    render_social_media(item.social_link)
                                
                                st.caption(f"✍️ {item.created_by} | {item.created_at}")
