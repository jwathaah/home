import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
import sys
import os

# ==========================================
# 1. الإعدادات العامة (تنفذ مرة واحدة فقط)
# ==========================================
st.set_page_config(page_title="لوحة الإدارة", page_icon="🛠️", layout="wide")

# إعداد المسارات واستيراد Backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import backend as bk
    # استيراد النماذج المطلوبة من الباك إند
    from backend import (
        UserModel, SectionModel, ContentModel, ChecklistModel, MediaModel,
        ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_NAMES,
        get_data, TABLE_CONTENT
    )
except ImportError as e:
    st.error(f"⚠️ خطأ في الاستيراد من backend: {e}")
    st.stop()

# تطبيق الستايل الموحد
if hasattr(bk, 'apply_custom_style'):
    bk.apply_custom_style()

# التحقق من المستخدم (مرة واحدة للكل)
if hasattr(bk, 'get_current_user'):
    user = bk.get_current_user()
else:
    user = None

if not user:
    st.warning("🔒 يجب تسجيل الدخول أولاً!")
    time.sleep(1)
    st.stop() # توقف هنا إذا لم يكن مسجلاً

# عرض القائمة الجانبية الموحدة (إذا كانت موجودة)
if hasattr(bk, 'render_sidebar'):
    bk.render_sidebar()

# ==========================================
# 2. دوال الكاش (يجب أن تكون في المستوى الأعلى)
# ==========================================

# --- كاش الوسائط ---
@st.cache_data(ttl=60)
def get_cached_media():
    try:
        return MediaModel.get_all_media()
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return []

# --- كاش النماذج ---
@st.cache_data(ttl=60)
def get_cached_checklists():
    try:
        return ChecklistModel.get_all_items()
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return []

# --- كاش التقارير ---
@st.cache_data(ttl=300)
def get_analytics_data():
    # 1. بيانات المستخدمين
    try:
        users = UserModel.get_all_users()
        df_users = pd.DataFrame([vars(u) for u in users])
    except Exception as e:
        st.error(f"خطأ في جلب المستخدمين: {e}")
        df_users = pd.DataFrame()
    
    # 2. بيانات المحتوى
    try:
        df_content = get_data(TABLE_CONTENT)
    except Exception:
        df_content = pd.DataFrame(columns=["title", "category_id", "created_by", "created_at"])

    # 3. بيانات القوائم
    try:
        checklists = ChecklistModel.get_all_items()
        df_checklists = pd.DataFrame([vars(i) for i in checklists])
    except Exception:
        df_checklists = pd.DataFrame()

    return df_users, df_content, df_checklists

# ==========================================
# 3. دوال الصفحات (Logics)
# ==========================================

def render_media_page():
    # التحقق من الصلاحيات لهذه الصفحة
    ALLOWED_ROLES = [ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR]
    if user.role_id not in ALLOWED_ROLES:
        st.error("⛔ عذراً، ليس لديك صلاحية لدخول هذه الصفحة!")
        return

    def clear_media_cache():
        st.cache_data.clear()

    st.header("📂 مكتبة الوسائط والملفات")
    st.markdown("---")

    tabs = st.tabs(["⬆️ رفع ملف جديد", "🖼️ استعراض المكتبة"])

    with tabs[0]:
        st.subheader("رفع ملفات إلى Google Drive")
        with st.container(border=True):
            uploaded_file = st.file_uploader(
                "اختر ملفاً للرفع (صور، فيديو، مستندات)", 
                type=['png', 'jpg', 'jpeg', 'pdf', 'mp4', 'docx', 'xlsx'],
                accept_multiple_files=False
            )

            if uploaded_file is not None:
                file_details = {
                    "اسم الملف": uploaded_file.name,
                    "النوع": uploaded_file.type,
                    "الحجم": f"{uploaded_file.size / 1024:.2f} KB"
                }
                st.json(file_details)
                
                if st.button("🚀 بدء الرفع", use_container_width=True):
                    with st.status("جارٍ معالجة الملف...", expanded=True) as status:
                        st.write("1️⃣ الاتصال بـ Google Drive...")
                        drive_file_id, web_view_link = bk.upload_file_to_cloud(
                            uploaded_file, 
                            uploaded_file.name, 
                            uploaded_file.type
                        )
                        
                        if drive_file_id:
                            st.write("2️⃣ حفظ البيانات في النظام...")
                            MediaModel.add_media(
                                name=uploaded_file.name,
                                mtype=uploaded_file.type,
                                drive_id=drive_file_id,
                                by=user.name
                            )
                            status.update(label="✅ تم الرفع بنجاح!", state="complete", expanded=False)
                            st.success(f"تم رفع الملف: {uploaded_file.name}")
                            clear_media_cache()
                            time.sleep(1)
                            st.rerun()
                        else:
                            status.update(label="❌ فشل الرفع!", state="error")

    with tabs[1]:
        st.subheader("الأرشيف")
        c_filter, c_refresh = st.columns([6, 1])
        with c_refresh:
            if st.button("🔄 تحديث", use_container_width=True):
                clear_media_cache()
                st.rerun()
                
        all_media = get_cached_media()
        
        if not all_media:
            st.info("لا توجد ملفات مرفوعة حتى الآن.")
        else:
            cols_count = 4
            cols = st.columns(cols_count)
            for index, item in enumerate(all_media):
                with cols[index % cols_count]:
                    with st.container(border=True):
                        is_image = "image" in item.file_type.lower()
                        file_shown = False
                        if is_image and item.google_drive_id:
                            if hasattr(bk, 'get_file_content'):
                                try:
                                    with st.spinner("."):
                                        image_data = bk.get_file_content(item.google_drive_id)
                                    if image_data:
                                        st.image(image_data, use_container_width=True)
                                        file_shown = True
                                except Exception:
                                    pass
                        
                        if not file_shown:
                            icon = "📄"
                            if "video" in item.file_type: icon = "🎥"
                            elif "pdf" in item.file_type: icon = "📕"
                            elif "sheet" in item.file_type or "excel" in item.file_type: icon = "📊"
                            elif is_image: icon = "🖼️"
                            st.markdown(f"<div style='text-align: center; font-size: 50px; margin-bottom: 10px;'>{icon}</div>", unsafe_allow_html=True)

                        st.markdown(f"**{item.file_name}**")
                        st.caption(f"👤 {item.uploaded_by}")
                        st.caption(f"📅 {item.uploaded_at}")
                        
                        if item.google_drive_id:
                            drive_link = f"https://drive.google.com/file/d/{item.google_drive_id}/view?usp=sharing"
                            st.link_button("🔗 فتح في Drive", drive_link, use_container_width=True)
                        else:
                            st.caption("الرابط غير متوفر")


