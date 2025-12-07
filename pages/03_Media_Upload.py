import streamlit as st
import time
from datetime import datetime

# ==========================================
# 1. الاستدعاءات (Imports)
# ==========================================
try:
    # استيراد النماذج والثوابت من الباك إند الموحد
    from backend import (
        MediaModel, 
        ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR
    )
    from core.auth import get_current_user
    
    # استيراد خدمة رفع الملفات (نفترض وجودها في services كما في الكود الأصلي)
    # إذا لم تكن موجودة، تأكد من إنشاء الملف services/google_drive.py
    from services.google_drive import upload_file_to_drive
    
except ImportError as e:
    st.error(f"⚠️ خطأ في الاستيراد: {e}\nيرجى التأكد من وجود ملفات backend.py و services/google_drive.py")
    st.stop()

# ==========================================
# 2. إعداد الصفحة
# ==========================================
st.set_page_config(page_title="مكتبة الوسائط", page_icon="🖼️", layout="wide")

# ==========================================
# 3. التحقق من الصلاحيات
# ==========================================
user = get_current_user()

# تحديد من يحق له الدخول (المدراء والمشرفين)
ALLOWED_ROLES = [ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR]

if not user or user.role_id not in ALLOWED_ROLES:
    st.toast("⛔ عذراً، ليس لديك صلاحية لدخول هذه الصفحة!", icon="🚫")
    time.sleep(1.5)
    st.switch_page("app.py")

# ==========================================
# 4. دوال مساعدة
# ==========================================
@st.cache_data(ttl=60)
def get_cached_media():
    """جلب قائمة الوسائط مع التخزين المؤقت لتسريع التصفح"""
    return MediaModel.get_all_media()

def clear_media_cache():
    st.cache_data.clear()

# ==========================================
# 5. واجهة المستخدم الرئيسية
# ==========================================
st.title("📂 مكتبة الوسائط والملفات")
st.markdown("---")

# تقسيم الصفحة لتبويبين
tabs = st.tabs(["⬆️ رفع ملف جديد", "🖼️ استعراض المكتبة"])

# --- التبويب 1: رفع الملفات ---
with tabs[0]:
    st.header("رفع ملفات إلى Google Drive")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "اختر ملفاً للرفع (صور، فيديو، مستندات)", 
            type=['png', 'jpg', 'jpeg', 'pdf', 'mp4', 'docx', 'xlsx'],
            accept_multiple_files=False
        )

        if uploaded_file is not None:
            # عرض تفاصيل الملف قبل الرفع
            file_details = {
                "اسم الملف": uploaded_file.name,
                "النوع": uploaded_file.type,
                "الحجم": f"{uploaded_file.size / 1024:.2f} KB"
            }
            st.json(file_details)
            
            if st.button("🚀 بدء الرفع", use_container_width=True):
                with st.status("جارٍ معالجة الملف...", expanded=True) as status:
                    st.write("1️⃣ الاتصال بـ Google Drive...")
                    # عملية الرفع
                    try:
                        drive_file_id, web_view_link = upload_file_to_drive(uploaded_file)
                        
                        st.write("2️⃣ حفظ البيانات في النظام...")
                        # حفظ البيانات في الشيت عبر Backend
                        MediaModel.add_media(
                            name=uploaded_file.name,
                            mtype=uploaded_file.type,
                            drive_id=drive_file_id,
                            by=user.name
                        )
                        
                        status.update(label="✅ تم الرفع بنجاح!", state="complete", expanded=False)
                        st.success(f"تم رفع الملف: {uploaded_file.name}")
                        
                        # تحديث الكاش ليظهر الملف في المكتبة فوراً
                        clear_media_cache()
                        time.sleep(1)
                        st.rerun()
                        
                    except Exception as e:
                        status.update(label="❌ حدث خطأ!", state="error")
                        st.error(f"تفاصيل الخطأ: {str(e)}")

# --- التبويب 2: مكتبة الوسائط ---
with tabs[1]:
    st.header("الأرشيف")
    
    # أزرار تحكم علوية
    c_filter, c_refresh = st.columns([6, 1])
    with c_refresh:
        if st.button("🔄 تحديث", use_container_width=True):
            clear_media_cache()
            st.rerun()
            
    # جلب البيانات
    all_media = get_cached_media()
    
    if not all_media:
        st.info("لا توجد ملفات مرفوعة حتى الآن.")
    else:
        # عرض الملفات في شبكة (Grid)
        # عدد الأعمدة يعتمد على حجم الشاشة، نستخدم 4 كمتوسط
        cols_count = 4
        cols = st.columns(cols_count)
        
        for index, item in enumerate(all_media):
            with cols[index % cols_count]:
                with st.container(border=True):
                    # محاولة تحديد أيقونة مناسبة بناءً على نوع الملف
                    icon = "📄"
                    if "image" in item.file_type: icon = "🖼️"
                    elif "video" in item.file_type: icon = "🎥"
                    elif "pdf" in item.file_type: icon = "📕"
                    
                    st.markdown(f"### {icon}")
                    st.markdown(f"**{item.file_name}**")
                    st.caption(f"👤 {item.uploaded_by}")
                    st.caption(f"📅 {item.uploaded_at}")
                    
                    # رابط العرض
                    # ملاحظة: item.google_drive_id يجب أن يكون مخزناً بشكل صحيح
                    drive_link = f"https://drive.google.com/file/d/{item.google_drive_id}/view?usp=sharing"
                    
                    st.link_button("👁️ عرض الملف", drive_link, use_container_width=True)
