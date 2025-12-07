import streamlit as st
import time
from streamlit_quill import st_quill

# ==========================================
# 1. الاستدعاءات (Imports)
# ==========================================
try:
    # نستخدم backend كمصدر موحد للبيانات لضمان التوافق مع باقي النظام
    from backend import (
        SectionModel, TabModel, CategoryModel, ContentModel, PermissionModel,
        ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR
    )
    from core.auth import get_current_user
    # محاولة استيراد التنسيقات والأدوات المساعدة
    from utils.formatting import apply_custom_style
    from utils.media_embedder import render_social_media
except ImportError as e:
    st.error(f"⚠️ خطأ في الاستيراد: {e}\nتأكد من وجود ملف backend.py والمجلدات core/utils.")
    st.stop()

# ==========================================
# 2. إعداد الصفحة
# ==========================================
st.set_page_config(page_title="تصفح الأقسام", page_icon="📂", layout="wide")

# ==========================================
# 3. التحقق من الصلاحيات والأمان
# ==========================================
user = get_current_user()

if not user:
    st.warning("🔒 يجب تسجيل الدخول أولاً!")
    time.sleep(1)
    st.switch_page("app.py")

# تطبيق التنسيق العام
try:
    apply_custom_style()
except:
    pass # تجاوز الخطأ إذا لم يكن ملف التنسيق موجوداً

# دوال مساعدة للصلاحيات
def is_super_admin():
    return user.role_id == ROLE_SUPER_ADMIN

def can_edit_structure():
    return user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]

def can_edit_content(section_id=None):
    if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]: return True
    if user.role_id == ROLE_SUPER_ADMIN: return True # مكرر للتاكيد
    if user.role_id == ROLE_SUPERVISOR:
        # هنا نفترض وجود دالة في PermissionModel للتحقق
        try:
            can_view, can_edit = PermissionModel.check_access(user.user_id, section_id=section_id)
            return can_edit
        except:
            return False
    return False

# ==========================================
# 4. دوال جلب البيانات (مع الكاش لتحسين السرعة)
# ==========================================
@st.cache_data(ttl=60)
def get_cached_structure():
    """جلب الهيكل (أقسام، تبويبات) مرة واحدة وتخزينه مؤقتاً"""
    sections = SectionModel.get_all_sections()
    tabs = TabModel.get_all_tabs()
    return sections, tabs

def clear_cache():
    """مسح الكاش عند الإضافة أو الحذف"""
    st.cache_data.clear()

# ==========================================
# 5. واجهة المستخدم (UI Construction)
# ==========================================

# --- القائمة الجانبية: اختيار القسم والتبويب ---
st.sidebar.title("🗂️ التنقل")

sections, all_tabs = get_cached_structure()

if not sections:
    st.sidebar.warning("لا توجد أقسام متاحة حالياً.")
    selected_section = None
else:
    # قائمة الأقسام
    sec_names = [s.name for s in sections]
    sel_sec_name = st.sidebar.selectbox("اختر القسم:", sec_names)
    selected_section = next((s for s in sections if s.name == sel_sec_name), None)

selected_tab = None
if selected_section:
    # فلترة التبويبات التابعة للقسم المختار
    sec_tabs = [t for t in all_tabs if t.section_id == selected_section.section_id]
    
    if sec_tabs:
        tab_names = [t.name for t in sec_tabs]
        # استخدام radio لسهولة التنقل بدل selectbox إذا كانت الخيارات قليلة
        sel_tab_name = st.sidebar.radio("التبويبات الفرعية:", tab_names)
        selected_tab = next((t for t in sec_tabs if t.name == sel_tab_name), None)
    else:
        st.sidebar.info("هذا القسم لا يحتوي على تبويبات فرعية.")

# --- المحتوى الرئيسي ---

if not selected_section or not selected_tab:
    st.title("📂 تصفح المحتوى")
    st.info("👈 يرجى اختيار قسم وتبويب من القائمة الجانبية لعرض المحتوى.")
else:
    # عرض العنوان
    st.title(f"{selected_section.name} / {selected_tab.name}")
    st.markdown("---")

    # 1. جلب التصنيفات (Categories) لهذا التبويب
    # ملاحظة: لا نستخدم الكاش هنا لتحديث المحتوى بشكل فوري عند التبديل
    categories = CategoryModel.get_categories_by_tab(selected_tab.tab_id)

    if not categories:
        st.warning("لا توجد تصنيفات في هذا التبويب.")
        # خيار للمشرفين لإضافة تصنيف سريعاً (اختياري)
        if can_edit_structure():
            with st.expander("➕ إضافة تصنيف جديد"):
                new_cat_name = st.text_input("اسم التصنيف الجديد")
                if st.button("إضافة التصنيف"):
                    if new_cat_name:
                        CategoryModel.add_category(new_cat_name, selected_tab.tab_id, user.name)
                        st.toast("تمت إضافة التصنيف بنجاح")
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
                            # محرر النصوص الغني
                            ct_body = st_quill(placeholder="اكتب المحتوى هنا...", key=f"quill_{category.category_id}")
                            social_link = st.text_input("رابط (يوتيوب/تويتر/إنستا) - اختياري")
                            
                            submitted = st.form_submit_button("نشر المحتوى")
                            if submitted:
                                if not ct_title:
                                    st.error("يرجى كتابة عنوان للموضوع.")
                                else:
                                    ContentModel.add_content(
                                        category_id=category.category_id,
                                        title=ct_title,
                                        body=ct_body,
                                        social_link=social_link,
                                        created_by=user.name
                                    )
                                    st.success("تم النشر بنجاح! ✅")
                                    time.sleep(1)
                                    st.rerun()

                # --- عرض المحتوى الموجود ---
                contents = ContentModel.get_content_by_category(category.category_id)
                
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
                                    # زر حذف صغير
                                    if st.button("🗑", key=f"del_{item.content_id}", help="حذف هذا المحتوى نهائياً"):
                                        ContentModel.delete_content(item.content_id)
                                        st.toast("تم حذف المحتوى")
                                        time.sleep(0.5)
                                        st.rerun()

                            # جسم المحتوى
                            if item.body:
                                st.markdown(item.body, unsafe_allow_html=True)
                            
                            # روابط التواصل الاجتماعي
                            if item.social_link:
                                st.divider()
                                try:
                                    render_social_media(item.social_link)
                                except Exception as e:
                                    st.error(f"تعذر عرض الرابط: {e}")

                            # التذييل (معلومات الناشر)
                            st.caption(f"--- \n✍️ **{item.created_by}** | 📅 {item.created_at}")