def render_forms_page():
    is_admin = (user.role_id in [ROLE_SUPER_ADMIN, ROLE_ADMIN])

    def clear_checklist_cache():
        st.cache_data.clear()

    def toggle_item_status(item_id, current_status):
        ChecklistModel.toggle_status(item_id, current_status)
        clear_checklist_cache()

    all_items = get_cached_checklists()
    existing_main_titles = []
    if all_items:
        existing_main_titles = sorted(list(set([i.main_title for i in all_items if i.main_title])))

    # القائمة الجانبية الخاصة بالنماذج (تظهر فقط عند تفعيل التبويب)
    if is_admin:
        with st.sidebar:
            st.markdown("---")
            st.header("⚙️ إدارة القوائم (النماذج)")
            with st.expander("➕ إضافة بند جديد", expanded=False):
                with st.form("smart_add_form_chk", clear_on_submit=True):
                    select_options = ["✨ قسم جديد..."] + existing_main_titles
                    selected_main = st.selectbox("القسم الرئيسي:", select_options)
                    
                    new_main_title = None
                    if selected_main == "✨ قسم جديد...":
                        new_main_title = st.text_input("اكتب اسم القسم الجديد:")
                    
                    sub_title = st.text_input("العنوان الفرعي (اختياري):")
                    item_name = st.text_input("نص المهمة / البند:")
                    
                    if st.form_submit_button("إضافة", use_container_width=True):
                        final_main = new_main_title if (selected_main == "✨ قسم جديد...") else selected_main
                        if not final_main or not item_name:
                            st.error("يرجى تحديد القسم واسم المهمة!")
                        else:
                            ChecklistModel.add_item(
                                main=final_main, 
                                sub=sub_title if sub_title else "", 
                                name=item_name, 
                                by=user.name
                            )
                            st.toast("✅ تمت الإضافة بنجاح!")
                            clear_checklist_cache()
                            time.sleep(1)
                            st.rerun()

    st.header("📋 قوائم المهام والنماذج")
    st.markdown("---")

    if not all_items:
        st.info("📭 لا توجد قوائم مهام حالياً.")
    else:
        grouped_data = {}
        for item in all_items:
            if item.main_title not in grouped_data:
                grouped_data[item.main_title] = []
            grouped_data[item.main_title].append(item)
        
        for main_title, items in grouped_data.items():
            with st.expander(f"📌 {main_title}", expanded=True):
                unchecked_items = [i for i in items if not i.is_checked]
                checked_items = [i for i in items if i.is_checked]
                
                for item in unchecked_items:
                    c1, c2 = st.columns([0.5, 11])
                    with c1:
                        is_done = st.checkbox("done", value=False, key=f"check_{item.item_id}", label_visibility="collapsed")
                        if is_done:
                            toggle_item_status(item.item_id, False)
                            st.rerun()
                    with c2:
                        if item.sub_title:
                            st.markdown(f"**{item.sub_title}:** {item.item_name}")
                        else:
                            st.write(item.item_name)

                if checked_items:
                    if unchecked_items: st.divider()
                    for item in checked_items:
                        c1, c2, c3 = st.columns([0.5, 10.5, 1])
                        with c1:
                            undo = st.checkbox("undone", value=True, key=f"check_{item.item_id}", label_visibility="collapsed")
                            if not undo:
                                toggle_item_status(item.item_id, True)
                                st.rerun()
                        with c2:
                            st.markdown(f"""<div style="background-color: #f0f2f6; color: #888; padding: 8px 12px; border-radius: 8px; border: 1px solid #e0e0e0; text-decoration: line-through; display: flex; align-items: center;">✅ {item.item_name}</div>""", unsafe_allow_html=True)
                        with c3:
                            if is_admin:
                                if st.button("🗑", key=f"del_{item.item_id}", help="حذف"):
                                    ChecklistModel.delete_item(item.item_id)
                                    st.toast("تم الحذف")
                                    clear_checklist_cache()
                                    time.sleep(0.5)
                                    st.rerun()


