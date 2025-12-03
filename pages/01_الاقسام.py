import streamlit as st
from models.section_model import SectionModel, TabModel, CategoryModel
from models.content_model import ContentModel
from models.permission_model import PermissionModel
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR

# 1. إعداد الصفحة
st.set_page_config(page_title="تصفح الأقسام", page_icon="📂", layout="wide")

# التحقق من الدخول
user = get_current_user()
if not user:
    st.warning("🔒 يجب عليك تسجيل الدخول للوصول إلى هذه الصفحة.")
    st.stop()

# رسم القائمة الجانبية (من الملف الذي أنشأناه سابقاً)
from ui.layout import render_sidebar
render_sidebar()

# --- دوال مساعدة للصلاحيات ---
def can_edit_structure():
    """هل يحق للمستخدم تعديل الهيكل (أقسام/تبويبات)؟"""
    return user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]

def can_edit_content(section_id=None):
    """هل يحق للمستخدم إضافة/تعديل المحتوى؟"""
    if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]:
        return True
    if user.role_id == ROLE_SUPERVISOR:
        # المشرف يحتاج فحص صلاحية محددة على القسم
        can_view, can_edit = PermissionModel.check_access(user.user_id, section_id=section_id)
        return can_edit
    return False

# --- الواجهة الرئيسية ---

# عنوان الصفحة وزر إضافة قسم (للمدراء فقط)
col1, col2 = st.columns([4, 1])
with col1:
    st.title("📂 المكتبة الرقمية")
with col2:
    if can_edit_structure():
        with st.popover("➕ إضافة قسم جديد"):
            with st.form("add_section_form"):
                new_sec_name = st.text_input("اسم القسم")
                is_public = st.checkbox("عام للجميع؟", value=False)
                if st.form_submit_button("حفظ"):
                    if new_sec_name:
                        SectionModel.create_section(new_sec_name, user.name, is_public)
                        st.success("تم!")
                        st.rerun()

st.divider()

# 2. جلب الأقسام وعرضها
all_sections = SectionModel.get_all_sections()
available_sections = []

# تصفية الأقسام حسب الصلاحيات
for sec in all_sections:
    if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN] or sec.is_public:
        available_sections.append(sec)
    else:
        # فحص الصلاحيات الخاصة
        can_view, _ = PermissionModel.check_access(user.user_id, section_id=sec.section_id)
        if can_view:
            available_sections.append(sec)

if not available_sections:
    st.info("🚫 لا توجد أقسام متاحة للعرض حالياً.")
    st.stop()

# عرض الأقسام كـ Tabs علوية (أو Radio في الجانب إذا كانت كثيرة، سنستخدم Tabs للأناقة)
sec_names = [s.name for s in available_sections]
active_tab_idx = 0
# خدعة بسيطة للاحتفاظ بالتبويب المختار عند التحديث
if 'active_sec_idx' not in st.session_state: st.session_state.active_sec_idx = 0

# هنا نستخدم st.tabs لعرض الأقسام
section_tabs = st.tabs(sec_names)

for i, section in enumerate(available_sections):
    with section_tabs[i]:
        # --- داخل القسم المختار ---
        
        # شريط أدوات القسم (تعديل/حذف) للمدراء
        if can_edit_structure():
            c1, c2, c3 = st.columns([6, 1, 1])
            with c2:
                if st.button("🗑️ حذف القسم", key=f"del_sec_{section.section_id}"):
                    SectionModel.delete_section(section.section_id)
                    st.rerun()
            with c3:
                with st.popover("➕ إضافة تبويب"):
                    with st.form(f"add_tab_{section.section_id}"):
                        new_tab_name = st.text_input("اسم التبويب")
                        if st.form_submit_button("إضافة"):
                            TabModel.create_tab(section.section_id, new_tab_name, user.name)
                            st.rerun()
        
        st.markdown(f"### 📑 محتويات قسم: {section.name}")
        
        # جلب التبويبات (Tabs) لهذا القسم
        tabs = TabModel.get_tabs_by_section(section.section_id)
        
        if not tabs:
            st.warning("هذا القسم فارغ، أضف تبويبات بداخله.")
        else:
            # عرض التبويبات الداخلية (Sub-tabs)
            sub_tabs_names = [t.name for t in tabs]
            sub_tabs = st.tabs(sub_tabs_names)
            
            for j, tab in enumerate(tabs):
                with sub_tabs[j]:
                    # --- داخل التبويب ---
                    
                    # زر إضافة تصنيف (Category)
                    if can_edit_structure():
                         with st.expander("⚙️ إعدادات التبويب", expanded=False):
                            with st.form(f"add_cat_{tab.tab_id}"):
                                st.write("إضافة فئة جديدة (Category)")
                                new_cat_name = st.text_input("اسم الفئة")
                                if st.form_submit_button("إضافة الفئة"):
                                    CategoryModel.create_category(tab.tab_id, new_cat_name, user.name)
                                    st.rerun()

                    # جلب التصنيفات
                    categories = CategoryModel.get_categories_by_tab(tab.tab_id)
                    
                    if not categories:
                        st.info("لا توجد فئات هنا.")
                    
                    for category in categories:
                        # عرض الفئة كـ Expander
                        with st.expander(f"📂 {category.name}", expanded=True):
                            
                            # زر إضافة محتوى داخل الفئة
                            if can_edit_content(section.section_id):
                                col_add, _ = st.columns([1, 5])
                                with col_add:
                                    with st.popover("➕ إضافة محتوى"):
                                        with st.form(f"add_content_{category.category_id}"):
                                            ct_title = st.text_input("العنوان")
                                            ct_body = st.text_area("النص / التفاصيل")
                                            # يمكن إضافة حقول ميديا هنا لاحقاً
                                            if st.form_submit_button("نشر"):
                                                ContentModel.create_content(
                                                    category.category_id, 
                                                    "text", 
                                                    ct_title, 
                                                    body=ct_body, 
                                                    created_by=user.name
                                                )
                                                st.success("تم النشر")
                                                st.rerun()
                            
                            # عرض المحتويات
                            contents = ContentModel.get_content_by_category(category.category_id)
                            if not contents:
                                st.caption("لا يوجد محتوى.")
                            
                            for item in contents:
                                st.markdown(f"#### {item.title}")
                                st.write(item.body)
                                st.caption(f"✍️ {item.created_by} | 🕒 {item.created_at}")
                                
                                # أزرار التحكم بالمحتوى
                                if can_edit_content(section.section_id):
                                    if st.button("حذف", key=f"del_content_{item.content_id}"):
                                        ContentModel.delete_content(item.content_id)
                                        st.rerun()
                                st.divider()
