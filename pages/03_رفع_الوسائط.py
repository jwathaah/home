import streamlit as st
from services.google_drive import upload_file_to_drive
from models.media_model import MediaModel
from core.auth import get_current_user
from core.constants import ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR

# 1. إعداد الصفحة
st.set_page_config(page_title="مكتبة الوسائط", page_icon="🖼️", layout="wide")

# التحقق من الدخول والصلاحيات (يسمح للمدراء والمشرفين فقط)
user = get_current_user()
if not user:
    st.warning("🔒 يرجى تسجيل الدخول.")
    st.stop()

if user.role_id not in [ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SUPERVISOR]:
    st.error("⛔ ليس لديك صلاحية لرفع الوسائط.")
    st.stop()

# القائمة الجانبية
from ui.layout import render_sidebar
render_sidebar()

st.title("🖼️ مكتبة الوسائط")
st.markdown("مركز رفع الصور والفيديوهات لاستخدامها داخل المحتوى.")

# 2. قسم الرفع (Upload Section)
with st.container(border=True):
    st.subheader("☁️ رفع ملف جديد")
    uploaded_file = st.file_uploader("اختر صورة أو فيديو", type=['png', 'jpg', 'jpeg', 'mp4', 'pdf'])
    
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        st.caption(f"تفاصيل الملف: {file_details}")
        
        if st.button("🚀 بدء الرفع إلى Google Drive", type="primary"):
            with st.spinner("جاري الرفع... يرجى الانتظار"):
                # 1. الرفع الفعلي للدرايف
                file_id, web_link = upload_file_to_drive(uploaded_file, uploaded_file.name, uploaded_file.type)
                
                if file_id and web_link:
                    # 2. الحفظ في قاعدة البيانات
                    MediaModel.add_media(
                        file_name=uploaded_file.name,
                        file_type=uploaded_file.type,
                        google_drive_id=file_id,
                        uploaded_by=user.name
                    )
                    st.success("✅ تم الرفع والحفظ بنجاح!")
                    st.balloons()
                    st.rerun() # تحديث الصفحة لظهور الصورة في المعرض

st.divider()

# 3. معرض الصور (Gallery)
st.subheader("📂 الملفات المرفوعة سابقاً")

all_media = MediaModel.get_all_media()

if not all_media:
    st.info("المكتبة فارغة حالياً.")
else:
    # عرض الصور في شبكة (Grid)
    # سنعرض 4 صور في كل صف
    cols = st.columns(4)
    for i, media in enumerate(all_media):
        with cols[i % 4]:
            with st.container(border=True):
                # عرض أيقونة حسب نوع الملف
                if "image" in media.file_type:
                    # للأسف روابط Drive المباشرة تحتاج معالجة لتظهر كصورة مباشرة في Streamlit
                    # لكن سنعرض اسم الصورة وزر الرابط حالياً
                    st.image("assets/icons/image_placeholder.png") if False else st.markdown("🖼️ **صورة**")
                elif "video" in media.file_type:
                    st.markdown("🎥 **فيديو**")
                else:
                    st.markdown("📄 **ملف**")
                
                st.markdown(f"**{media.file_name}**")
                st.caption(f"بواسطة: {media.uploaded_by}")
                st.caption(f"{media.uploaded_at}")
                
                # ملاحظة: رابط webContentLink يقوم بالتنزيل المباشر
                # رابط webViewLink للعرض
                # سنحتاج لتخزين الرابط في المودل لعرضه هنا، حالياً سنعتمد على أن المودل خزّن الـ ID
                # لتسهيل الأمر في هذه المرحلة، سنعرض زر لفتح الملف
                
                # تحويل ID إلى رابط قابل للعرض (تقريبي)
                view_link = f"https://drive.google.com/file/d/{media.google_drive_id}/view?usp=sharing"
                
                st.link_button("🔗 فتح الملف", view_link)
                st.code(view_link, language="text") # لنسخ الرابط بسهولة
