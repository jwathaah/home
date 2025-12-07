import streamlit as st
import time
import sys
import os

# محاولة استيراد محرر النصوص، وإذا لم يوجد نستخدم النص العادي
try:
    from streamlit_quill import st_quill
except ImportError:
    st_quill = None

# ==========================================
# 1. الاستدعاءات (Imports)
# ==========================================
# إضافة المسار الرئيسي لضمان استيراد backend بشكل صحيح
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # استيراد كل شيء من الملف الموحد backend.py
    import backend as bk
except ImportError as e:
    st.error(f"⚠️ خطأ في الاستيراد من backend: {e}")
    st.stop()

# ==========================================
# 2. إعداد الصفحة
# ==========================================
st.set_page_config(page_title="تصفح الأقسام", page_icon="📂", layout="wide")

# تطبيق التنسيق العام من backend
bk.apply_custom_style()

# ==========================================
# 3. التحقق من الصلاحيات والأمان
# ==========================================
user = bk.get_current_user()

# إذا لم يكن المستخدم مسجل الدخول، نوجهه للصفحة الرئيسية
if not user:
    st.warning("🔒 يجب تسجيل الدخول أولاً!")
    time.sleep(1)
    st.switch_page("app.py")

# دوال مساعدة للصلاحيات
def is_super_admin():
    return user and user.role_id == bk.ROLE_SUPER_ADMIN

def can_edit_structure():
    return user and user.role_id in [bk.ROLE_SUPER_ADMIN, bk.ROLE_ADMIN]

def can_edit_content(section_id=None):
    if not user: return False
    if user.role_id in [bk.ROLE_SUPER_ADMIN, bk.ROLE_ADMIN]: return True
    if user.role_id == bk.ROLE_SUPERVISOR:
        try:
            can_view, can_edit = bk.PermissionModel.check_access(user.user_id, section_id=section_id)
            return can_edit
        except:
            return False
    return False

# ==========================================
# 4. واجهة المستخدم (UI Construction)
# ==========================================

# عرض القائمة الجانبية الموحدة
bk.render_sidebar()

# --- القائمة الجانبية الإضافية: اختيار القسم والتبويب ---
st.sidebar.markdown("---")
st.sidebar.title("🗂️ التنقل الداخلي")

# 1. جلب الأقسام
sections = bk.SectionModel.get_all_sections()

if not sections:
    st.sidebar.warning("لا توجد أقسام متاحة حالياً.")
    # زر سريع لإضافة قسم (للمشرفين فقط)
    if can_edit_structure():
        with st.sidebar.expander("إضافة قسم"):
            with st.form("quick_add_sec"):
                n = st.text_input("اسم القسم")
                if st.form_submit_button("إضافة"):
                    bk.SectionModel.create_section(n, user.name, True)
                    st.rerun()
    selected_section = None
else:
    # قائمة الأقسام
    sec_names = [s.name for s in sections]
    sel_sec_name = st.sidebar.selectbox("اختر القسم:", sec_names)
    selected_section = next((s for s in sections if s.name == sel_sec_name), None)

selected_tab = None

if selected_section:
    # 2. جلب التبويبات التابعة للقسم المختار
    sec_tabs = bk.TabModel.get_tabs_by_section(selected_section.section_id)
    
    if sec_tabs:
        tab_names = [t.name for t in sec_tabs]
        sel_tab_name = st.sidebar.radio("التبويبات الفرعية:", tab_names)
        selected_tab = next((t for t in sec_tabs if t.name == sel_tab_name), None)
    else:
        st.sidebar.info("هذا القسم لا يحتوي على تبويبات.")
        if can_edit_structure():
             with st.sidebar.expander("إضافة تبويب"):
                with st.form("quick_add_tab"):
                    tn = st.text_input("اسم التبويب")
                    if st.form_submit_button("إضافة"):
                        bk.TabModel.create_tab(selected_section.section_id, tn, user.name)
                        st.rerun()

