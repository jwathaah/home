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
    st.warning("🔒 يجب عليك تسجيل الدخول.")
    st.stop()

# تطبيق الستايل
from utils.formatting import apply_custom_style
apply_custom_style()

# دوال الصلاحيات
def can_edit_structure():
    return user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]

def can_edit_content(section_id=None):
    if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]: return True
    if user.role_id == ROLE_SUPERVISOR:
        can_view, can_edit = PermissionModel.check_access(user.user_id, section_id=section_id)
        return can_edit
    return False

# ==========================================
# 1. القائمة الجانبية (الأقسام الرئيسية)
# ==========================================
with st.sidebar:
    st.title("📌 الأقسام الرئيسية")
    
    # جلب الأقسام
    all_sections = SectionModel.get_all_sections()
    
    # تصفية الأقسام حسب الصلاحية
    available_sections = []
    for sec in all_sections:
        if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN] or sec.is_public:
            available_sections.append(sec)
        else:
            can_view, _ = PermissionModel.check_access(user.user_id, section_id=sec.section_id)
            if can_view:
                available_sections.append(sec)
    
    # عرض الأقسام كـ Radio Button (خيار واحد ظاهر دائماً)
    if not available_sections:
        st.warning("لا توجد أقسام.")
        selected_section = None
    else:
        # إنشاء قاموس لربط الاسم بالكائن
        sec_map = {s.name: s for s in available_sections}
        
        # عرض الأسماء في الراديو
        selected_sec_name = st.radio(
            "اختر القسم:",
            list(sec_map.keys()),
            label_visibility="collapsed" # إخفاء العنوان الصغير ليكون التصميم أنظف
        )
        selected_section = sec_map[selected_sec_name]

    st.divider()
    
    # (للمدراء) إضافة قسم جديد من القائمة الجانبية
    if can_edit_structure():
        with st.expander("➕ إضافة قسم رئيسي"):
            with st.form("add_sec_sidebar"):
                new_sec_name = st.text_input("اسم القسم")
                is_public = st.checkbox("عام للجميع؟", value=False)
                if st.form_submit_button("إضافة"):
                    SectionModel.create_section(new_sec_name, user.name, is_public)
                    st.rerun()

# ==========================================
# 2. منطقة المحتوى الرئيسية
# ==========================================

if selected_section:
    # عنوان القسم وزر الحذف
    col_h1, col_h2 = st.columns([6, 1])
    with col_h1:
        st.subheader(f"📂 {selected_section.name}")
    with col_h2:
        if can_edit_structure():
            if st.button("🗑 حذف القسم", key=f"del_sec_{selected_section.section_id}"):
                SectionModel.delete_section(selected_section.section_id)
                st.rerun()

    st.markdown("---")

    # جلب التبويبات (الأقسام الفرعية)
    tabs = TabModel.get_tabs_by_section(selected_section.section_id)

    # (للمدراء) زر إضافة تبويب جديد
    if can_edit_structure():
        with st.popover("➕ إضافة قسم فرعي (Tab)"):
            with st.form("add_tab_form"):
                new_tab_name = st.text_input("اسم القسم الفرعي")
                if st.form_submit_button("حفظ"):
                    TabModel.create_tab(selected_section.section_id, new_tab_name, user.name)
                    st.rerun()

    if not tabs:
        st.info("👈 هذا القسم فارغ، اختر 'إضافة قسم فرعي' للبدء.")
    else:
        # عرض الأقسام الفرعية كـ Tabs علوية
        tab_names = [t.name for t in tabs]
        st_tabs = st.tabs(tab_names)

        for i, tab in enumerate(tabs):
            with st_tabs[i]:
                # --- نحن الآن داخل القسم الفرعي المختار ---
                
                # جلب التصنيفات
                categories = CategoryModel.get_categories_by_tab(tab.tab_id)
                
                # (للمدراء) إضافة تصنيف
                if can_edit_structure():
                    c_add1, c_add2 = st.columns([1, 5])
                    with c_add1:
                         with st.popover("➕ تصنيف جديد"):
                            with st.form(f"add_cat_{tab.tab_id}"):
                                new_cat_name = st.text_input("اسم التصنيف")
                                if st.form_submit_button("إضافة"):
                                    CategoryModel.create_category(tab.tab_id, new_cat_name, user.name)
                                    st.rerun()
                
                if not categories:
                    st.warning("لا توجد تصنيفات هنا.")
                else:
                    # عرض التصنيفات بشكل "مكشوف" (Block) واحد تلو الآخر
                    for category in categories:
                        
                        # إطار جمالي لكل تصنيف
                        with st.container(border=True):
                            # رأس التصنيف
                            cat_col1, cat_col2 = st.columns([5, 1])
                            with cat_col1:
                                st.markdown(f"### 🏷️ {category.name}")
                            with cat_col2:
                                # زر لإضافة محتوى داخل هذا التصنيف مباشرة
                                if can_edit_content(selected_section.section_id):
                                    with st.popover("📝 إضافة محتوى"):
                                        with st.form(f"add_cnt_{category.category_id}"):
                                            ct_title = st.text_input("العنوان")
                                            ct_body = st.text_area("التفاصيل")
                                            # يمكن إضافة حقول الميديا هنا
                                            if st.form_submit_button("نشر"):
                                                ContentModel.create_content(category.category_id, "text", ct_title, ct_body, created_by=user.name)
                                                st.rerun()

                            # عرض المحتويات داخل التصنيف (بدون Expander)
                            contents = ContentModel.get_content_by_category(category.category_id)
                            
                            if not contents:
                                st.caption("   (لا يوجد محتوى مضاف بعد)")
                            else:
                                for item in contents:
                                    # عرض المحتوى كبطاقة صغيرة داخل التصنيف
                                    st.markdown(f"**🔹 {item.title}**")
                                    st.write(item.body)
                                    
                                    # معلومات الميديا والروابط (إن وجدت)
                                    if item.content_type == "image":
                                        st.image("assets/icons/image_placeholder.png", width=100) # (مثال)
                                    
                                    # أزرار التحكم بالمحتوى
                                    if can_edit_content(selected_section.section_id):
                                        if st.button("حذف الخبر", key=f"del_cnt_{item.content_id}"):
                                            ContentModel.delete_content(item.content_id)
                                            st.rerun()
                                    
                                    st.divider() # فاصل بين كل خبر وآخر