def render_reports_page():
    ALLOWED_ROLES = [ROLE_SUPER_ADMIN, ROLE_ADMIN]
    if user.role_id not in ALLOWED_ROLES:
        st.warning("⛔ هذه الصفحة مخصصة للمدراء فقط.")
        return

    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    st.header("📊 التقارير وتحليل البيانات")
    st.markdown("---")
    
    if st.button("🔄 تحديث البيانات الآن"):
        st.cache_data.clear()
        st.rerun()

    df_users, df_content, df_checklists = get_analytics_data()

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("👥 إجمالي المستخدمين", len(df_users))
    with col2:
        if not df_users.empty and 'status' in df_users.columns:
            active_users = len(df_users[df_users['status'] == 'active'])
        else: active_users = 0
        st.metric("🟢 المستخدمين النشطين", active_users)
    with col3: st.metric("📝 إجمالي المقالات", len(df_content))
    with col4:
        if not df_checklists.empty and 'is_checked' in df_checklists.columns:
            completed_tasks = len(df_checklists[df_checklists['is_checked'].astype(str).str.upper() == 'TRUE'])
            total_tasks = len(df_checklists)
            percent = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        else: percent = 0
        st.metric("✅ نسبة إنجاز المهام", f"{percent}%")

    st.markdown("---")
    r_tabs = st.tabs(["👥 تحليل المستخدمين", "📝 تحليل المحتوى", "✅ متابعة المهام"])

    with r_tabs[0]:
        st.subheader("توزيع المستخدمين")
        if not df_users.empty:
            c1, c2 = st.columns([2, 1])
            with c1:
                if 'role_id' in df_users.columns:
                    df_users['role_name'] = df_users['role_id'].map(ROLE_NAMES)
                    fig_roles = px.pie(df_users, names='role_name', title='توزيع المستخدمين')
                    st.plotly_chart(fig_roles, use_container_width=True)
            with c2:
                st.download_button("📥 تحميل القائمة (CSV)", convert_df_to_csv(df_users), "users.csv", "text/csv")
                if 'created_at' in df_users.columns:
                    cols_to_show = ['name', 'email', 'role_name', 'status']
                    valid_cols = [c for c in cols_to_show if c in df_users.columns]
                    st.dataframe(df_users[valid_cols].tail(5), use_container_width=True)
    
    with r_tabs[1]:
        st.subheader("أداء المحتوى")
        if not df_content.empty:
            if 'created_by' in df_content.columns:
                author_counts = df_content['created_by'].value_counts().reset_index()
                author_counts.columns = ['الكاتب', 'عدد المشاركات']
                fig_content = px.bar(author_counts, x='الكاتب', y='عدد المشاركات')
                st.plotly_chart(fig_content, use_container_width=True)
            with st.expander("عرض السجل كاملاً"):
                st.dataframe(df_content, use_container_width=True)
        else: st.info("لا يوجد محتوى.")

    with r_tabs[2]:
        st.subheader("تقدم العمل")
        if not df_checklists.empty and 'is_checked' in df_checklists.columns:
            df_checklists['status_bool'] = df_checklists['is_checked'].astype(str).str.upper() == 'TRUE'
            status_counts = df_checklists['status_bool'].value_counts().reset_index()
            status_counts.columns = ['الحالة', 'العدد']
            status_counts['الحالة'] = status_counts['الحالة'].map({True: 'منجز ✅', False: 'قيد الانتظار ⏳'})
            c1, c2 = st.columns(2)
            with c1:
                fig_tasks = px.pie(status_counts, names='الحالة', values='العدد', hole=0.4)
                st.plotly_chart(fig_tasks, use_container_width=True)
            with c2:
                pending = df_checklists[df_checklists['status_bool'] == False]
                if not pending.empty:
                    cols_show = ['main_title', 'item_name', 'created_by']
                    valid_cols = [c for c in cols_show if c in pending.columns]
                    st.dataframe(pending[valid_cols], use_container_width=True)

# ==========================================
# 4. التنفيذ الرئيسي (Main Interface)
# ==========================================

# إنشاء التبويبات العلوية
main_tabs = st.tabs(["🖼️ مكتبة الوسائط", "☑️ النماذج والقوائم", "📊 التقارير والإحصائيات"])

with main_tabs[0]:
    render_media_page()

with main_tabs[1]:
    render_forms_page()

with main_tabs[2]:
    render_reports_page()
