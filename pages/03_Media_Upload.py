import streamlit as st
import time
import sys
import os

# ==========================================
# 1. إعداد المسارات والاستيراد
# ==========================================
# إضافة المسار الرئيسي لضمان استيراد backend بشكل صحيح
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # استيراد الباك إند الموحد
    import backend as bk
except ImportError as e:
    st.error(f"⚠️ خطأ في استيراد backend.py: {e}")
    st.stop()

# ==========================================
# 2. إعداد الصفحة
# ==========================================
st.set_page_config(page_title="مكتبة الوسائط", page_icon="🖼️", layout="wide")

# تطبيق التنسيق العام (مع التأكد من وجود الدالة)
if hasattr(bk, 'apply_custom_style'):
    bk.apply_custom_style()

# ==========================================
# 3. التحقق من الصلاحيات
# ==========================================
# التأكد من وجود دالة المستخدم
if hasattr(bk, 'get_current_user'):
    user = bk.get_current_user()
else:
    user = None

if not user:
    st.warning("🔒 يجب تسجيل الدخول أولاً!")
    time.sleep(1)
    st.switch_page("app.py")

# تحديد من يحق له الدخول
ALLOWED_ROLES = [bk.ROLE_SUPER_ADMIN, bk.ROLE_ADMIN, bk.ROLE_SUPERVISOR]

if user.role_id not in ALLOWED_ROLES:
    st.toast("⛔ عذراً، ليس لديك صلاحية لدخول هذه الصفحة!", icon="🚫")
    time.sleep(1.5)
    st.switch_page("app.py")

# عرض القائمة الجانبية
if hasattr(bk, 'render_sidebar'):
    bk.render_sidebar()

# ==========================================
# 4. دوال مساعدة (Caching)
# ==========================================
@st.cache_data(ttl=60)
def get_cached_media():
    """جلب قائمة الوسائط مع التخزين المؤقت"""
    try:
        return bk.MediaModel.get_all_media()
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return []

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
            # عرض تفاصيل الملف
            file_details = {
                "اسم الملف": uploaded_file.name,
                "النوع": uploaded_file.type,
                "الحجم": f"{uploaded_file.size / 1024:.2f} KB"
            }
            st.json(file_details)
            
            if st.button("🚀 بدء الرفع", use_container_width=True):
                with st.status("جارٍ معالجة الملف...", expanded=True) as status:
                    st.write("1️⃣ الاتصال بـ Google Drive...")
                    
                    # الرفع باستخدام backend
                    drive_file_id, web_view_link = bk.upload_file_to_cloud(
                        uploaded_file, 
                        uploaded_file.name, 
                        uploaded_file.type
                    )
                    
                    if drive_file_id:
                        st.write("2️⃣ حفظ البيانات في النظام...")
                        bk.MediaModel.add_media(
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

# --- التبويب 2: مكتبة الوسائط ---
with tabs[1]:
    st.header("الأرشيف")
    
    c_filter, c_refresh = st.columns([6, 1])
    with c_refresh:
        if st.button("🔄 تحديث", use_container_width=True):
            clear_media_cache()
            st.rerun()
            
    all_media = get_cached_media()
    
    if not all_media:
        st.info("لا توجد ملفات مرفوعة حتى الآن.")
    else:
        # عرض الملفات في شبكة
        cols_count = 4
        cols = st.columns(cols_count)
        
        for index, item in enumerate(all_media):
            with cols[index % cols_count]:
                with st.container(border=True):
                    
                    # --- منطق العرض الذكي (مع فحص الأخطاء) ---
                    is_image = "image" in item.file_type.lower()
                    file_shown = False

                    if is_image and item.google_drive_id:
                        # 🔥 التعديل هنا: التأكد من وجود الدالة في backend قبل استدعائها
                        if hasattr(bk, 'get_file_content'):
                            try:
                                with st.spinner("."):
                                    image_data = bk.get_file_content(item.google_drive_id)
                                if image_data:
                                    st.image(image_data, use_container_width=True)
                                    file_shown = True
                            except Exception:
                                pass # تجاهل الأخطاء وعرض الأيقونة بدلاً من الصورة
                        else:
                            # إذا كانت الدالة غير موجودة، لا نحاول استدعاءها
                            pass 
                    
                    # إذا لم تظهر الصورة، نعرض أيقونة
                    if not file_shown:
                        icon = "📄"
                        if "video" in item.file_type: icon = "🎥"
                        elif "pdf" in item.file_type: icon = "📕"
                        elif "sheet" in item.file_type or "excel" in item.file_type: icon = "📊"
                        elif is_image: icon = "🖼️" # أيقونة صورة في حال فشل التحميل
                        
                        st.markdown(f"<div style='text-align: center; font-size: 50px; margin-bottom: 10px;'>{icon}</div>", unsafe_allow_html=True)

                    # تفاصيل الملف
                    st.markdown(f"**{item.file_name}**")
                    st.caption(f"👤 {item.uploaded_by}")
                    st.caption(f"📅 {item.uploaded_at}")
                    
                    # رابط العرض
                    if item.google_drive_id:
                        drive_link = f"https://drive.google.com/file/d/{item.google_drive_id}/view?usp=sharing"
                        st.link_button("🔗 فتح في Drive", drive_link, use_container_width=True)
                    else:
                        st.caption("الرابط غير متوفر")
