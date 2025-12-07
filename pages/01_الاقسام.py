import streamlit as st
import time

# محاولة استيراد محرر النصوص، وإذا لم يوجد نستخدم النص العادي
try:
    from streamlit_quill import st_quill
except ImportError:
    st_quill = None

# ==========================================
# 1. الاستدعاءات (Imports)
# ==========================================
try:
    import sys
    import os
    # ضمان رؤية المجلد الرئيسي
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    from backend import (
        SectionModel, TabModel, CategoryModel, ContentModel, PermissionModel,
        ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR
    )
except ImportError as e:
    st.error(f"⚠️ خطأ في الاستيراد من backend: {e}")
    st.stop()

# ==========================================
# 2. معالجة التبعيات المفقودة (Utils & Auth)
# ==========================================
# هذه الدوال احتياطية لضمان عمل الصفحة حتى لو لم تنشئ ملفات core/utils بعد
def get_current_user_mock():
    # محاولة جلب المستخدم من الجلسة إذا كان backend.py يدعم ذلك، أو الاعتماد على app.py
    # هنا نفترض وجود كائن مستخدم في الـ Session State
    if 'user' in st.session_state:
        return st.session_state['user']
    return None

def render_social_media_mock(link):
    if "youtube" in link:
        st.video(link)
    else:
        st.markdown(f"[رابط خارجي]({link})")

# محاولة الاستيراد الحقيقي، والعودة للموك إذا فشل
try:
    from core.auth import get_current_user
except ImportError:
    get_current_user = get_current_user_mock

try:
    from utils.media_embedder import render_social_media
except ImportError:
    render_social_media = render_social_media_mock

# ==========================================
# 3. إعداد الصفحة
# ==========================================
st.set_page_config(page_title="تصفح الأقسام", page_icon="📂", layout="wide")

# تطبيق اتجاه النص (RTL)
st.markdown("""
<style>
    .stApp { direction: rtl; }
    .stMarkdown, .stText, .stHeader, .stSubheader, p, div { text-align: right; }
    .stSelectbox, .stTextInput { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. التحقق من الصلاحيات والأمان
# ==========================================
user = get_current_user()

# تجاوز التحقق مؤقتاً إذا لم يكن هناك نظام تسجيل دخول فعلي لتجربة الصفحة
# (يمكنك تفعيل السطرين التاليين لإجبار المستخدم على الدخول)
if not user and 'logged_in' in st.session_state and not st.session_state['logged_in']:
   st.warning("🔒 يجب تسجيل الدخول أولاً!")
   st.stop()

# دوال مساعدة للصلاحيات
def is_super_admin():
    return user and user.role_id == ROLE_SUPER_ADMIN

def can_edit_structure():
    return user and user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]

def can_edit_content(section_id=None):
    if not user: return False
    if user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN]: return True
    if user.role_id == ROLE_SUPERVISOR:
        try:
            can_view, can_edit = PermissionModel.check_access(user.user_id, section_id=section_id)
            return can_edit
        except:
            return False
    return False

# ==========================================
# 5. واجهة المستخدم (UI Construction)
# ==========================================

# --- القائمة الجانبية: اختيار القسم والتبويب ---
st.sidebar.title("🗂️ التنقل")

# 1. جلب الأقسام
sections = SectionModel.get_all_sections()

if not sections:
    st.sidebar.warning("لا توجد أقسام متاحة حالياً.")
    # زر سريع لإضافة قسم (للمشرفين فقط) لتسهيل البداية
    if can_edit_structure():
        with st.sidebar.expander("إضافة قسم"):
            with st.form("quick_add_sec"):
                n = st.text_input("اسم القسم")
                if st.form_submit_button("إضافة"):
                    SectionModel.create_section(n, user.name if user else "System", True)
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
    # (تم التعديل لتتوافق مع backend.py الذي يستخدم get_tabs_by_section)
    sec_tabs = TabModel.get_tabs_by_section(selected_section.section_id)
    
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
                        TabModel.create_tab(selected_section.section_id, tn, user.name if user else "System")
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
    categories = CategoryModel.get_categories_by_tab(selected_tab.tab_id)

    if not categories:
        st.warning("لا توجد تصنيفات في هذا التبويب.")
        
        if can_edit_structure():
            with st.expander("➕ إضافة تصنيف جديد"):
                new_cat_name = st.text_input("اسم التصنيف الجديد")
                if st.button("إضافة التصنيف"):
                    if new_cat_name:
                        # (تصحيح: الدالة في backend اسمها create_category)
                        CategoryModel.create_category(selected_tab.tab_id, new_cat_name, user.name if user else "System")
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
                                st.caption("ملاحظة: للحصول على محرر متطور، أضف streamlit-quill إلى requirements.txt")

                            social_link = st.text_input("رابط (يوتيوب/تويتر/إنستا) - اختياري")
                            
                            submitted = st.form_submit_button("نشر المحتوى")
                            if submitted:
                                if not ct_title:
                                    st.error("يرجى كتابة عنوان للموضوع.")
                                else:
                                    # (تصحيح: الدالة في backend اسمها create_content وتتطلب ctype)
                                    ContentModel.create_content(
                                        cat_id=category.category_id,
                                        ctype="text",  # قيمة افتراضية
                                        title=ct_title,
                                        body=ct_body,
                                        social_link=social_link,
                                        created_by=user.name if user else "System"
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
                                    if st.button("🗑", key=f"del_{item.content_id}", help="حذف"):
                                        ContentModel.delete_content(item.content_id)
                                        st.toast("تم الحذف")
                                        time.sleep(0.5)
                                        st.rerun()

                            # جسم المحتوى
                            if item.body:
                                st.markdown(item.body, unsafe_allow_html=True)
                            
                            # روابط التواصل الاجتماعي
                            if item.social_link:
                                st.divider()
                                render_social_media(item.social_link)

                            # التذييل
                            st.caption(f"--- \n✍️ **{item.created_by}** | 📅 {item.created_at}")