# --- المحتوى الرئيسي ---

if not selected_section or not selected_tab:
    st.title("📂 تصفح المحتوى")
    st.info("👈 يرجى اختيار قسم وتبويب من القائمة الجانبية لعرض المحتوى.")
else:
    # عرض العنوان
    st.title(f"{selected_section.name} / {selected_tab.name}")
    st.markdown("---")

    # 3. جلب التصنيفات (Categories) لهذا التبويب
    categories = bk.CategoryModel.get_categories_by_tab(selected_tab.tab_id)

    if not categories:
        st.warning("لا توجد تصنيفات في هذا التبويب.")
        
        if can_edit_structure():
            with st.expander("➕ إضافة تصنيف جديد"):
                new_cat_name = st.text_input("اسم التصنيف الجديد")
                if st.button("إضافة التصنيف"):
                    if new_cat_name:
                        bk.CategoryModel.create_category(selected_tab.tab_id, new_cat_name, user.name)
                        st.success("تمت الإضافة")
                        time.sleep(1)
                        st.rerun()
    else:
        # عرض التصنيفات كـ Tabs علوية
        cat_names = [c.name for c in categories]
        active_cat_tab = st.tabs(cat_names)

        # التعامل مع كل تصنيف داخل التبويب الخاص به
        for i, category in enumerate(categories):
            with active_cat_tab[i]:
                
                # --- منطقة إضافة محتوى جديد (للمصرح لهم فقط) ---
                if can_edit_content(selected_section.section_id):
                    with st.expander(f"✍️ إضافة محتوى جديد في: {category.name}"):
                        with st.form(f"add_content_{category.category_id}"):
                            ct_title = st.text_input("عنوان الموضوع")
                            
                            # محرر النصوص الغني (مع بديل في حال عدم توفره)
                            if st_quill:
                                ct_body = st_quill(placeholder="اكتب المحتوى هنا...", key=f"quill_{category.category_id}")
                            else:
                                ct_body = st.text_area("اكتب المحتوى هنا...", key=f"area_{category.category_id}")
                                st.caption("ملاحظة: لمحرر أفضل، تأكد من تثبيت streamlit-quill")

                            social_link = st.text_input("رابط (يوتيوب/تويتر/إنستا) - اختياري")
                            
                            submitted = st.form_submit_button("نشر المحتوى")
                            if submitted:
                                if not ct_title:
                                    st.error("يرجى كتابة عنوان للموضوع.")
                                else:
                                    bk.ContentModel.create_content(
                                        cat_id=category.category_id,
                                        ctype="text", 
                                        title=ct_title,
                                        body=ct_body,
                                        social_link=social_link,
                                        created_by=user.name
                                    )
                                    st.success("تم النشر بنجاح! ✅")
                                    time.sleep(1)
                                    st.rerun()

                # --- عرض المحتوى الموجود ---
                contents = bk.ContentModel.get_content_by_category(category.category_id)
                
                if not contents:
                    st.caption("📭 لا يوجد محتوى في هذا التصنيف حتى الآن.")
                else:
                    for item in contents:
                        with st.container(border=True):
                            # ترويسة المحتوى (العنوان + زر الحذف)
                            c_head, c_btn = st.columns([0.9, 0.1])
                            with c_head:
                                st.markdown(f"### {item.title}")
                            with c_btn:
                                if is_super_admin():
                                    if st.button("🗑", key=f"del_{item.content_id}", help="حذف"):
                                        bk.ContentModel.delete_content(item.content_id)
                                        st.toast("تم الحذف")
                                        time.sleep(0.5)
                                        st.rerun()

                            # جسم المحتوى
                            if item.body:
                                st.markdown(item.body, unsafe_allow_html=True)
                            
                            # روابط التواصل الاجتماعي
                            if item.social_link:
                                st.divider()
                                bk.render_social_media(item.social_link)

                            # التذييل
                            st.caption(f"--- \n✍️ **{item.created_by}** | 📅 {item.created_at}")
